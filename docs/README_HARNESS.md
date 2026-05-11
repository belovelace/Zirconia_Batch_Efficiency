ZirSave harness notes

This folder contains lightweight harness scaffolding for running ZirSave in development and production.

Files added (non-destructive):

- app/config.py - pydantic settings from .env
- app/health.py - /health/live, /health/ready, /metrics endpoints
- app/metrics.py - example Prometheus metrics
- app/logging_conf.py - basic structured logging config
- app/graceful.py - graceful shutdown hooks
- app/worker.py - RQ enqueue helper
- scripts/start.sh - dev start (uvicorn --reload)
- scripts/worker_start.sh - starts rq worker
- docker/Dockerfile - minimal container image
- .env.example - example env file
- .github/workflows/ci.yaml - basic CI workflow scaffold
- tests/integration/test_playwright.py - simple readiness test
- requirements.txt - runtime dependencies

Next steps to activate harness locally

1. Populate .env from .env.example (do not commit secrets).
2. Install Python deps: python -m pip install -r requirements.txt
3. Start dependencies: redis, postgres (docker-compose or local). Example: docker run -d --name redis -p 6379:6379 redis
4. Start app: ./scripts/start.sh
5. Start worker: ./scripts/worker_start.sh
6. Run tests: pytest tests/integration -q

Production notes

- Create a systemd unit (example in README) to run uvicorn in a virtualenv and start the worker process.
- Use Prometheus to scrape /metrics and a log collector for structured logs.
