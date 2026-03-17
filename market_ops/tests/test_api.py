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
