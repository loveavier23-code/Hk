"""Shared, in-memory bot state shared by the engine, API and websocket hub.

All data is plain dataclasses that serialize cleanly to JSON for the dashboard.
The engine is the sole writer; API/WS are readers (single asyncio event loop).
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Candle:
    t: float          # open time (ms)
    o: float
    h: float
    l: float
    c: float
    v: float

    def to_list(self) -> list:
        return [self.t, self.o, self.h, self.l, self.c, self.v]


@dataclass
class Position:
    symbol: str
    side: str             # "LONG" | "SHORT"
    qty: float            # base asset quantity (signed positive)
    entry: float          # avg entry price
    leverage: int
    opened_at: float
    stop_loss: float = 0.0
    take_profit: float = 0.0
    trailing_high: float = 0.0   # best price seen since open (for trailing)
    strategy: str = ""
    meta: str = ""

    def unrealized(self, price: float) -> float:
        diff = (price - self.entry) if self.side == "LONG" else (self.entry - price)
        return diff * self.qty


@dataclass
class Trade:
    id: int
    symbol: str
    side: str              # "LONG"/"SHORT" for open direction
    action: str            # "OPEN" | "CLOSE"
    qty: float
    price: float
    pnl: float             # realized pnl (0 on OPEN)
    reason: str
    strategy: str
    t: float


@dataclass
class LogEntry:
    t: float
    level: str
    msg: str
    source: str = "engine"


@dataclass
class Signal:
    side: str          # "long" | "short" | "flat"
    strength: float    # 0..1
    reason: str
    stop: Optional[float] = None
    target: Optional[float] = None


class BotState:
    """Central state container."""

    MAX_CANDLES = 240
    MAX_TRADES = 300
    MAX_LOGS = 400
    MAX_EQUITY = 600

    def __init__(self):
        self.mode: str = "sim"            # "live" | "sim"
        self.connected: bool = False      # reachable Binance in live mode
        self.running: bool = False
        self.auto_strategy: bool = True   # dynamic strategy rotation
        self.strategy: str = "auto"
        self.symbols: list[str] = []
        self.started_at: float = time.time()
        self._trade_seq = 0

        # Market
        self.candles: dict[str, deque] = {}            # symbol -> deque[Candle]
        self.prices: dict[str, float] = {}

        # Account
        self.balance: float = 0.0        # wallet balance
        self.equity: float = 0.0         # balance + unrealized
        self.initial_equity: float = 0.0
        self.peak_equity: float = 0.0
        self.halted: bool = False        # drawdown circuit breaker

        # Books
        self.positions: dict[str, Position] = {}
        self.trades: list[Trade] = []
        self.logs: deque[LogEntry] = deque(maxlen=self.MAX_LOGS)
        self.equity_curve: deque[dict] = deque(maxlen=self.MAX_EQUITY)  # {t, equity}
        self.active_strategy_per_symbol: dict[str, str] = {}
        self.last_signal_per_symbol: dict[str, dict] = {}

    # ---------- writers ----------
    def init_symbol(self, symbol: str) -> None:
        if symbol not in self.candles:
            self.candles[symbol] = deque(maxlen=self.MAX_CANDLES)
        self.symbols = list(self.candles.keys())

    def push_candle(self, symbol: str, c: Candle) -> None:
        dq = self.candles.setdefault(symbol, deque(maxlen=self.MAX_CANDLES))
        dq.append(c)
        self.prices[symbol] = c.c
        self.symbols = list(self.candles.keys())

    def set_price(self, symbol: str, price: float) -> None:
        self.prices[symbol] = price

    def next_trade_id(self) -> int:
        self._trade_seq += 1
        return self._trade_seq

    def add_trade(self, **kw) -> Trade:
        t = Trade(id=self.next_trade_id(), t=time.time() * 1000, **kw)
        self.trades.append(t)
        if len(self.trades) > self.MAX_TRADES:
            self.trades = self.trades[-self.MAX_TRADES:]
        return t

    def log(self, msg: str, level: str = "INFO", source: str = "engine") -> None:
        self.logs.append(LogEntry(t=time.time() * 1000, level=level, msg=msg, source=source))

    def record_equity(self) -> None:
        self.equity_curve.append({"t": int(time.time() * 1000), "equity": round(self.equity, 2)})

    # ---------- snapshot ----------
    def snapshot(self) -> dict:
        positions = []
        for sym, p in self.positions.items():
            price = self.prices.get(sym, p.entry)
            upnl = p.unrealized(price)
            positions.append({
                "symbol": p.symbol, "side": p.side, "qty": round(p.qty, 6),
                "entry": round(p.entry, 4), "price": round(price, 4),
                "leverage": p.leverage, "unrealized": round(upnl, 2),
                "pnl_pct": round(upnl / (p.entry * p.qty) * 100, 2) if p.entry and p.qty else 0.0,
                "strategy": p.strategy, "opened_at": p.opened_at,
                "stop_loss": round(p.stop_loss, 4) if p.stop_loss else None,
                "take_profit": round(p.take_profit, 4) if p.take_profit else None,
            })

        realized = sum(tr.pnl for tr in self.trades if tr.action == "CLOSE")
        total_upnl = sum(p["unrealized"] for p in positions)
        dd = 0.0
        if self.peak_equity > 0:
            dd = round((self.peak_equity - self.equity) / self.peak_equity * 100, 2)

        return {
            "version": "1.0.0",
            "mode": self.mode,
            "connected": self.connected,
            "running": self.running,
            "halted": self.halted,
            "auto_strategy": self.auto_strategy,
            "strategy": self.strategy,
            "symbols": self.symbols,
            "started_at": self.started_at,
            "server_time": int(time.time() * 1000),
            "account": {
                "balance": round(self.balance, 2),
                "equity": round(self.equity, 2),
                "initial_equity": round(self.initial_equity, 2),
                "unrealized": round(total_upnl, 2),
                "realized": round(realized, 2),
                "peak_equity": round(self.peak_equity, 2),
                "drawdown_pct": dd,
                "roi_pct": round((self.equity - self.initial_equity) / self.initial_equity * 100, 2)
                            if self.initial_equity else 0.0,
            },
            "positions": positions,
            "trades": [asdict(t) for t in reversed(self.trades[-60:])],
            "logs": [asdict(l) for l in reversed(list(self.logs)[-80:])],
            "equity_curve": list(self.equity_curve),
            "prices": {s: round(p, 4) for s, p in self.prices.items()},
            "candles": {s: [c.to_list() for c in dq] for s, dq in self.candles.items()},
            "signals": self.last_signal_per_symbol,
            "active_strategy": self.active_strategy_per_symbol,
        }


# Singleton
state = BotState()
