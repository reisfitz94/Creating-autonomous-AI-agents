from market_ops.orchestrator import MarketOpsCommander


def test_basic_loop():
    moc = MarketOpsCommander()
    ops = moc.run_loop()
    assert isinstance(ops, list)
    assert "starting run loop" in moc.memory["logs"]


def test_scoring():
    from market_ops.models.scoring import simple_opportunity_score

    # feed synthetic data and verify scoring logic
    data = {
        "fin": {"A": {"price": 100, "change": 2.0}},
        "sent": {"A": {"sentiment": 0.5}},
        "news": [{"headline": "A stock is rising"}],
    }
    ops = simple_opportunity_score(data)
    assert isinstance(ops, list)
    assert ops and ops[0]["symbol"] == "A"
    assert ops[0]["score"] > 0


def test_scoring_news_match_is_token_based():
    from market_ops.models.scoring import simple_opportunity_score

    data = {
        "fin": {"AAPL": {"price": 100, "change": 0.0}},
        "sent": {"AAPL": {"sentiment": 0.0}},
        # AAPL should not match the token AAPLX.
        "news": [{"headline": "Analysts bullish on AAPLX after earnings"}],
    }
    ops = simple_opportunity_score(data)
    assert ops
    assert ops[0]["details"]["news_count"] == 0


def test_reinforcement():
    from market_ops.models.reinforcement import update_strategy

    strat = {"X": 0.2}
    new = update_strategy(strat, outcome=1.0, lr=0.5)
    assert new["X"] > 0.2


def test_experiment_runner():
    from market_ops.experiments.run import run_experiment

    res = run_experiment("test", {"features": 2, "samples": 10})
    assert res["name"] == "test"
    assert "score" in res and isinstance(res["score"], float)


def test_llm_scoring(monkeypatch, tmp_path, capsys):
    import os

    os.environ["USE_LLM"] = "1"
    os.environ["OPENAI_API_KEY"] = "dummy"

    # create fake response object
    class DummyChoice:
        def __init__(self, content):
            self.message = type("m", (), {"content": content})

    class DummyResp:
        def __init__(self, content):
            self.choices = [DummyChoice(content)]

    def fake_create(**kwargs):
        # return a JSON list string
        return DummyResp('[{"symbol": "Z", "score": 42.0}]')

    import openai

    monkeypatch.setattr(openai.ChatCompletion, "create", fake_create)

    from market_ops.models.scoring import simple_opportunity_score

    data = {"fin": {"Z": {"price": 1, "change": 1}}, "sent": {}, "news": []}
    result = simple_opportunity_score(data)
    assert isinstance(result, list)
    assert result and result[0]["symbol"] == "Z"
    assert result[0]["score"] == 42.0


def test_mlflow_logging(monkeypatch, tmp_path):
    # simulate mlflow module and ensure run_experiment logs without error
    import sys

    class DummyMlflow:
        def __init__(self):
            self.runs = []

        def set_tracking_uri(self, uri):
            pass

        def start_run(self, run_name=None):
            class Ctx:
                def __enter__(selfi):
                    return selfi

                def __exit__(selfi, exc_type, exc_val, exc_tb):
                    pass

            return Ctx()

        def log_params(self, params):
            self.last_params = params

        def log_metric(self, name, val):
            self.last_metric = (name, val)

    ml = DummyMlflow()
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "http://dummy")
    sys.modules["mlflow"] = ml

    from market_ops.experiments.run import run_experiment

    res = run_experiment("m", {"features": 1, "samples": 5})
    assert res["name"] == "m"
    assert hasattr(ml, "last_metric")


def test_logging_to_db(tmp_path):
    # orchestrator should log into sqlite when db_path provided
    dbfile = str(tmp_path / "log.db")
    moc = MarketOpsCommander(db_path=dbfile)
    moc.log("hello")
    from market_ops.db import get_connection

    conn = get_connection(dbfile)
    c = conn.cursor()
    c.execute("SELECT event,data FROM logs WHERE event='log'")
    row = c.fetchone()
    assert row and "hello" in row[1]


