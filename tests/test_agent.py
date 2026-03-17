import networkx as nx

from ai_tpm_agent.agent import AIProjectManagerAgent


def test_build_dependency_graph_and_bottlenecks():
    agent = AIProjectManagerAgent()
    tickets = [
        {"key": "T1", "fields": {"labels": [], "issuelinks": []}},
        {
            "key": "T2",
            "fields": {
                "labels": [],
                "issuelinks": [
                    {"type": {"name": "Blocks"}, "outwardIssue": {"key": "T1"}}
                ],
            },
        },
    ]
    graph = agent.build_dependency_graph(tickets)
    assert isinstance(graph, nx.DiGraph)
    assert set(graph.nodes()) == {"T1", "T2"}
    bottlenecks = agent.identify_bottlenecks(graph)
    assert "T1" in bottlenecks or "T2" in bottlenecks


def test_predict_sprint_slippage():
    agent = AIProjectManagerAgent()
    velocity = [10, 12, 8]
    slippage = agent.predict_sprint_slippage(velocity, remaining_work=20)
    assert slippage > 0


def test_predict_sprint_slippage_with_model():
    agent = AIProjectManagerAgent()

    class DummyModel:
        def predict(self, df):
            assert list(df.columns) == ["velocity", "remaining"]
            assert df.shape == (1, 2)
            return [3.5]

    slippage = agent.predict_sprint_slippage(
        velocity_history=[10, 12, 8], remaining_work=20, model=DummyModel()
    )
    assert slippage == 3.5


def test_risk_summary_and_mitigation():
    agent = AIProjectManagerAgent()
    tickets = [
        {"key": "R1", "fields": {"labels": ["risk:high"]}},
        {"key": "R2", "fields": {"labels": ["risk:high", "risk:low"]}},
    ]
    summary = agent.summarize_risk_exposure(tickets)
    assert summary["risk_count"] == 3
    plans = agent.suggest_mitigation_plans(summary)
    assert isinstance(plans, list)


def test_mitigation_thresholds():
    agent = AIProjectManagerAgent()
    # create synthetic summaries to hit each branch
    summ = {"by_label": {"risk:low": 2, "risk:mid": 6, "risk:high": 12}}
    plans = agent.suggest_mitigation_plans(summ)
    assert any("Immediate action" in p for p in plans)
    assert any("Investigate" in p for p in plans)
    assert any("Monitor" in p for p in plans)


def test_optional_helpers_and_errors():
    agent = AIProjectManagerAgent()
    # Jira client not configured
    try:
        agent.fetch_jira_tickets("project=XYZ")
        assert False, "Expected error when Jira client missing"
    except RuntimeError:
        pass

    # GitHub velocity mocking
    class DummyRepo:
        def __init__(self, count):
            self._count = count

        def get_commits(self, since=None):
            class C:
                def __init__(self, total):
                    self.totalCount = total

            return C(self._count)

    class DummyGH:
        def get_repo(self, name):
            return DummyRepo(28)

    agent.github = DummyGH()
    vel = agent.compute_commit_velocity("foo/bar", days=7)
    assert vel == 4.0

    # burndown anomalies
    import pandas as pd

    df = pd.DataFrame({"remaining": [100, 90, 85, 20, 19]})
    anomalies = agent.detect_burndown_anomalies(df)
    assert isinstance(anomalies, list)
