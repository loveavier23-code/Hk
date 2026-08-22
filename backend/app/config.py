"""Centralized configuration loaded from environment / .env file."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()  # reads backend/.env if present


def _get(name: str, default, cast=str):
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    if cast is bool:
        return str(raw).strip().lower() in {"1", "true", "yes", "on"}
    try:
        return cast(raw)
    except (TypeError, ValueError):
        return default


@dataclass
class Settings:
    # Binance
    binance_api_key: str = _get("BINANCE_API_KEY", "")
    binance_api_secret: str = _get("BINANCE_API_SECRET", "")
    binance_base_url: str = _get("BINANCE_BASE_URL", "https://testnet.binancefuture.com")
    binance_ws_url: str = _get("BINANCE_WS_URL", "wss://stream.binancefuture.com")

    # Mode / strategy
    trading_mode: str = _get("TRADING_MODE", "auto").lower()
    symbols: list[str] = field(
        default_factory=lambda: [s.strip().upper() for s in _get("SYMBOLS", "BTCUSDT,ETHUSDT,SOLUSDT").split(",") if s.strip()]
    )
    strategy: str = _get("STRATEGY", "auto").lower()

    # Risk
    leverage: int = _get("LEVERAGE", 10, int)
    risk_per_trade_pct: float = _get("RISK_PER_TRADE_PCT", 2.0, float)
    stop_loss_pct: float = _get("STOP_LOSS_PCT", 2.5, float)
    take_profit_pct: float = _get("TAKE_PROFIT_PCT", 5.0, float)
    trailing_stop_pct: float = _get("TRAILING_STOP_PCT", 0.0, float)
    max_positions: int = _get("MAX_POSITIONS", 3, int)
    max_drawdown_pct: float = _get("MAX_DRAWDOWN_PCT", 12.0, float)

    # Timing
    loop_interval_sim: float = _get("LOOP_INTERVAL_SIM", 4.0, float)
    loop_interval_live: float = _get("LOOP_INTERVAL_LIVE", 12.0, float)

    # Server
    host: str = _get("HOST", "0.0.0.0")
    port: int = _get("PORT", 8000, int)

    @property
    def loop_interval(self) -> float:
        return self.loop_interval_sim  # overridden by runtime mode

    def risk_dict(self) -> dict:
        return {
            "leverage": self.leverage,
            "risk_per_trade_pct": self.risk_per_trade_pct,
            "stop_loss_pct": self.stop_loss_pct,
            "take_profit_pct": self.take_profit_pct,
            "trailing_stop_pct": self.trailing_stop_pct,
            "max_positions": self.max_positions,
            "max_drawdown_pct": self.max_drawdown_pct,
        }


settings = Settings()
