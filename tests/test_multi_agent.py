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
    X, y, df = make_fake_data()
    mas = MultiAgentSystem(kpis={"default": None})
    results = mas.run_workflow(X, y, LogisticRegression, solver="liblinear")
    assert "model" in results
    assert results["leakage"] is False
    assert "kpi_review" in results


def test_auditor_bias():
    from ai_multi_agent.agents import AuditorAgent

    df = pd.DataFrame({"a": [0, 1, 0, 1], "label": [1, 1, 0, 0]})
    aud = AuditorAgent()
    bias = aud.check_bias(df, "label", "a")
    assert "parity_diff" in bias
