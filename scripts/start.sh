#!/usr/bin/env bash
set -euo pipefail

# Simple local start script for dev
# Requires a Python venv with deps installed and an ASGI entrypoint at app.main:app

: "Ensure .env is loaded if present"
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs -d '\n') || true
fi

HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}

exec uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
