"""Realistic market simulator used in SIM mode (and when Binance is offline).

Generates regime-switching geometric-Brownian-motion price series per symbol so
that strategies, exits and the dashboard behave believably with no network.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

from .state import Candle

# symbol -> (base_price, step_volatility, tick_substeps)
SYMBOL_PROFILES = {
    "BTCUSDT": (65000.0, 0.011, 6),
    "ETHUSDT": (3200.0, 0.013, 6),
    "SOLUSDT": (150.0, 0.020, 6),
    "BNBUSDT": (580.0, 0.015, 6),
    "XRPUSDT": (0.62, 0.018, 6),
    "DOGEUSDT": (0.16, 0.022, 6),
    "ADAUSDT": (0.45, 0.019, 6),
    "AVAXUSDT": (35.0, 0.021, 6),
}

DEFAULT_PROFILE = (100.0, 0.015, 6)


@dataclass
class _SymState:
    price: float
    base: float           # mean-reversion anchor (realistic price level)
    vol: float
    subs: int
    regime: str = "range"     # "up" | "down" | "range"
    regime_ttl: int = 0
    drift: float = 0.0


class MarketSimulator:
    # mean-reversion strength keeps prices near a believable level long-term,
    # while short-term regime drift lets strategies catch real-looking trends.
    KAPPA = 0.006

    def __init__(self, seed: int = 1337):
        self.rng = random.Random(seed)
        self.symbols: dict[str, _SymState] = {}

    def profile(self, symbol: str):
        return SYMBOL_PROFILES.get(symbol, DEFAULT_PROFILE)

    def register(self, symbol: str) -> None:
        if symbol in self.symbols:
            return
        base, vol, subs = self.profile(symbol)
        self.symbols[symbol] = _SymState(price=base, base=base, vol=vol, subs=subs)

    def _switch_regime(self, s: _SymState) -> None:
        s.regime_ttl -= 1
        if s.regime_ttl > 0:
            # gently vary drift inside a regime
            if s.regime == "up":
                s.drift = 0.0026 * (0.5 + 0.6 * self.rng.random())
            elif s.regime == "down":
                s.drift = -0.0026 * (0.5 + 0.6 * self.rng.random())
            else:
                s.drift = (self.rng.random() - 0.5) * 0.0008
            return
        r = self.rng.random()
        if r < 0.42:
            s.regime = "up"
        elif r < 0.78:
            s.regime = "down"
        else:
            s.regime = "range"
        s.regime_ttl = self.rng.randint(25, 65)

    def _step(self, s: _SymState) -> float:
        z = self.rng.gauss(0, 1)
        dt = 1.0
        # mean-reverting drift toward the anchor + regime drift
        reversion = self.KAPPA * (math.log(s.base) - math.log(s.price))
        mu = s.drift + reversion
        s.price *= math.exp((mu - 0.5 * s.vol ** 2) * dt + s.vol * math.sqrt(dt) * z)
        s.price = max(s.price, 0.0001)
        return s.price

    def prewarm(self, symbol: str, n: int = 200) -> list[Candle]:
        """Generate `n` historical candles to seed indicators."""
        self.register(symbol)
        s = self.symbols[symbol]
        self._switch_regime(s)
        candles: list[Candle] = []
        prev = s.price
        t0 = 0
        for i in range(n):
            self._switch_regime(s)
            o = prev
            hi, lo = o, o
            for _ in range(s.subs):
                p = self._step(s)
                hi = max(hi, p); lo = min(lo, p)
            c = s.price
            v = self.rng.uniform(50, 600) * (1 + abs(c - o) / o * 50)
            candles.append(Candle(t=t0 + i, o=o, h=hi, l=lo, c=c, v=round(v, 2)))
            prev = c
        return candles

    def next_candle(self, symbol: str, t: float) -> Candle:
        """Advance the market by one bar and return the new candle."""
        self.register(symbol)
        s = self.symbols[symbol]
        self._switch_regime(s)
        o = s.price
        hi, lo = o, o
        for _ in range(s.subs):
            p = self._step(s)
            hi = max(hi, p); lo = min(lo, p)
        c = s.price
        v = self.rng.uniform(50, 600) * (1 + abs(c - o) / o * 50)
        return Candle(t=t, o=o, h=hi, l=lo, c=c, v=round(v, 2))

    def price(self, symbol: str) -> float:
        self.register(symbol)
        return self.symbols[symbol].price
