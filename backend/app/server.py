"""FastAPI application: REST control plane + live WebSocket + dashboard hosting."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import settings
from .engine import TradingEngine
from .hub import hub
from .logger import get_logger, setup_logging
from .state import state
from . import strategies as strat

log = get_logger("server")

setup_logging()
engine = TradingEngine(settings)

app = FastAPI(title="AutoTrader — Binance Futures Bot", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


# ---------------- request models ----------------
class ConfigUpdate(BaseModel):
    strategy: str | None = None
    leverage: int | None = None
    risk_per_trade_pct: float | None = None
    stop_loss_pct: float | None = None
    take_profit_pct: float | None = None
    trailing_stop_pct: float | None = None
    max_positions: int | None = None
    max_drawdown_pct: float | None = None
    symbols: list[str] | None = None


# ---------------- REST ----------------
@app.on_event("startup")
async def _startup() -> None:
    state.log("AutoTrader booting up…", "INFO", "server")
    await engine.bootstrap()
    engine.set_running(True)          # fully autonomous by default
    engine.start_loop()
    asyncio.create_task(hub.broadcaster_loop(interval=1.5))
    log.info("Startup complete — mode=%s running=%s", state.mode, state.running)


@app.on_event("shutdown")
async def _shutdown() -> None:
    state.log("AutoTrader shutting down…", "WARNING", "server")
    await engine.shutdown()


@app.get("/api/health")
async def health():
    return {"ok": True, "mode": state.mode, "running": state.running, "connected": state.connected}


@app.get("/api/state")
async def get_state():
    return state.snapshot()


@app.get("/api/strategies")
async def get_strategies():
    return {"strategies": strat.list_strategies()}


@app.get("/api/config")
async def get_config():
    return {
        "strategy": state.strategy,
        "auto_strategy": state.auto_strategy,
        "symbols": state.symbols,
        "mode": state.mode,
        **engine.cfg.__dict__,
    }


@app.post("/api/config")
async def update_config(body: ConfigUpdate):
    data = body.model_dump()
    if data.get("symbols") is not None:
        await engine.set_symbols(data["symbols"])
    risk_fields = {k: v for k, v in data.items()
                   if k != "symbols" and k != "strategy" and v is not None}
    if risk_fields:
        engine.update_risk(risk_fields)
    if data.get("strategy"):
        engine.set_strategy(data["strategy"])
    return {"ok": True, "config": await get_config()}


@app.post("/api/start")
async def start_bot():
    engine.set_running(True)
    return {"ok": True, "running": state.running}


@app.post("/api/stop")
async def stop_bot():
    engine.set_running(False)
    return {"ok": True, "running": state.running}


@app.post("/api/close_all")
async def close_all():
    await engine.close_all()
    return {"ok": True}


@app.post("/api/close_position/{symbol}")
async def close_position(symbol: str):
    ok = await engine.manual_close(symbol.upper())
    return {"ok": ok}


@app.post("/api/reset")
async def reset():
    await engine.reset_sim()
    return {"ok": True}


# ---------------- WebSocket ----------------
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await hub.connect(ws)
    try:
        # send an immediate snapshot
        import json
        await ws.send_text(json.dumps(state.snapshot()))
        while True:
            await ws.receive_text()  # ignore inbound; we push snapshots
    except WebSocketDisconnect:
        hub.disconnect(ws)
    except Exception:
        hub.disconnect(ws)


# ---------------- dashboard (static) ----------------
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
else:
    @app.get("/")
    async def root():
        return JSONResponse({
            "message": "AutoTrader API is running. Build the dashboard: cd frontend && npm install && npm run build",
            "api": ["/api/health", "/api/state", "/api/strategies", "/api/config",
                    "/api/start", "/api/stop", "/api/close_all", "/ws"],
        })


def main():
    import uvicorn
    uvicorn.run("app.server:app", host=settings.host, port=settings.port,
                reload=False, log_level="info", app_dir=str(Path(__file__).resolve().parent.parent))


if __name__ == "__main__":
    main()
