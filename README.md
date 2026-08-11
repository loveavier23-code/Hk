# Trading Bot Platform

A trading bot platform wired directly to real exchange market data via
[ccxt](https://github.com/ccxt/ccxt) — no simulated or mock data anywhere in
the pipeline. Default exchange is Kraken (public endpoints, no API keys
required for market data).

## Install

```bash
pip install -r requirements.txt
cp .env.example .env   # then edit
```

## Run

```bash
python run.py engine   # market data loop: fetch -> signal -> persist
python run.py api      # REST API + dashboard on :8000
```

## Modes

- `MODE=analyze` (default) — fetches real candles, evaluates the strategy,
  records signals. **No orders are ever placed.**
- `MODE=live` — places real market orders via the exchange API. Requires
  `API_KEY` / `API_SECRET` in `.env`. Without credentials the executor
  refuses to place orders.

## Config (.env)

| Key | Default | Purpose |
|---|---|---|
| `EXCHANGE` | `kraken` | ccxt exchange id (`coinbase`, `okx`, ...) |
| `SYMBOL` | `BTC/USD` | trading pair |
| `TIMEFRAME` | `1m` | candle interval |
| `INTERVAL_SECONDS` | `60` | engine loop period |
| `MODE` | `analyze` | `analyze` or `live` |
| `STRATEGY` | `sma_cross` | strategy id (`sma_cross`, `sma_cross_rsi`) |
| `STRATEGY_FAST_PERIOD` | `10` | fast SMA window |
| `STRATEGY_SLOW_PERIOD` | `30` | slow SMA window |
| `STRATEGY_RSI_PERIOD` | `14` | RSI window |
| `STRATEGY_RSI_LOWER` / `STRATEGY_RSI_UPPER` | `30` / `70` | RSI bounds |
| `CANDLE_WARMUP` | `300` | historical candles fetched at startup |
| `DB_PATH` | `bot.db` | SQLite database |
| `CA_BUNDLE` | *(empty)* | custom CA bundle path for the exchange session |
| `API_KEY` / `API_SECRET` | *(empty)* | exchange credentials (live mode only) |
| `ORDER_AMOUNT` | `0.001` | order size in base currency |

## Architecture

```
run.py engine ──> Engine (async loop)
                    ├─ ExchangeClient (ccxt, real REST data)
                    ├─ Strategy (SMA cross / RSI, registry)
                    ├─ Executor (real orders; refused without keys)
                    └─ Database (SQLite: candles, signals, orders)
run.py api ────> FastAPI + static dashboard (canvas chart, no CDNs)
```

## API

- `GET /api/health` — engine status
- `GET /api/candles?limit=500` — stored candles
- `GET /api/signals` — strategy signals
- `GET /api/orders` — placed orders
- `GET /api/config` — effective configuration

## Adding a strategy

Add a callable `(closes: list[float], params: dict) -> Signal` to
`bot/strategies.py` and register it in the `STRATEGIES` dict. The engine
picks it up via the `STRATEGY` env var.

## Caveats

- Live trading with real money is risky. Start in `analyze` mode, and verify
  strategy behavior over real data before enabling `live`.
- ccxt exchanges have rate limits; the engine throttles itself via
  `enableRateLimit`.
- If your network egress terminates TLS with a private CA (corporate proxy,
  sandbox), point `CA_BUNDLE` at the CA bundle that validates it.
