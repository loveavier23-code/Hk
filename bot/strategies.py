from dataclasses import dataclass
from typing import Callable

import pandas as pd


@dataclass(frozen=True)
class Signal:
    action: str
    price: float
    reason: str


def _sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period, min_periods=period).mean()


def _rsi(series: pd.Series, period: int) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period, min_periods=period).mean()
    loss = (-delta.clip(upper=0)).rolling(period, min_periods=period).mean()
    rs = gain / loss.replace(0, 1e-12)
    return 100 - (100 / (1 + rs))


def sma_cross(closes: list[float], params: dict) -> Signal:
    series = pd.Series(closes, dtype=float)
    fast = _sma(series, int(params["fast_period"]))
    slow = _sma(series, int(params["slow_period"]))
    price = float(series.iloc[-1])
    if fast.iloc[-2] <= slow.iloc[-2] and fast.iloc[-1] > slow.iloc[-1]:
        return Signal("buy", price, "fast SMA crossed above slow SMA")
    if fast.iloc[-2] >= slow.iloc[-2] and fast.iloc[-1] < slow.iloc[-1]:
        return Signal("sell", price, "fast SMA crossed below slow SMA")
    return Signal("hold", price, "no crossover")


def sma_cross_rsi(closes: list[float], params: dict) -> Signal:
    series = pd.Series(closes, dtype=float)
    fast = _sma(series, int(params["fast_period"]))
    slow = _sma(series, int(params["slow_period"]))
    rsi = _rsi(series, int(params["rsi_period"]))
    price = float(series.iloc[-1])
    lower = float(params["rsi_lower"])
    upper = float(params["rsi_upper"])
    if fast.iloc[-2] <= slow.iloc[-2] and fast.iloc[-1] > slow.iloc[-1]:
        if rsi.iloc[-1] < upper:
            return Signal("buy", price, "bullish SMA cross with RSI below upper bound")
        return Signal("hold", price, "bullish cross but RSI overbought")
    if fast.iloc[-2] >= slow.iloc[-2] and fast.iloc[-1] < slow.iloc[-1]:
        if rsi.iloc[-1] > lower:
            return Signal("sell", price, "bearish SMA cross with RSI above lower bound")
        return Signal("hold", price, "bearish cross but RSI oversold")
    return Signal("hold", price, "no crossover")


STRATEGIES: dict[str, Callable[[list[float], dict], Signal]] = {
    "sma_cross": sma_cross,
    "sma_cross_rsi": sma_cross_rsi,
}
