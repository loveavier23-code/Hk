# 🤖 AutoTrader — Autonomous Binance Futures Trading Bot

A powerful, **fully autonomous** (zero human intervention) full-stack trading-bot
platform for **Binance USDT-M Futures** (testnet by default). It scans the
market, detects regime, picks a strategy, sizes positions, places trades, and
manages risk (stops, targets, trailing, drawdown circuit-breaker) all by itself —
with a polished real-time trading-terminal dashboard.

```
React + TypeScript + Vite + Tailwind + Recharts  (frontend)
        │  REST (/api/*)  +  WebSocket (/ws)
FastAPI + Uvicorn  (backend)
        │
Autonomous Trading Engine  ──►  6 strategies + dynamic auto-regime
        │
Execution Adapter ──►  LIVE: Binance Futures testnet (signed REST)
                  └─►  SIM : realistic market simulator + paper trading
```

---

## ✨ Features

**Autonomous engine (set it and forget it)**
- Continuous scan → signal → execute → manage → repeat loop
- **Dynamic "auto" strategy** that detects trend vs. range regime and switches
  strategy per symbol automatically (also 5 standalone strategies)
- Risk-based position sizing, leverage, stop-loss / take-profit, optional
  trailing stop
- **Max-drawdown circuit breaker** auto-flattens and halts on breach, resumes on recovery
- Cooldowns between entries to avoid churn; max concurrent positions

**Strategies** (all pure-Python, no heavy deps)
| Strategy | Idea |
|---|---|
| `auto` | Regime detector → picks trend/momentum/mean-reversion per symbol |
| `ema_cross` | 12/26 EMA trend-following crossover |
| `rsi_momentum` | RSI(14) momentum breakout |
| `macd` | MACD(12,26,9) continuation |
| `mean_reversion` | Bollinger-band fade + RSI filter |
| `grid` | Grid fade around a 30-period SMA |

**Dashboard (live)**
- Equity / balance / unrealized / realized / ROI / drawdown / win-rate cards
- Live equity curve, custom SVG candlestick chart with symbol tabs
- Market scanner with per-symbol signals & strength bars
- Open positions table (live uPnL, one-click close)
- Trade history + streaming activity log
- Live strategy / risk / symbols configuration

**Two execution backends, one engine**
- **LIVE** — real signed REST calls to Binance Futures testnet (orders, leverage,
  balance/position sync, reconciliation of externally-closed positions)
- **SIM** — regime-switching synthetic market + paper order-matching engine so
  the bot, strategies, risk and dashboard run with **no network at all**

---

## 🔐 Security note (read this)

You shared your API keys in plain text. These are **testnet** keys so the risk is
limited to play-money, but **rotate/regenerate them** in the Binance Futures
testnet dashboard regardless — anything pasted in chat should be considered
compromised.

This project stores credentials **only** in `backend/.env`, which is
**gitignored** and never committed. The app loads them at runtime via
`python-dotenv`.

---

## 🚀 Quick start

### Prerequisites
- Python ≥ 3.10 and Node ≥ 18

### 1. Backend
```bash
cd backend
cp .env.example .env          # then edit .env with your testnet keys
./run.sh                      # creates venv, installs deps, runs on :8000
```

### 2. Frontend (dashboard)
```bash
cd frontend
npm install
npm run build                 # outputs to frontend/dist (served by the backend)
```
Then open **http://localhost:8000** — the backend serves the built dashboard,
the REST API, and the WebSocket from one port.

For hot-reload frontend dev instead: `npm run dev` (proxies `/api` and `/ws` to
`:8000`).

### One-shot
From the repo root:
```bash
./run.sh                      # builds dashboard then starts the backend
```

---

## ⚙️ Configuration (`backend/.env`)

| Var | Default | Meaning |
|---|---|---|
| `BINANCE_API_KEY` / `BINANCE_API_SECRET` | — | Testnet credentials |
| `BINANCE_BASE_URL` | `https://testnet.binancefuture.com` | REST base |
| `TRADING_MODE` | `auto` | `auto` (detect) \| `live` \| `sim` |
| `SYMBOLS` | `BTCUSDT,ETHUSDT,SOLUSDT` | Symbols to trade |
| `STRATEGY` | `auto` | `auto` \| `ema_cross` \| `rsi_momentum` \| `macd` \| `mean_reversion` \| `grid` |
| `LEVERAGE` | `10` | Per-trade leverage |
| `RISK_PER_TRADE_PCT` | `2.0` | % equity risked per trade (sizes via stop) |
| `STOP_LOSS_PCT` / `TAKE_PROFIT_PCT` | `2.5` / `5.0` | Stop & target distance |
| `TRAILING_STOP_PCT` | `0.0` | 0 = off; >0 ratchets stop with price |
| `MAX_POSITIONS` | `3` | Max concurrent open positions |
| `MAX_DRAWDOWN_PCT` | `12.0` | Circuit-breaker threshold |
| `LOOP_INTERVAL_SIM` / `LOOP_INTERVAL_LIVE` | `4` / `12` | Seconds between ticks |

---

## 🔌 API reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Liveness + mode |
| `GET` | `/api/state` | Full snapshot (account, positions, trades, candles, signals…) |
| `GET` | `/api/strategies` | Available strategies |
| `GET` / `POST` | `/api/config` | Read / update strategy + risk + symbols |
| `POST` | `/api/start` / `/api/stop` | Start / pause the bot |
| `POST` | `/api/close_all` | Flatten everything |
| `POST` | `/api/close_position/{symbol}` | Close one position |
| `POST` | `/api/reset` | Reset the SIM account |
| `WS` | `/ws` | Pushes a full snapshot ~every 1.5s |

---

## 🧠 How autonomy works

1. **Each tick** the engine refreshes market data + account for every symbol and
   reconciles any positions closed externally (e.g. liquidation).
2. **Circuit breaker** — if equity drawdown from peak ≥ `MAX_DRAWDOWN_PCT`, it
   flattens and halts; it resumes automatically once equity recovers.
3. **Exits** — trailing stop is ratcheted; if price hits SL/TP the position is
   closed and PnL realized.
4. **Entries** — if running, not halted, and under `MAX_POSITIONS`, each symbol
   is evaluated by the active (or auto) strategy; a strong-enough signal opens a
   risk-sized position with SL/TP attached.
5. The dashboard receives the full state over WebSocket every ~1.5s — you watch,
   it trades.

---

## 🗂 Project layout

```
backend/
  app/
    config.py          # env-driven settings
    indicators.py      # EMA, RSI, MACD, Bollinger, ATR, slope…
    state.py           # shared state + data models (JSON-serializable)
    hub.py             # WebSocket broadcast hub
    binance_client.py  # signed Binance Futures REST client (LIVE)
    simulator.py       # regime-switching market simulator (SIM)
    execution.py       # Live + Sim execution adapters (one interface)
    risk.py            # sizing, stops, trailing, drawdown breaker
    strategies.py      # 5 strategies + dynamic auto-regime selector
    engine.py          # the autonomous trading loop
    server.py          # FastAPI: REST + WS + dashboard hosting
  .env / .env.example  # credentials + config
frontend/
  src/                 # React dashboard (components, lib, types)
```

> ⚠️ **Disclaimer:** For educational/testnet use. Automated futures trading
> carries real risk. In `live` mode against testnet you trade play-money; on
> mainnet the same code would trade real funds — review risk parameters and test
> thoroughly first.
