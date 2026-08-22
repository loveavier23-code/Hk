"""Execution adapters — one interface, two backends.

  * LiveAdapter  -> real Binance Futures testnet (REST, signed orders)
  * SimAdapter   -> paper trading on the local simulator

The engine talks only to the adapter, so strategy/risk/exit logic is identical
across modes. State (positions, balance, equity) lives in `state` for both.
"""
from __future__ import annotations

import time
from typing import Optional

from .binance_client import BinanceFuturesClient, BinanceError
from .logger import get_logger
from .risk import RiskManager
from .simulator import MarketSimulator
from .state import Candle, Position, state as global_state
from .config import Settings

log = get_logger("execution")

SIM_INITIAL_CAPITAL = 10_000.0


class ExecutionAdapter:
    mode = "base"

    def __init__(self, st, risk: RiskManager, settings: Settings):
        self.state = st
        self.risk = risk
        self.settings = settings

    async def prewarm(self, symbol: str) -> None: ...
    async def refresh_market(self, symbol: str) -> None: ...
    async def refresh_account(self) -> None: ...
    async def reconcile(self) -> None: ...
    async def open(self, symbol: str, side: str, qty: float, stop: float,
                   target: float, strategy: str, reason: str) -> bool: ...
    async def close(self, symbol: str, reason: str) -> bool: ...
    async def set_leverage(self, symbol: str) -> None: ...
    async def close_all(self, reason: str = "manual") -> None: ...


# ---------------------------------------------------------------------------
class SimAdapter(ExecutionAdapter):
    mode = "sim"

    def __init__(self, st, risk, settings):
        super().__init__(st, risk, settings)
        self.sim = MarketSimulator(seed=20260822)
        self.state.balance = SIM_INITIAL_CAPITAL
        self.state.equity = SIM_INITIAL_CAPITAL
        self.state.initial_equity = SIM_INITIAL_CAPITAL
        self.state.peak_equity = SIM_INITIAL_CAPITAL

    async def prewarm(self, symbol: str) -> None:
        self.state.init_symbol(symbol)
        candles = self.sim.prewarm(symbol, n=200)
        for c in candles:
            self.state.push_candle(symbol, c)
        self.state.set_price(symbol, self.sim.price(symbol))
        log.info("SIM prewarmed %s @ %.4f (%d candles)", symbol, self.sim.price(symbol), len(candles))

    async def refresh_market(self, symbol: str) -> None:
        t = int(time.time() * 1000)
        candle = self.sim.next_candle(symbol, t)
        self.state.push_candle(symbol, candle)

    async def refresh_account(self) -> None:
        upnl = sum(p.unrealized(self.state.prices.get(s, p.entry))
                   for s, p in self.state.positions.items())
        self.state.equity = self.state.balance + upnl
        if self.state.equity > self.state.peak_equity:
            self.state.peak_equity = self.state.equity

    async def reconcile(self) -> None:
        pass  # SIM book is canonical

    async def set_leverage(self, symbol: str) -> None:
        pass

    def _fee(self, qty: float, price: float) -> float:
        return self.risk.fee(qty * price)

    async def open(self, symbol, side, qty, stop, target, strategy, reason) -> bool:
        if symbol in self.state.positions:
            return False
        price = self.state.prices.get(symbol)
        if not price or qty <= 0:
            return False
        fee = self._fee(qty, price)
        self.state.balance -= fee
        pos = Position(
            symbol=symbol, side=side, qty=qty, entry=price,
            leverage=self.risk.cfg.leverage, opened_at=time.time(),
            stop_loss=stop, take_profit=target, trailing_high=price,
            strategy=strategy, meta=reason,
        )
        self.state.positions[symbol] = pos
        self.state.add_trade(symbol=symbol, side=side, action="OPEN", qty=qty,
                             price=price, pnl=-fee, reason=reason, strategy=strategy)
        self.state.log(f"OPEN {side} {symbol} {qty} @ {price:.2f} | {reason}", "INFO", "execution")
        return True

    async def close(self, symbol: str, reason: str) -> bool:
        pos = self.state.positions.get(symbol)
        if not pos:
            return False
        price = self.state.prices.get(symbol, pos.entry)
        exit_fee = self._fee(pos.qty, price)
        pnl = pos.unrealized(price) - exit_fee
        self.state.balance += pnl
        self.state.add_trade(symbol=symbol, side=pos.side, action="CLOSE", qty=pos.qty,
                             price=price, pnl=pnl, reason=reason, strategy=pos.strategy)
        del self.state.positions[symbol]
        verb = "PROFIT" if pnl >= 0 else "LOSS"
        self.state.log(f"CLOSE {pos.side} {symbol} {pos.qty} @ {price:.2f} → {verb} {pnl:+.2f} | {reason}",
                       "INFO", "execution")
        return True

    async def close_all(self, reason: str = "manual") -> None:
        for symbol in list(self.state.positions.keys()):
            await self.close(symbol, reason)


