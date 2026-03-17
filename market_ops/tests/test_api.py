import importlib

from fastapi.testclient import TestClient
from market_ops import api
from market_ops.api import app

client = TestClient(app)


def test_status_endpoint():
    r = client.get("/status")
    assert r.status_code == 200
    assert "logs" in r.json()


def test_health_metrics_dashboard():
    h = client.get("/health")
    assert h.status_code == 200
    assert h.json()["status"] == "ok"

    m = client.get("/metrics")
    assert m.status_code == 200
    assert "requests_total" in m.json()

    d = client.get("/dashboard")
    assert d.status_code == 200
    assert "Market Ops Dashboard" in d.text


def test_run_and_strategy():
    # run once, check strategy afterwards
    r = client.post("/run")
    assert r.status_code == 200
    data = r.json()
    assert "opportunities" in data

    s = client.get("/strategy")
    assert s.status_code == 200
    assert "strategy" in s.json()


def test_experiment_endpoint():
    r = client.post("/experiment", params={"name": "foo", "features": 2, "samples": 5})
    assert r.status_code == 200
    res = r.json()
    assert res["name"] == "foo"
    assert "score" in res


def test_cli_run(capsys):
    # ensure the CLI run command executes without error; output may contain
    # the list of opportunities or logger info lines.
    import subprocess
    import sys

    out = subprocess.check_output([sys.executable, "-m", "market_ops.cli", "run"])
    assert out  # at least something was printed
    # output should either be a Python list of opportunities or include INFO logs
    assert out.strip().startswith(b"[") or b"INFO" in out


def test_api_key_protection(monkeypatch):
    monkeypatch.setattr(api, "API_KEY", "secret")
    # missing key should fail
    fail = client.post("/run")
    assert fail.status_code == 401

    # correct key should pass
    ok = client.post("/run", headers={"X-API-Key": "secret"})
    assert ok.status_code == 200

    # reset to avoid side effects for future tests
    monkeypatch.setattr(api, "API_KEY", None)


def test_security_headers_present():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["referrer-policy"] == "no-referrer"
    assert "content-security-policy" in r.headers


def test_rate_limit_on_protected_endpoints(monkeypatch):
    monkeypatch.setattr(api, "API_KEY", "secret")
    monkeypatch.setattr(api, "RATE_LIMIT_MAX_REQUESTS", 2)
    monkeypatch.setattr(api, "RATE_LIMIT_WINDOW_SEC", 60)
    api.RATE_BUCKETS.clear()

    ok1 = client.post("/run", headers={"X-API-Key": "secret"})
    ok2 = client.post("/run", headers={"X-API-Key": "secret"})
    limited = client.post("/run", headers={"X-API-Key": "secret"})

    assert ok1.status_code == 200
    assert ok2.status_code == 200
    assert limited.status_code == 429

    monkeypatch.setattr(api, "API_KEY", None)
    api.RATE_BUCKETS.clear()


def test_trusted_host_blocks_unknown_host_header():
    blocked = client.get("/health", headers={"Host": "evil.example.com"})
    assert blocked.status_code == 400


def test_cors_preflight_allows_configured_origin(monkeypatch):
    monkeypatch.setenv("MARKET_OPS_CORS_ORIGINS", "https://ops.example.com")
    reloaded_api = importlib.reload(api)
    cors_client = TestClient(reloaded_api.app)

    preflight = cors_client.options(
        "/run",
        headers={
            "Origin": "https://ops.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == "https://ops.example.com"
