"""Trading strategies and a dynamic auto-regime selector.

Each strategy exposes:
    name -> str
    min_candles -> int
    evaluate(candles: list[Candle]) -> Signal

Signals carry a side ("long"/"short"/"flat"), a 0..1 strength and a reason.
The engine turns long/short signals into positions (with SL/TP from risk).
"""
from __future__ import annotations

from typing import Optional

from . import indicators as ind
from .state import Candle, Signal

STRATEGY_REGISTRY: dict[str, "Strategy"] = {}


def register(cls):
    STRATEGY_REGISTRY[cls.name] = cls()
    return cls


def closes(candles: list[Candle]) -> list[float]:
    return [c.c for c in candles]


def highs(candles: list[Candle]) -> list[float]:
    return [c.h for c in candles]


def lows(candles: list[Candle]) -> list[float]:
    return [c.l for c in candles]


# ------------------------------------------------------------------
class Strategy:
    name = "base"
    min_candles = 60

    def evaluate(self, candles: list[Candle]) -> Signal:
        raise NotImplementedError


@register
class EmaCross(Strategy):
    name = "ema_cross"
    min_candles = 60

    def evaluate(self, candles):
        c = closes(candles)
        fast = ind.ema(c, 12)
        slow = ind.ema(c, 26)
        prev_fast = ind.ema(c[:-1], 12) if len(c) > 26 else None
        prev_slow = ind.ema(c[:-1], 26) if len(c) > 26 else None
        if None in (fast, slow, prev_fast, prev_slow):
            return Signal("flat", 0, "warming up")
        crossed_up = prev_fast <= prev_slow and fast > slow
        crossed_down = prev_fast >= prev_slow and fast < slow
        spread = abs(fast - slow) / slow * 100
        strength = min(spread / 0.6, 1.0)
        if crossed_up and fast > slow:
            return Signal("long", strength, f"EMA12>EMA26 bull cross (Δ {spread:.2f}%)")
        if crossed_down and fast < slow:
            return Signal("short", strength, f"EMA12<EMA26 bear cross (Δ {spread:.2f}%)")
        if fast > slow:
            return Signal("long", strength * 0.4, f"above EMA stack, awaiting cross")
        if fast < slow:
            return Signal("short", strength * 0.4, f"below EMA stack, awaiting cross")
        return Signal("flat", 0, "EMA balanced")


@register
class RsiMomentum(Strategy):
    name = "rsi_momentum"
    min_candles = 40

    def evaluate(self, candles):
        c = closes(candles)
        r = ind.rsi(c, 14)
        if r is None:
            return Signal("flat", 0, "warming up")
        slope = ind.slope(c, 5) or 0
        if r > 55 and slope > 0:
            return Signal("long", min((r - 50) / 40, 1), f"RSI {r:.0f} rising (mom+)")
        if r < 45 and slope < 0:
            return Signal("short", min((50 - r) / 40, 1), f"RSI {r:.0f} falling (mom-)")
        return Signal("flat", 0, f"RSI neutral {r:.0f}")


@register
class MacdStrategy(Strategy):
    name = "macd"
    min_candles = 60

    def evaluate(self, candles):
        c = closes(candles)
        line, signal, hist = ind.macd(c, 12, 26, 9)
        if None in (line, signal, hist):
            return Signal("flat", 0, "warming up")
        price = c[-1]
        strength = min(abs(hist) / (price * 0.001), 1.0) if price else 0
        if line > signal and hist > 0:
            return Signal("long", strength, f"MACD bullish (hist {hist:+.2f})")
        if line < signal and hist < 0:
            return Signal("short", strength, f"MACD bearish (hist {hist:+.2f})")
        return Signal("flat", 0, "MACD flat")


