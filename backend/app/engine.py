"""The autonomous trading engine.

A single async loop that, every tick:
  1. refreshes market data + account for every symbol
  2. reconciles externally-closed positions
  3. enforces the drawdown circuit breaker
  4. manages open positions (trailing stops, SL/TP exits)
  5. generates signals and opens new positions when risk permits

It runs entirely on its own — start it and it trades without intervention.
"""
from __future__ import annotations

import asyncio
import time

from . import strategies as strat
from .execution import ExecutionAdapter, LiveAdapter, SimAdapter
from .binance_client import BinanceFuturesClient
from .config import Settings
from .logger import get_logger
from .risk import RiskConfig, RiskManager
from .state import state

log = get_logger("engine")

ENTRY_STRENGTH_MIN = 0.30
ENTRY_COOLDOWN_SEC = 20.0
HALT_COOLDOWN_SEC = 25.0      # autonomous resume window after a drawdown halt


class TradingEngine:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.cfg = RiskConfig(**{k: v for k, v in settings.risk_dict().items()})
        self.risk = RiskManager(self.cfg)
        self.adapter: ExecutionAdapter | None = None
        self.client: BinanceFuturesClient | None = None
        self._task: asyncio.Task | None = None
        self._last_entry: dict[str, float] = {}
        self._halted_until: float = 0.0
        self._stop = asyncio.Event()

    # ---------------- bootstrap ----------------
    async def bootstrap(self) -> None:
        mode = self.settings.trading_mode
        connected = False
        if mode in ("auto", "live"):
            self.client = BinanceFuturesClient(
                self.settings.binance_api_key, self.settings.binance_api_secret,
                self.settings.binance_base_url)
            connected = await self.client.ping()
            state.log(f"Binance reachability check: {'OK' if connected else 'unreachable'}",
                      "INFO", "engine")

        if (mode == "live") or (mode == "auto" and connected):
            state.mode = "live"
            state.connected = True
            self.adapter = LiveAdapter(state, self.risk, self.settings, self.client)
            state.log("Mode = LIVE (Binance Futures testnet)", "INFO", "engine")
        else:
            state.mode = "sim"
            state.connected = False
            self.adapter = SimAdapter(state, self.risk, self.settings)
            if mode == "auto":
                state.log("Mode = SIM (Binance unreachable — running realistic simulation)",
                          "WARNING", "engine")
            else:
                state.log("Mode = SIM (forced)", "INFO", "engine")

        state.strategy = self.settings.strategy
        state.auto_strategy = self.settings.strategy == "auto"
        state.symbols = list(self.settings.symbols)
        state.started_at = time.time()
        state.log(f"Trading {', '.join(state.symbols)} | strategy={state.strategy} | "
                  f"leverage={self.cfg.leverage}x risk={self.cfg.risk_per_trade_pct}%", "INFO", "engine")

        for sym in state.symbols:
            await self.adapter.prewarm(sym)
        await self.adapter.refresh_account()
        if state.initial_equity == 0:
            state.initial_equity = state.equity
            state.peak_equity = state.equity
        state.record_equity()

    # ---------------- lifecycle ----------------
    def start_loop(self) -> None:
        if self._task is None or self._task.done():
            self._stop.clear()
            self._task = asyncio.create_task(self._run_forever())

    async def stop_loop(self) -> None:
        self._stop.set()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=3)
            except asyncio.TimeoutError:
                self._task.cancel()

    async def shutdown(self) -> None:
        await self.stop_loop()
        if self.client:
            await self.client.close()

    # ---------------- runtime controls ----------------
    def set_running(self, running: bool) -> None:
        state.running = running
        state.log(f"Bot {'STARTED' if running else 'PAUSED'}", "INFO", "engine")

    def set_strategy(self, name: str) -> None:
        name = (name or "auto").lower()
        if name not in strat.STRATEGY_REGISTRY:
            return
        state.strategy = name
        state.auto_strategy = name == "auto"
        state.log(f"Strategy set to {name}", "INFO", "engine")

    def update_risk(self, data: dict) -> None:
        self.cfg.update(data)
        state.log(f"Risk updated: lev={self.cfg.leverage}x risk={self.cfg.risk_per_trade_pct}% "
                  f"SL={self.cfg.stop_loss_pct}% TP={self.cfg.take_profit_pct}% "
                  f"trail={self.cfg.trailing_stop_pct}% maxPos={self.cfg.max_positions}",
                  "INFO", "engine")

    async def set_symbols(self, symbols: list[str]) -> None:
        symbols = [s.strip().upper() for s in symbols if s.strip()]
        if not symbols:
            return
        new = [s for s in symbols if s not in state.candles]
        for s in new:
            await self.adapter.prewarm(s)
        # close positions for symbols removed
        for sym in list(state.positions.keys()):
            if sym not in symbols:
                await self.adapter.close(sym, "symbol removed")
        state.symbols = symbols
        self.settings.symbols = symbols
        state.log(f"Symbols -> {', '.join(symbols)}", "INFO", "engine")

    async def manual_close(self, symbol: str) -> bool:
        return await self.adapter.close(symbol, "manual close")

    async def close_all(self) -> None:
        await self.adapter.close_all("close all")
        state.log("All positions closed", "INFO", "engine")

    async def reset_sim(self) -> None:
        if state.mode != "sim":
            return
        await self.adapter.close_all("reset")
        state.trades.clear()
        state.equity_curve.clear()
        state.logs.clear()
        state.halted = False
        state.peak_equity = state.balance
        state.initial_equity = state.balance
        self._last_entry.clear()
        state.log("SIM reset → capital restored", "INFO", "engine")

    # ---------------- main loop ----------------
    @property
    def loop_interval(self) -> float:
        return self.settings.loop_interval_sim if state.mode == "sim" else self.settings.loop_interval_live

    async def _run_forever(self) -> None:
        state.log("Engine loop started", "DEBUG", "engine")
        while not self._stop.is_set():
            try:
                await self._tick()
            except Exception as e:
                log.exception("tick error: %s", e)
                state.log(f"tick error: {e}", "ERROR", "engine")
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self.loop_interval)
            except asyncio.TimeoutError:
                pass
        state.log("Engine loop stopped", "DEBUG", "engine")

    async def _tick(self) -> None:
        # 1) market data
        for sym in state.symbols:
            await self.adapter.refresh_market(sym)

        # 2) account + reconcile
        await self.adapter.refresh_account()
        await self.adapter.reconcile()

        # 3) drawdown circuit breaker
        if not state.halted and self.risk.drawdown_breached(state.equity, state.peak_equity):
            state.halted = True
            self._halted_until = time.time() + HALT_COOLDOWN_SEC
            state.log(
                f"MAX DRAWDOWN breached ({self.cfg.max_drawdown_pct}%) → halting & flattening; "
                f"auto-resume in {HALT_COOLDOWN_SEC:.0f}s", "ERROR", "engine")
            await self.adapter.close_all("max drawdown")
            # lock in the drawdown as the new baseline so the bot can recover autonomously
            state.peak_equity = state.equity
        elif state.halted and time.time() > self._halted_until:
            state.halted = False
            state.log("Drawdown cooldown elapsed — resuming autonomous trading", "INFO", "engine")

        # 4) manage exits
        await self._manage_exits()

        # 5) entries (only when running, not halted, has budget)
        if state.running and not state.halted:
            await self._manage_entries()

        # 6) bookkeeping
        state.record_equity()
        state.log(
            f"eq {state.equity:.2f} | pnl "
            f"{sum(p.unrealized(state.prices.get(s, p.entry)) for s, p in state.positions.items()):+.2f} "
            f"| pos {len(state.positions)}",
            "DEBUG", "engine",
        )

    async def _manage_exits(self) -> None:
        for symbol, pos in list(state.positions.items()):
            price = state.prices.get(symbol, pos.entry)
            self.risk.update_trailing(pos, price)
            reason = self.risk.check_exit(pos, price)
            if reason:
                await self.adapter.close(symbol, reason.replace("_", " "))

    async def _manage_entries(self) -> None:
        if len(state.positions) >= self.cfg.max_positions:
            return
        now = time.time()
        for symbol in state.symbols:
            if len(state.positions) >= self.cfg.max_positions:
                break
            if symbol in state.positions:
                continue
            if now - self._last_entry.get(symbol, 0) < ENTRY_COOLDOWN_SEC:
                continue

            candles = list(state.candles.get(symbol, []))
            if len(candles) < 60:
                continue

            strategy = strat.get_strategy(state.strategy)
            sig = strategy.evaluate(candles)
            self._record_signal(symbol, sig, strategy.name)

            if sig.side == "flat" or sig.strength < ENTRY_STRENGTH_MIN:
                continue

            price = state.prices.get(symbol)
            if not price:
                continue
            equity = state.equity if state.equity > 0 else state.initial_equity
            side = "LONG" if sig.side == "long" else "SHORT"
            # provisional stop for sizing
            sl, tp = self.risk.stops_for(price, side)
            qty = self.risk.position_size(equity, price, sl, side)
            if qty <= 0:
                continue
            await self.adapter.set_leverage(symbol)
            ok = await self.adapter.open(symbol, side, qty, sl, tp, strategy.name, sig.reason)
            if ok:
                self._last_entry[symbol] = now

    def _record_signal(self, symbol: str, sig, strategy_name: str) -> None:
        tag = ""
        if strategy_name == "auto" and sig.reason.startswith("["):
            tag = sig.reason.split("]")[0].strip("[]")
        active = strategy_name if strategy_name != "auto" else f"auto:{tag or '?'}"
        state.active_strategy_per_symbol[symbol] = active
        state.last_signal_per_symbol[symbol] = {
            "side": sig.side, "strength": round(sig.strength, 2),
            "reason": sig.reason, "strategy": active, "t": int(time.time() * 1000),
        }
