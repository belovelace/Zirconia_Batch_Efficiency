from prometheus_client import Counter, Gauge, Histogram

REQUESTS = Counter("zirsave_requests_total", "Total HTTP requests", ["method", "endpoint"])  # labels: method, endpoint
IN_PROGRESS = Gauge("zirsave_in_progress", "Number of in-progress tasks")
REQUEST_LATENCY = Histogram("zirsave_request_latency_seconds", "Histogram of request latency seconds")

# Helper to instrument endpoints can be added in middleware
