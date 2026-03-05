from fastapi.testclient import TestClient
from market_ops.api import app

client = TestClient(app)


def test_status_endpoint():
    r = client.get("/status")
    assert r.status_code == 200
    assert "logs" in r.json()


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
    import subprocess, sys

    out = subprocess.check_output([sys.executable, "-m", "market_ops.cli", "run"])
    assert out  # at least something was printed
    # output should either be a Python list of opportunities or include INFO logs
    assert out.strip().startswith(b"[") or b"INFO" in out
