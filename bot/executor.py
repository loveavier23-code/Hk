import time

from .config import Config
from .db import Database
from .exchange import ExchangeClient


class ExecutionError(Exception):
    pass


class Executor:
    def __init__(self, config: Config, exchange: ExchangeClient, db: Database):
        self.config = config
        self.exchange = exchange
        self.db = db

    def execute(self, side: str, price: float) -> dict:
        if not self.config.is_live():
            raise ExecutionError(
                "MODE=analyze: signals are logged but no orders are placed"
            )
        if not self.config.has_credentials():
            raise ExecutionError(
                "MODE=live requires API_KEY and API_SECRET for the configured exchange"
            )
        order = self.exchange.create_market_order(side, self.config.order_amount)
        record = {
            "ts": int(time.time() * 1000),
            "symbol": self.config.symbol,
            "side": side,
            "amount": self.config.order_amount,
            "price": order.get("price") or price,
            "status": order.get("status", "submitted"),
            "exchange_id": order.get("id"),
        }
        self.db.insert_order(record)
        return record
