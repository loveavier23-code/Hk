import os
from dataclasses import dataclass, field
from pathlib import Path

VALID_MODES = ("analyze", "live")
VALID_STRATEGIES = ("sma_cross",)


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _get_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        raise SystemExit(f"Invalid integer for {name}: {raw!r}")


def _get_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError:
        raise SystemExit(f"Invalid float for {name}: {raw!r}")


@dataclass(frozen=True)
class Config:
    exchange: str = "kraken"
    symbol: str = "BTC/USD"
    timeframe: str = "1m"
    interval_seconds: int = 60
    mode: str = "analyze"
    strategy: str = "sma_cross"
    strategy_fast_period: int = 10
    strategy_slow_period: int = 30
    strategy_rsi_period: int = 14
    strategy_rsi_lower: float = 30.0
    strategy_rsi_upper: float = 70.0
    candle_warmup: int = 300
    db_path: str = "bot.db"
    ca_bundle: str = ""
    api_key: str = ""
    api_secret: str = ""
    order_amount: float = 0.001
    engine_state: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_env(cls, env_path: Path | None = None) -> "Config":
        if env_path is not None:
            load_dotenv(env_path)
        mode = os.environ.get("MODE", "analyze").lower()
        strategy = os.environ.get("STRATEGY", "sma_cross").lower()
        if mode not in VALID_MODES:
            raise SystemExit(f"Invalid MODE {mode!r}, expected one of {VALID_MODES}")
        if strategy not in VALID_STRATEGIES:
            raise SystemExit(
                f"Invalid STRATEGY {strategy!r}, expected one of {VALID_STRATEGIES}"
            )
        return cls(
            exchange=os.environ.get("EXCHANGE", "kraken").lower(),
            symbol=os.environ.get("SYMBOL", "BTC/USD").upper(),
            timeframe=os.environ.get("TIMEFRAME", "1m"),
            interval_seconds=_get_int("INTERVAL_SECONDS", 60),
            mode=mode,
            strategy=strategy,
            strategy_fast_period=_get_int("STRATEGY_FAST_PERIOD", 10),
            strategy_slow_period=_get_int("STRATEGY_SLOW_PERIOD", 30),
            strategy_rsi_period=_get_int("STRATEGY_RSI_PERIOD", 14),
            strategy_rsi_lower=_get_float("STRATEGY_RSI_LOWER", 30.0),
            strategy_rsi_upper=_get_float("STRATEGY_RSI_UPPER", 70.0),
            candle_warmup=_get_int("CANDLE_WARMUP", 300),
            db_path=os.environ.get("DB_PATH", "bot.db"),
            ca_bundle=os.environ.get("CA_BUNDLE", ""),
            api_key=os.environ.get("API_KEY", ""),
            api_secret=os.environ.get("API_SECRET", ""),
            order_amount=_get_float("ORDER_AMOUNT", 0.001),
        )

    def strategy_params(self) -> dict:
        return {
            "fast_period": self.strategy_fast_period,
            "slow_period": self.strategy_slow_period,
            "rsi_period": self.strategy_rsi_period,
            "rsi_lower": self.strategy_rsi_lower,
            "rsi_upper": self.strategy_rsi_upper,
        }

    def is_live(self) -> bool:
        return self.mode == "live"

    def has_credentials(self) -> bool:
        return bool(self.api_key and self.api_secret)