@register
class MeanReversion(Strategy):
    name = "mean_reversion"
    min_candles = 40

    def evaluate(self, candles):
        c = closes(candles)
        mid, upper, lower, bw = ind.bollinger(c, 20, 2.0)
        r = ind.rsi(c, 14)
        if None in (mid, upper, lower) or r is None:
            return Signal("flat", 0, "warming up")
        price = c[-1]
        if price <= lower and r < 45:
            return Signal("long", 0.6, f"tagged lower BB, RSI {r:.0f}")
        if price >= upper and r > 55:
            return Signal("short", 0.6, f"tagged upper BB, RSI {r:.0f}")
        if price < mid:
            return Signal("long", 0.25, f"below mid-band, mean pull up")
        if price > mid:
            return Signal("short", 0.25, f"above mid-band, mean pull down")
        return Signal("flat", 0, "at mean")


@register
class GridStrategy(Strategy):
    """Stateless grid signal: fades moves away from a recent SMA."""
    name = "grid"
    min_candles = 60

    def evaluate(self, candles):
        c = closes(candles)
        mid = ind.sma(c, 30)
        if not mid:
            return Signal("flat", 0, "warming up")
        price = c[-1]
        dev = (price - mid) / mid * 100
        band = 0.8  # grid spacing %
        tier = min(int(abs(dev) / band), 3)
        if dev <= -band:
            return Signal("long", 0.3 + tier * 0.2, f"grid buy tier {tier} (dev {dev:+.2f}%)")
        if dev >= band:
            return Signal("short", 0.3 + tier * 0.2, f"grid sell tier {tier} (dev {dev:+.2f}%)")
        return Signal("flat", 0, "grid center")


@register
class AutoStrategy(Strategy):
    """Dynamic: detect market regime, then delegate to the best strategy.

    Trending  -> EMA cross / MACD
    Ranging   -> Mean reversion / Grid
    The chosen strategy is surfaced for the dashboard.
    """
    name = "auto"
    min_candles = 60

    def __init__(self):
        self._trend = STRATEGY_REGISTRY["ema_cross"]
        self._mom = STRATEGY_REGISTRY["rsi_momentum"]
        self._rev = STRATEGY_REGISTRY["mean_reversion"]

    def _regime(self, candles):
        c = closes(candles)
        mid, upper, lower, bw = ind.bollinger(c, 20, 2.0)
        slp = ind.slope(c, 10) or 0
        if bw is None:
            return "range", 0
        adx_like = bw  # bandwidth as a cheap volatility proxy
        if abs(slp) > 0.25 and adx_like > 2.2:
            return "trend", slp
        if adx_like < 1.6:
            return "range", slp
        return "mix", slp

    def evaluate(self, candles):
        regime, slp = self._regime(candles)
        if regime == "trend":
            sig = self._trend.evaluate(candles)
            return Signal(sig.side, sig.strength, f"[trend↑{slp:+.2f}%] {sig.reason}", sig.stop, sig.target)
        if regime == "range":
            sig = self._rev.evaluate(candles)
            return Signal(sig.side, sig.strength, f"[range] {sig.reason}", sig.stop, sig.target)
        sig = self._mom.evaluate(candles)
        return Signal(sig.side, sig.strength, f"[mix] {sig.reason}", sig.stop, sig.target)


def get_strategy(name: str) -> Strategy:
    return STRATEGY_REGISTRY.get((name or "auto").lower(), STRATEGY_REGISTRY["auto"])


def list_strategies() -> list[dict]:
    out = []
    desc = {
        "auto": "Dynamic regime detection — auto-picks the best strategy per symbol",
        "ema_cross": "Trend following via 12/26 EMA crossover",
        "rsi_momentum": "RSI(14) momentum breakout",
        "macd": "MACD(12,26,9) trend continuation",
        "mean_reversion": "Bollinger Band fade + RSI filter",
        "grid": "Grid fade around 30-period SMA",
    }
    for name in ["auto", "ema_cross", "rsi_momentum", "macd", "mean_reversion", "grid"]:
        out.append({"name": name, "description": desc.get(name, "")})
    return out