# ---------------------------------------------------------------------------
class LiveAdapter(ExecutionAdapter):
    mode = "live"

    def __init__(self, st, risk, settings, client: BinanceFuturesClient):
        super().__init__(st, risk, settings)
        self.client = client
        # shadow book of orders we placed, keyed by symbol
        self._ours: dict[str, Position] = {}

    async def prewarm(self, symbol: str) -> None:
        self.state.init_symbol(symbol)
        try:
            kl = await self.client.klines(symbol, "1m", 200)
            for k in kl:
                self.state.push_candle(symbol, Candle(t=k[0], o=k[1], h=k[2], l=k[3], c=k[4], v=k[5]))
            self.state.set_price(symbol, kl[-1][4] if kl else 0)
            log.info("LIVE prewarmed %s @ %.4f", symbol, self.state.prices.get(symbol, 0))
        except BinanceError as e:
            self.state.log(f"prewarm {symbol} failed: {e}", "ERROR", "execution")

    async def refresh_market(self, symbol: str) -> None:
        try:
            from collections import deque
            kl = await self.client.klines(symbol, "1m", self.state.MAX_CANDLES)
            # replace the window for a clean live view
            self.state.candles[symbol] = deque(maxlen=self.state.MAX_CANDLES)
            for k in kl:
                self.state.push_candle(symbol, Candle(t=k[0], o=k[1], h=k[2], l=k[3], c=k[4], v=k[5]))
            self.state.set_price(symbol, kl[-1][4] if kl else self.state.prices.get(symbol, 0))
        except BinanceError as e:
            self.state.log(f"refresh {symbol} failed: {e}", "ERROR", "execution")

    async def refresh_account(self) -> None:
        try:
            bal, eq = await self.client.usdt_equity()
            if self.state.initial_equity == 0:
                self.state.initial_equity = eq
                self.state.balance = bal
            else:
                self.state.balance = bal
            self.state.equity = eq
            if eq > self.state.peak_equity:
                self.state.peak_equity = eq
        except BinanceError as e:
            self.state.log(f"account refresh failed: {e}", "ERROR", "execution")

    async def reconcile(self) -> None:
        """Detect externally-closed (e.g. liquidated) positions and clean up."""
        try:
            ex = {p["symbol"]: p for p in await self.client.positions()}
        except BinanceError:
            return
        for symbol, pos in list(self._ours.items()):
            ex_pos = ex.get(symbol)
            if not ex_pos or ex_pos["qty"] == 0:
                # gone — realize at last mark
                price = ex_pos["mark"] if ex_pos else self.state.prices.get(symbol, pos.entry)
                pnl = pos.unrealized(price)
                self.state.add_trade(symbol=symbol, side=pos.side, action="CLOSE",
                                     qty=pos.qty, price=price, pnl=pnl,
                                     reason="exchange close", strategy=pos.strategy)
                self.state.log(f"RECONCILE: {symbol} closed on exchange (pnl {pnl:+.2f})",
                               "WARNING", "execution")
                self._ours.pop(symbol, None)
                self.state.positions.pop(symbol, None)
            else:
                self.state.positions[symbol] = pos

    async def set_leverage(self, symbol: str) -> None:
        try:
            await self.client.set_leverage(symbol, self.risk.cfg.leverage)
        except BinanceError as e:
            self.state.log(f"set leverage {symbol}: {e}", "WARNING", "execution")

    async def open(self, symbol, side, qty, stop, target, strategy, reason) -> bool:
        if symbol in self._ours:
            return False
        binance_side = "BUY" if side == "LONG" else "SELL"
        try:
            await self.set_leverage(symbol)
            res = await self.client.place_order(symbol, binance_side, qty, order_type="MARKET")
            entry = float(res.get("avgPrice", 0)) or self.state.prices.get(symbol, 0)
            ex_qty = abs(float(res.get("executedQty", qty)))
            pos = Position(symbol=symbol, side=side, qty=ex_qty, entry=entry,
                           leverage=self.risk.cfg.leverage, opened_at=time.time(),
                           stop_loss=stop, take_profit=target, trailing_high=entry,
                           strategy=strategy, meta=reason)
            self._ours[symbol] = pos
            self.state.positions[symbol] = pos
            self.state.add_trade(symbol=symbol, side=side, action="OPEN", qty=ex_qty,
                                 price=entry, pnl=0, reason=reason, strategy=strategy)
            self.state.log(f"LIVE OPEN {side} {symbol} {ex_qty} @ {entry:.2f} | {reason}", "INFO", "execution")
            return True
        except BinanceError as e:
            self.state.log(f"LIVE open {symbol} failed: {e}", "ERROR", "execution")
            return False

    async def close(self, symbol: str, reason: str) -> bool:
        pos = self._ours.get(symbol) or self.state.positions.get(symbol)
        if not pos:
            return False
        binance_side = "SELL" if pos.side == "LONG" else "BUY"
        try:
            res = await self.client.place_order(symbol, binance_side, pos.qty,
                                                order_type="MARKET", reduce_only=True)
            exit_price = float(res.get("avgPrice", 0)) or self.state.prices.get(symbol, pos.entry)
            pnl = pos.unrealized(exit_price)
            self.state.add_trade(symbol=symbol, side=pos.side, action="CLOSE", qty=pos.qty,
                                 price=exit_price, pnl=pnl, reason=reason, strategy=pos.strategy)
            self.state.log(f"LIVE CLOSE {pos.side} {symbol} @ {exit_price:.2f} → {pnl:+.2f} | {reason}",
                           "INFO", "execution")
            self._ours.pop(symbol, None)
            self.state.positions.pop(symbol, None)
            return True
        except BinanceError as e:
            self.state.log(f"LIVE close {symbol} failed: {e}", "ERROR", "execution")
            return False

    async def close_all(self, reason: str = "manual") -> None:
        for symbol in list(self._ours.keys()):
            await self.close(symbol, reason)
