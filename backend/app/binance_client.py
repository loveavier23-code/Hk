"""Binance USDT-M Futures REST client (HMAC signed).

Built directly on httpx so there are no heavyweight dependencies and we have
full control over testnet endpoint URLs and error handling. Used only in LIVE
mode; if the host is unreachable, the engine falls back to SIM mode.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import time
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from .logger import get_logger

log = get_logger("binance")


class BinanceError(Exception):
    def __init__(self, code: int, msg: str, status: int):
        super().__init__(f"[{status}] code={code} {msg}")
        self.code = code
        self.msg = msg
        self.status = status


class BinanceFuturesClient:
    def __init__(self, api_key: str, api_secret: str, base_url: str, timeout: float = 12.0):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _http(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    def _sign(self, query: str) -> str:
        return hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ----- core request -----
    async def request(self, method: str, path: str, params: dict | None = None,
                      signed: bool = False, _retry: int = 0) -> Any:
        params = dict(params or {})
        if signed:
            if "timestamp" not in params:
                params["timestamp"] = int(time.time() * 1000)
            params.setdefault("recvWindow", 10000)

        query = urlencode(params) if params else ""
        if signed:
            sig = self._sign(query)
            query = f"{query}&signature={sig}" if query else f"signature={sig}"

        url = f"{self.base_url}{path}"
        full = f"{url}?{query}" if query else url
        headers = {"X-MBX-APIKEY": self.api_key} if signed else {}
        client = await self._http()
        try:
            resp = await client.request(method, full, headers=headers)
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as e:
            raise BinanceError(-1, f"network: {e}", 0)

        if resp.status_code != 200:
            try:
                body = resp.json()
                code = body.get("code", resp.status_code)
                msg = body.get("msg", resp.text)
            except Exception:
                code, msg = resp.status_code, resp.text
            raise BinanceError(code, msg, resp.status_code)
        if not resp.content:
            return None
        return resp.json()

    # ----- public -----
    async def ping(self) -> bool:
        try:
            await self.request("GET", "/fapi/v1/ping")
            return True
        except Exception as e:
            log.debug("ping failed: %s", e)
            return False

    async def server_time(self) -> int:
        data = await self.request("GET", "/fapi/v1/time")
        return data["serverTime"]

    async def price(self, symbol: str) -> float:
        data = await self.request("GET", "/fapi/v1/ticker/price", {"symbol": symbol})
        return float(data["price"])

    async def klines(self, symbol: str, interval: str = "1m", limit: int = 200) -> list[list]:
        data = await self.request("GET", "/fapi/v1/klines",
                                  {"symbol": symbol, "interval": interval, "limit": limit})
        return [[int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])] for k in data]

    # ----- account (signed) -----
    async def balance(self) -> list[dict]:
        data = await self.request("GET", "/fapi/v2/balance", signed=True)
        out = []
        for d in data:
            out.append({
                "asset": d["asset"],
                "balance": float(d["balance"]),
                "available": float(d["availableBalance"]),
                "pnl": float(d.get("crossUnPnl", 0)),
            })
        return out

    async def usdt_equity(self) -> tuple[float, float]:
        bal = await self.balance()
        for d in bal:
            if d["asset"] == "USDT":
                return d["balance"], d["balance"] + d["pnl"]
        # fallback: sum
        total = sum(d["balance"] for d in bal)
        return total, total

    async def positions(self) -> list[dict]:
        data = await self.request("GET", "/fapi/v2/positionRisk", signed=True)
        out = []
        for d in data:
            amt = float(d["positionAmt"])
            if amt == 0:
                continue
            out.append({
                "symbol": d["symbol"],
                "side": "LONG" if amt > 0 else "SHORT",
                "qty": abs(amt),
                "entry": float(d["entryPrice"]),
                "mark": float(d["markPrice"]),
                "unrealized": float(d["unRealizedProfit"]),
                "leverage": int(d["leverage"]),
            })
        return out

    async def set_leverage(self, symbol: str, leverage: int) -> dict:
        try:
            return await self.request("POST", "/fapi/v1/leverage",
                                      {"symbol": symbol, "leverage": leverage}, signed=True)
        except BinanceError as e:
            if e.code == -4043:  # no need to change
                return {}
            raise

    async def place_order(self, symbol: str, side: str, quantity: float,
                          order_type: str = "MARKET", price: float | None = None,
                          reduce_only: bool = False, stop_price: float | None = None,
                          time_in_force: str | None = None, new_client_order_id: str | None = None) -> dict:
        params: dict = {
            "symbol": symbol,
            "side": side,            # "BUY" / "SELL"
            "type": order_type,
            "quantity": f"{quantity:.3f}",
        }
        if reduce_only:
            params["reduceOnly"] = "true"
        if price is not None:
            params["price"] = f"{price:.2f}"
            params.setdefault("timeInForce", "GTC")
        if stop_price is not None:
            params["stopPrice"] = f"{stop_price:.2f}"
        if time_in_force:
            params["timeInForce"] = time_in_force
        if new_client_order_id:
            params["newClientOrderId"] = new_client_order_id
        return await self.request("POST", "/fapi/v1/order", params, signed=True)

    async def close_position_market(self, symbol: str, qty: float, is_long: bool) -> dict:
        side = "SELL" if is_long else "BUY"
        return await self.place_order(symbol, side, qty, order_type="MARKET", reduce_only=True)

    async def get_income(self, symbol: str | None = None, limit: int = 50) -> list[dict]:
        params = {"limit": limit}
        if symbol:
            params["symbol"] = symbol
        data = await self.request("GET", "/fapi/v1/income", params, signed=True)
        return data

    async def account_info(self) -> dict:
        return await self.request("GET", "/fapi/v2/account", signed=True)