def test_db_logging():
    from market_ops.db import get_connection, init_schema, log_event

    conn = get_connection()
    init_schema(conn)
    log_event(conn, "test", "data")
    c = conn.cursor()
    c.execute("SELECT event,data FROM logs")
    row = c.fetchone()
    assert row == ("test", "data")


def test_strategy_persistence(tmp_path):
    from market_ops.db import get_connection, init_schema, save_strategy, load_strategy

    dbfile = str(tmp_path / "test.db")
    conn = get_connection(dbfile)
    init_schema(conn)
    save_strategy(conn, {"A": 0.5, "B": 1.2})
    loaded = load_strategy(conn)
    assert loaded == {"A": 0.5, "B": 1.2}


def test_orchestrator_with_db(tmp_path):
    # verify that orchestrator will persist strategy to provided db
    dbfile = str(tmp_path / "ops.db")
    moc = MarketOpsCommander(db_path=dbfile)
    assert moc.memory.get("strategy", {}) == {}
    # run loop with fake data to generate a strategy entry
    moc.fetch_financial_data = lambda: {"X": {"price": 10, "change": 1.0}}
    moc.fetch_social_sentiment = lambda: {"X": {"sentiment": 0.2}}
    moc.fetch_news = lambda: []
    moc.score_opportunities = lambda data: [{"symbol": "X", "score": 0.5}]
    moc.run_loop()
    # reload from db
    from market_ops.db import get_connection, load_strategy

    conn2 = get_connection(dbfile)
    strat = load_strategy(conn2)
    assert strat.get("X") == 0.5


def test_notifications():
    from market_ops.notifications import send_slack, send_email

    send_slack("hello")
    send_email("me@example.com", "sub", "body")


def test_notifications_slack(monkeypatch):
    # simulate webhook behavior
    from market_ops import notifications

    messages = []

    class DummyResp:
        def __init__(self):
            self.status_code = 200

        def raise_for_status(self):
            pass

    def fake_post(url, json, timeout):
        messages.append(json["text"])
        return DummyResp()

    monkeypatch.setattr(notifications, "SlackWebhook", "https://dummy")
    # ensure requests.post is replaced
    import requests

    monkeypatch.setattr(requests, "post", fake_post)
    notifications.send_slack("hi")
    assert messages == ["hi"]


def test_notifications_email(monkeypatch):
    from market_ops import notifications

    sent = []

    class DummySMTP:
        def __init__(self, server, port, timeout):
            pass

        def login(self, user, pw):
            pass

        def send_message(self, msg):
            sent.append(str(msg))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(notifications, "SMTP_SERVER", "smtp.example.com")
    monkeypatch.setattr(notifications, "SMTP_PORT", 25)
    monkeypatch.setattr(notifications, "SMTP_USER", "user")
    monkeypatch.setattr(notifications, "SMTP_PASSWORD", "pw")
    # patch smtplib globally
    import sys

    fake_smtp = type("m", (), {"SMTP": DummySMTP})
    sys.modules["smtplib"] = fake_smtp

    notifications.send_email("you@example.com", "subj", "body")
    assert sent


def test_scheduler_runs(monkeypatch):
    # ensure run_loop is called at least once when the scheduler is started
    called = {"count": 0}

    def fake_run(*args, **kwargs):
        called["count"] += 1

    from market_ops import scheduler

    moc = type("X", (), {"run_loop": fake_run})()
    monkeypatch.setattr(scheduler, "MarketOpsCommander", lambda: moc)

    # intercept schedule.run_pending to invoke our fake and then stop the loop
    def fake_pending():
        moc.run_loop()
        raise KeyboardInterrupt

    monkeypatch.setattr(scheduler.schedule, "run_pending", fake_pending)

    # call run_periodic; it will call fake_pending once and break
    try:
        scheduler.run_periodic(interval_minutes=1, max_cycles=5)
    except KeyboardInterrupt:
        pass

    assert called["count"] >= 1
