"""Risk management — position sizing, stop/target placement and exits."""
from __future__ import annotations

from dataclasses import dataclass

from .logger import get_logger

log = get_logger("risk")


@dataclass
class RiskConfig:
    leverage: int = 10
    risk_per_trade_pct: float = 2.0
    stop_loss_pct: float = 2.5
    take_profit_pct: float = 5.0
    trailing_stop_pct: float = 0.0
    max_positions: int = 3
    max_drawdown_pct: float = 12.0
    taker_fee_pct: float = 0.04

    def update(self, data: dict) -> None:
        for k in ("leverage", "max_positions"):
            if k in data and data[k] is not None:
                setattr(self, k, int(data[k]))
        for k in ("risk_per_trade_pct", "stop_loss_pct", "take_profit_pct",
                  "trailing_stop_pct", "max_drawdown_pct"):
            if k in data and data[k] is not None:
                setattr(self, k, float(data[k]))


class RiskManager:
    def __init__(self, cfg: RiskConfig):
        self.cfg = cfg

    # ---- position sizing (risk-based) ----
    def position_size(self, equity: float, entry: float, stop: float, side: str) -> float:
        """Size so that a stop-out costs at most risk_per_trade_pct of equity.

        If no stop, fall back to notional = (risk% of equity) * leverage / entry.
        """
        risk_capital = equity * (self.cfg.risk_per_trade_pct / 100.0)
        if stop and entry:
            per_unit_risk = abs(entry - stop)
            if per_unit_risk > 0:
                qty = risk_capital / per_unit_risk
                return self._cap_notional(qty, equity, entry)
        # fallback sizing
        notional = (equity * (self.cfg.risk_per_trade_pct / 100.0)) * self.cfg.leverage
        return self._cap_notional(notional / entry if entry else 0, equity, entry)

    def _cap_notional(self, qty: float, equity: float, entry: float) -> float:
        # never use more than ~40% of equity as margin at given leverage
        max_notional = equity * 0.40 * self.cfg.leverage
        if entry and qty * entry > max_notional:
            qty = max_notional / entry
        return round(qty, 3)

    # ---- stop / target placement ----
    def stops_for(self, entry: float, side: str) -> tuple[float, float]:
        if side == "LONG":
            sl = entry * (1 - self.cfg.stop_loss_pct / 100.0)
            tp = entry * (1 + self.cfg.take_profit_pct / 100.0)
        else:
            sl = entry * (1 + self.cfg.stop_loss_pct / 100.0)
            tp = entry * (1 - self.cfg.take_profit_pct / 100.0)
        return round(sl, 6), round(tp, 6)

    def update_trailing(self, position, price: float) -> None:
        """Maintain best-seen price and (optionally) ratchet stop loss."""
        if self.cfg.trailing_stop_pct <= 0:
            return
        if position.side == "LONG":
            if price > position.trailing_high:
                position.trailing_high = price
            new_sl = position.trailing_high * (1 - self.cfg.trailing_stop_pct / 100.0)
            if new_sl > position.stop_loss:
                position.stop_loss = new_sl
        else:
            if position.trailing_high == 0 or price < position.trailing_high:
                position.trailing_high = price
            new_sl = position.trailing_high * (1 + self.cfg.trailing_stop_pct / 100.0)
            if position.stop_loss == 0 or new_sl < position.stop_loss:
                position.stop_loss = new_sl

    def check_exit(self, position, price: float) -> str | None:
        """Return an exit reason if SL/TP is hit, else None."""
        if position.side == "LONG":
            if position.stop_loss and price <= position.stop_loss:
                return "stop_loss"
            if position.take_profit and price >= position.take_profit:
                return "take_profit"
        else:
            if position.stop_loss and price >= position.stop_loss:
                return "stop_loss"
            if position.take_profit and price <= position.take_profit:
                return "take_profit"
        return None

    # ---- circuit breaker ----
    def drawdown_breached(self, equity: float, peak: float) -> bool:
        if peak <= 0:
            return False
        dd = (peak - equity) / peak * 100.0
        return dd >= self.cfg.max_drawdown_pct

    def fee(self, notional: float) -> float:
        return notional * (self.cfg.taker_fee_pct / 100.0)
