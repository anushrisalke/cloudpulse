import time

import psutil
from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

app = FastAPI(title="CloudPulse")

# --- Metric definitions ---
REQUEST_COUNT = Counter(
    "cloudpulse_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "cloudpulse_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["endpoint"],
)
CPU_USAGE = Gauge("cloudpulse_cpu_usage_percent", "System CPU usage in percent")
MEMORY_USAGE = Gauge("cloudpulse_memory_usage_percent", "System memory usage in percent")
APP_UP = Gauge("cloudpulse_app_up", "1 if the app is running")
APP_UP.set(1)


# --- Middleware: runs on every request ---
@app.middleware("http")
async def track_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    endpoint = request.url.path
    REQUEST_COUNT.labels(request.method, endpoint, response.status_code).inc()
    REQUEST_LATENCY.labels(endpoint).observe(duration)
    return response


# --- Normal endpoints ---
@app.get("/")
def home():
    return {"message": "CloudPulse is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


# --- Metrics endpoint for Prometheus ---
@app.get("/metrics")
def metrics():
    CPU_USAGE.set(psutil.cpu_percent(interval=None))
    MEMORY_USAGE.set(psutil.virtual_memory().percent)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
