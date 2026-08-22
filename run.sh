#!/usr/bin/env bash
# Build the dashboard and run the full stack from the repository root.
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "==> Building dashboard…"
cd "$ROOT/frontend"
npm install
npm run build

echo "==> Starting backend (API + WS + dashboard)…"
cd "$ROOT/backend"
./run.sh
