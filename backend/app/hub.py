"""Tiny pub/sub hub broadcasting state snapshots to dashboard clients."""
from __future__ import annotations

import asyncio
import json
from typing import Set

from fastapi import WebSocket

from .logger import get_logger
from .state import state

log = get_logger("hub")


class Hub:
    def __init__(self):
        self.clients: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.clients.add(ws)
        log.info("WS client connected (total=%d)", len(self.clients))

    def disconnect(self, ws: WebSocket) -> None:
        self.clients.discard(ws)
        log.info("WS client disconnected (total=%d)", len(self.clients))

    async def broadcast_snapshot(self) -> None:
        if not self.clients:
            return
        payload = json.dumps(state.snapshot())
        dead = []
        for ws in list(self.clients):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def broadcaster_loop(self, interval: float = 1.5) -> None:
        """Continuously push fresh snapshots at a fixed cadence."""
        while True:
            try:
                await self.broadcast_snapshot()
            except Exception as e:
                log.warning("broadcast error: %s", e)
            await asyncio.sleep(interval)


hub = Hub()
