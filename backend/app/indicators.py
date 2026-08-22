"""Pure-Python technical indicators used by the strategies.

All functions accept a sequence (list/tuple) of float closes (or high/low/close
arrays where noted) ordered oldest -> newest and return the latest value(s).
"""
from __future__ import annotations

import math
from typing import Sequence


def sma(values: Sequence[float], period: int) -> float | None:
    if len(values) < period or period <= 0:
        return None
    return sum(values[-period:]) / period


def ema(values: Sequence[float], period: int) -> float | None:
    """Exponential moving average of the full series, returning the last value."""
    if len(values) < period or period <= 0:
        return None
    k = 2 / (period + 1)
    # seed with SMA of first `period` values
    ema_prev = sum(values[:period]) / period
    for price in values[period:]:
        ema_prev = price * k + ema_prev * (1 - k)
    return ema_prev


def ema_series(values: Sequence[float], period: int) -> list[float]:
    """Full EMA series aligned to the input length (first period-1 are None)."""
    if len(values) < period or period <= 0:
        return []
    k = 2 / (period + 1)
    out: list[float] = []
    ema_prev = sum(values[:period]) / period
    for i, price in enumerate(values):
        if i < period - 1:
            out.append(float("nan"))
        elif i == period - 1:
            out.append(ema_prev)
        else:
            ema_prev = price * k + ema_prev * (1 - k)
            out.append(ema_prev)
    return out


def rsi(values: Sequence[float], period: int = 14) -> float | None:
    if len(values) < period + 1:
        return None
    gains, losses = 0.0, 0.0
    for i in range(-period, 0):
        change = values[i] - values[i - 1]
        if change >= 0:
            gains += change
        else:
            losses -= change
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(values: Sequence[float], fast: int = 12, slow: int = 26, signal: int = 9):
    """Return (macd_line, signal_line, histogram) latest values."""
    if len(values) < slow + signal:
        return None, None, None
    fast_s = ema_series(values, fast)
    slow_s = ema_series(values, slow)
    macd_line = [f - s for f, s in zip(fast_s, slow_s) if not (math.isnan(f) or math.isnan(s))]
    if len(macd_line) < signal:
        return None, None, None
    signal_line = ema(macd_line, signal)
    hist = macd_line[-1] - signal_line if signal_line is not None else None
    return macd_line[-1], signal_line, hist


def bollinger(values: Sequence[float], period: int = 20, std_mult: float = 2.0):
    """Return (middle, upper, lower, bandwidth_pct) latest values."""
    if len(values) < period:
        return None, None, None, None
    window = values[-period:]
    mid = sum(window) / period
    variance = sum((x - mid) ** 2 for x in window) / period
    sd = math.sqrt(variance)
    upper = mid + std_mult * sd
    lower = mid - std_mult * sd
    bw = (upper - lower) / mid * 100 if mid else 0.0
    return mid, upper, lower, bw


def atr(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], period: int = 14) -> float | None:
    """Average True Range."""
    n = len(closes)
    if n < period + 1:
        return None
    trs = []
    for i in range(1, n):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        trs.append(tr)
    if len(trs) < period:
        return None
    return sum(trs[-period:]) / period


def stdev(values: Sequence[float], period: int) -> float | None:
    if len(values) < period:
        return None
    window = values[-period:]
    mean = sum(window) / period
    var = sum((x - mean) ** 2 for x in window) / period
    return math.sqrt(var)


def slope(values: Sequence[float], period: int = 5) -> float | None:
    """Normalized slope of recent prices (percent change over `period`)."""
    if len(values) < period + 1:
        return None
    a, b = values[-period - 1], values[-1]
    if a == 0:
        return None
    return (b - a) / a * 100
