#!/usr/bin/env bash
set -euo pipefail

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs -d '\n') || true
fi

REDIS_URL=${REDIS_URL:-redis://localhost:6379/0}

# Start an RQ worker for the "default" queue
exec rq worker --url "$REDIS_URL" default
