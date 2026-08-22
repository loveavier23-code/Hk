#!/usr/bin/env bash
# Start the AutoTrader backend (serves the API, WebSocket and dashboard).
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
else
  source .venv/bin/activate
fi
exec python -m uvicorn app.server:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
