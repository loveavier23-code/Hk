from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .config import Config
from .db import Database
from .exchange import ExchangeClient

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def create_app(config: Config, engine=None) -> FastAPI:
    app = FastAPI(title="Trading Bot Platform", version="1.0.0")
    db = Database(config)
    exchange = ExchangeClient(config)

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC_DIR / "dashboard.html")

    @app.get("/api/health")
    def health():
        if engine is not None:
            return {"status": "running" if engine.running else "stopped", **engine.status()}
        state = db.get_status()
        if state is None:
            return {"status": "standalone", "mode": config.mode}
        return {"status": "running" if state.get("running") else "stopped", **state}

    @app.get("/api/candles")
    def candles(
        symbol: str = Query(default=None),
        timeframe: str = Query(default=None),
        limit: int = Query(default=300, ge=1, le=2000),
    ):
        target = symbol or config.symbol
        tf = timeframe or config.timeframe
        rows = db.candles(target, tf, limit=limit)
        return {
            "symbol": target,
            "timeframe": tf,
            "candles": [dict(r) for r in reversed(rows)],
        }

    @app.get("/api/signals")
    def signals(limit: int = Query(default=100, ge=1, le=1000)):
        return {"signals": [dict(r) for r in db.signals(limit)]}

    @app.get("/api/orders")
    def orders(limit: int = Query(default=100, ge=1, le=1000)):
        return {"orders": [dict(r) for r in db.orders(limit)]}

    @app.get("/api/equity")
    def equity(limit: int = Query(default=500, ge=1, le=5000)):
        return {"equity": [dict(r) for r in db.equity(limit)]}

    @app.get("/api/config")
    def config_endpoint():
        public = {
            "exchange": config.exchange,
            "symbol": config.symbol,
            "timeframe": config.timeframe,
            "interval_seconds": config.interval_seconds,
            "mode": config.mode,
            "strategy": config.strategy,
            "strategy_params": config.strategy_params(),
            "order_amount": config.order_amount,
            "credentials_configured": config.has_credentials(),
        }
        return public

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    return app
