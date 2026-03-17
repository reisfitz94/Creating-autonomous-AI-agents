import pandas as pd
from sklearn.linear_model import LogisticRegression

from ai_multi_agent.orchestrator import MultiAgentSystem


def make_fake_data():
    df = pd.DataFrame(
        {
            "feature": range(10),
            "target": [0, 1] * 5,
            "protected": [0, 0, 1, 1] * 2 + [0, 1],
        }
    )
    return df[["feature", "protected"]], df["target"], df


def test_multi_agent_workflow():
    X, y, _ = make_fake_data()
    mas = MultiAgentSystem(kpis={"default": None})
    results = mas.run_workflow(X, y, LogisticRegression, solver="liblinear")
    assert "model" in results
    assert not results["leakage"]
    assert "kpi_review" in results


def test_auditor_bias():
    from ai_multi_agent.agents import AuditorAgent

    df = pd.DataFrame({"a": [0, 1, 0, 1], "label": [1, 1, 0, 0]})
    aud = AuditorAgent()
    bias = aud.check_bias(df, "label", "a")
    assert "parity_diff" in bias


def test_auditor_check_outliers():
    from ai_multi_agent.agents import AuditorAgent

    # Use z_threshold=1.5: for n=5 the maximum possible z-score is ~1.79,
    # so 3.0 (the default) never flags anything in tiny datasets.
    df = pd.DataFrame({"a": [1, 1, 1, 1, 100], "b": [2, 2, 2, 2, 200]})
    aud = AuditorAgent()
    outliers = aud.check_outliers(df, z_threshold=1.5)
    assert "a" in outliers
    assert "b" in outliers
    assert outliers["a"] == 1


def test_business_reviewer_kpi_with_threshold():
    from ai_multi_agent.agents import BusinessReviewerAgent

    X, y, _ = make_fake_data()
    model = LogisticRegression(solver="liblinear").fit(X, y)
    reviewer = BusinessReviewerAgent(kpis={"accuracy": 0.5})
    result = reviewer.assess_kpi_alignment(model, "accuracy")
    # A fitted model with threshold defined must produce a comparison string.
    assert "accuracy" in result.lower()
    assert "meets" in result.lower() or "not meet" in result.lower()


def test_business_reviewer_unknown_kpi():
    from ai_multi_agent.agents import BusinessReviewerAgent

    X, y, _ = make_fake_data()
    model = LogisticRegression(solver="liblinear").fit(X, y)
    reviewer = BusinessReviewerAgent(kpis={})
    result = reviewer.assess_kpi_alignment(model, "nonexistent")
    assert "no kpi" in result.lower()
