import asyncio
import logging
import time

from .config import Config
from .db import Database
from .exchange import ExchangeClient
from .executor import Executor
from .strategies import STRATEGIES

logger = logging.getLogger("bot.engine")


class Engine:
    def __init__(self, config: Config):
        self.config = config
        self.db = Database(config)
        self.exchange = ExchangeClient(config)
        self.executor = Executor(config, self.exchange, self.db)
        self.strategy = STRATEGIES[config.strategy]
        self.running = False
        self.last_tick_ts = None
        self.last_error = None
        self.ticks = 0

    def warmup(self) -> int:
        rows = self.exchange.fetch_ohlcv(
            limit=self.config.candle_warmup
        )
        self.db.insert_candles(self.config.symbol, self.config.timeframe, rows)
        logger.info(
            "warmup: stored %d real %s candles for %s",
            len(rows), self.config.timeframe, self.config.symbol,
        )
        return len(rows)

    def _evaluate(self) -> None:
        rows = self.db.candles(self.config.symbol, self.config.timeframe, limit=500)
        closes = [float(r["close"]) for r in reversed(rows)]
        needed = self.config.strategy_slow_period + 2
        if len(closes) < needed:
            logger.info(
                "strategy needs %d candles, have %d; waiting",
                needed, len(closes),
            )
            return
        signal = self.strategy(closes, self.config.strategy_params())
        record = {
            "ts": int(time.time() * 1000),
            "symbol": self.config.symbol,
            "timeframe": self.config.timeframe,
            "strategy": self.config.strategy,
            "action": signal.action,
            "price": signal.price,
            "reason": signal.reason,
        }
        self.db.insert_signal(record)
        logger.info("signal %s @ %.2f: %s", signal.action, signal.price, signal.reason)
        if signal.action in ("buy", "sell"):
            try:
                order = self.executor.execute(signal.action, signal.price)
                logger.info("order %s %s executed (%s)", signal.action, order["amount"], order["status"])
            except Exception as exc:
                logger.warning("order skipped: %s", exc)

    def _tick(self) -> None:
        self.ticks += 1
        self.last_tick_ts = int(time.time() * 1000)
        try:
            rows = self.exchange.fetch_ohlcv(limit=10)
            self.db.insert_candles(self.config.symbol, self.config.timeframe, rows)
            self._evaluate()
            self.last_error = None
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"
            logger.error("tick failed: %s", self.last_error)
        finally:
            self.db.set_status(self.status())

    async def run(self) -> None:
        self.running = True
        warm = self.warmup()
        if warm == 0:
            logger.error("warmup returned no candles; aborting")
            self.running = False
            return
        logger.info(
            "engine running mode=%s strategy=%s interval=%ds",
            self.config.mode, self.config.strategy, self.config.interval_seconds,
        )
        while self.running:
            self._tick()
            await asyncio.sleep(self.config.interval_seconds)

    def stop(self) -> None:
        self.running = False

    def status(self) -> dict:
        return {
            "exchange": self.config.exchange,
            "symbol": self.config.symbol,
            "timeframe": self.config.timeframe,
            "mode": self.config.mode,
            "strategy": self.config.strategy,
            "interval_seconds": self.config.interval_seconds,
            "running": self.running,
            "ticks": self.ticks,
            "last_tick_ts": self.last_tick_ts,
            "last_error": self.last_error,
        }
