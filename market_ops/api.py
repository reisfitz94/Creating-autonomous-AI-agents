import os
import time
from collections import defaultdict, deque
from html import escape
import hmac
from typing import Any, Dict

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse

from .config import get_bool_env, get_csv_env, get_int_env
from .orchestrator import MarketOpsCommander

DB_PATH = os.getenv("MARKET_OPS_DB_PATH")
API_KEY = os.getenv("MARKET_OPS_API_KEY")

app = FastAPI(title="Market Ops Commander API", version="1.0.0")
commander = MarketOpsCommander(db_path=DB_PATH)

ALLOWED_HOSTS = get_csv_env(
    "MARKET_OPS_ALLOWED_HOSTS", ["127.0.0.1", "localhost", "testserver"]
)
CORS_ORIGINS = get_csv_env("MARKET_OPS_CORS_ORIGINS", [])
ENFORCE_HTTPS = get_bool_env("MARKET_OPS_ENFORCE_HTTPS", False)
RATE_LIMIT_WINDOW_SEC = max(get_int_env("MARKET_OPS_RATE_LIMIT_WINDOW_SEC", 60), 1)
RATE_LIMIT_MAX_REQUESTS = max(get_int_env("MARKET_OPS_RATE_LIMIT_MAX_REQUESTS", 30), 1)

RATE_BUCKETS: dict[str, deque[float]] = defaultdict(deque)

METRICS: Dict[str, Any] = {
    "requests_total": 0,
    "run_calls": 0,
    "experiment_calls": 0,
    "last_run_duration_sec": None,
    "last_run_ts": None,
}

app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

if ENFORCE_HTTPS:
    app.add_middleware(HTTPSRedirectMiddleware)

if CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["X-API-Key", "Content-Type"],
    )


def _touch_request_metric() -> None:
    METRICS["requests_total"] += 1


def _get_effective_api_key() -> str | None:
    # Allow tests to monkeypatch API_KEY while still supporting runtime env updates.
    return API_KEY if API_KEY is not None else os.getenv("MARKET_OPS_API_KEY")


def _enforce_rate_limit(request: Request, scope: str) -> None:
    client_host = request.client.host if request.client else "unknown"
    now = time.time()
    bucket = RATE_BUCKETS[f"{client_host}:{scope}"]
    cutoff = now - RATE_LIMIT_WINDOW_SEC
    while bucket and bucket[0] < cutoff:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )
    bucket.append(now)


def require_api_key(
    request: Request, x_api_key: str | None = Header(default=None)
) -> None:
    """Require an API key when MARKET_OPS_API_KEY is configured."""
    configured_api_key = _get_effective_api_key()
    if not configured_api_key:
        return
    _enforce_rate_limit(request, "protected")
    if not x_api_key or not hmac.compare_digest(x_api_key, configured_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )


@app.middleware("http")
async def set_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; "
        "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
    )
    return response


@app.get("/health")
def health():
    _touch_request_metric()
    return {"status": "ok", "service": "market-ops"}


@app.get("/metrics")
def metrics():
    _touch_request_metric()
    return METRICS


@app.get("/status")
def status_view():
    _touch_request_metric()
    return {"logs": commander.memory.get("logs", [])}


@app.get("/strategy")
def get_strategy():
    _touch_request_metric()
    return {"strategy": commander.memory.get("strategy", {})}


@app.post("/run")
def run(_auth: None = Depends(require_api_key)):
    _touch_request_metric()
    start = time.time()
    ops = commander.run_loop()
    METRICS["run_calls"] += 1
    METRICS["last_run_duration_sec"] = round(time.time() - start, 4)
    METRICS["last_run_ts"] = int(time.time())
    return {"opportunities": ops}


@app.post("/experiment")
def start_experiment(
    name: str,
    features: int = 3,
    samples: int = 100,
    _auth: None = Depends(require_api_key),
):
    _touch_request_metric()
    from .experiments.run import run_experiment

    METRICS["experiment_calls"] += 1
    res = run_experiment(name, {"features": features, "samples": samples})
    return res


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    _touch_request_metric()
    logs = commander.memory.get("logs", [])
    strategy = commander.memory.get("strategy", {})
    safe_strategy = escape(str(strategy))
    safe_logs = escape(str(logs[-25:]))
    html = f"""
    <html>
      <head><title>Market Ops Dashboard</title></head>
      <body style='font-family: sans-serif; max-width: 900px; margin: 24px auto;'>
        <h1>Market Ops Dashboard</h1>
        <p><b>Requests:</b> {METRICS['requests_total']} | <b>Runs:</b> {METRICS['run_calls']} | <b>Experiments:</b> {METRICS['experiment_calls']}</p>
        <h2>Strategy</h2>
        <pre>{safe_strategy}</pre>
        <h2>Recent Logs</h2>
        <pre>{safe_logs}</pre>
      </body>
    </html>
    """
    return html
