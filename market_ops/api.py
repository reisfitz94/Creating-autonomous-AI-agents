import os
import time
from typing import Any, Dict

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import HTMLResponse

from .orchestrator import MarketOpsCommander

DB_PATH = os.getenv("MARKET_OPS_DB_PATH")
API_KEY = os.getenv("MARKET_OPS_API_KEY")

app = FastAPI(title="Market Ops Commander API", version="1.0.0")
commander = MarketOpsCommander(db_path=DB_PATH)

METRICS: Dict[str, Any] = {
    "requests_total": 0,
    "run_calls": 0,
    "experiment_calls": 0,
    "last_run_duration_sec": None,
    "last_run_ts": None,
}


def _touch_request_metric() -> None:
    METRICS["requests_total"] += 1


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Require an API key when MARKET_OPS_API_KEY is configured."""
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key",
        )


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
    html = f"""
    <html>
      <head><title>Market Ops Dashboard</title></head>
      <body style='font-family: sans-serif; max-width: 900px; margin: 24px auto;'>
        <h1>Market Ops Dashboard</h1>
        <p><b>Requests:</b> {METRICS['requests_total']} | <b>Runs:</b> {METRICS['run_calls']} | <b>Experiments:</b> {METRICS['experiment_calls']}</p>
        <h2>Strategy</h2>
        <pre>{strategy}</pre>
        <h2>Recent Logs</h2>
        <pre>{logs[-25:]}</pre>
      </body>
    </html>
    """
    return html
