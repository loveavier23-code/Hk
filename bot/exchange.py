import ccxt

from .config import Config


class ExchangeError(Exception):
    pass


class ExchangeClient:
    def __init__(self, config: Config):
        self.config = config
        params = {"enableRateLimit": True}
        if config.has_credentials():
            params["apiKey"] = config.api_key
            params["secret"] = config.api_secret
        if not hasattr(ccxt, config.exchange):
            raise ExchangeError(f"Unknown exchange {config.exchange!r}")
        self.exchange = getattr(ccxt, config.exchange)(params)
        if config.ca_bundle:
            self.exchange.session.verify = config.ca_bundle
            self.exchange.session.trust_env = True
        self._markets_loaded = False

    def _load_markets(self) -> None:
        if not self._markets_loaded:
            self.exchange.load_markets()
            self._markets_loaded = True

    def _require_symbol(self, symbol: str | None) -> str:
        target = symbol or self.config.symbol
        self._load_markets()
        if target not in self.exchange.markets:
            raise ExchangeError(f"Symbol {target!r} not traded on {self.config.exchange}")
        return target

    def fetch_ohlcv(
        self, symbol: str | None = None, timeframe: str | None = None, limit: int = 100
    ) -> list[list]:
        target = self._require_symbol(symbol)
        return self.exchange.fetch_ohlcv(
            target, timeframe or self.config.timeframe, limit=limit
        )

    def fetch_ticker(self, symbol: str | None = None) -> dict:
        target = self._require_symbol(symbol)
        return self.exchange.fetch_ticker(target)

    def fetch_balance(self) -> dict:
        if not self.config.has_credentials():
            raise ExchangeError("API credentials required to read balances")
        return self.exchange.fetch_balance()

    def create_market_order(self, side: str, amount: float, symbol: str | None = None) -> dict:
        if not self.config.has_credentials():
            raise ExchangeError("API credentials required to place orders")
        target = self._require_symbol(symbol)
        return self.exchange.create_order(target, "market", side, amount)

    def create_limit_order(
        self, side: str, amount: float, price: float, symbol: str | None = None
    ) -> dict:
        if not self.config.has_credentials():
            raise ExchangeError("API credentials required to place orders")
        target = self._require_symbol(symbol)
        return self.exchange.create_order(target, "limit", side, amount, price)
