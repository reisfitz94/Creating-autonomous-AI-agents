from ai_org_agent.orchestrator import Orchestrator


def test_orchestrator_flow():
    orch = Orchestrator()
    result = orch.run_task("predict churn")
    assert "exec" in result["outputs"]
    assert "model" in result["outputs"]
    assert "monitor" in result["outputs"]
    # log count may vary as critique can trigger retries
    assert len(result["memory"]["logs"]) >= 8


def test_vector_memory_and_tool():
    orch = Orchestrator()
    orch.store_vector({"text": "previous output", "role": "test"})
    found = orch.retrieve_similar("previous")
    assert found is not None
    # tool execution stub
    assert orch.execute_tool("1 + 1") == 2

    # drift detection stub
    assert orch.monitor.detect_drift([1, 1, 2, 2, 100]) is True


def test_simulation():
    orch = Orchestrator()
    orig = [1, 2, 3, 4]
    noisy = orch.simulate_drift(orig, noise_level=0.1)
    assert len(noisy) == len(orig)
    assert any(o != n for o, n in zip(orig, noisy))


def test_objective_context_propagates_to_outputs():
    orch = Orchestrator()
    result = orch.run_task("reduce churn")
    assert "reduce churn" in result["outputs"]["exec"].lower()
    assert "reduce churn" in result["outputs"]["arch"].lower()
    assert "reduce churn" in result["outputs"]["model"].lower()


def test_objective_propagates_to_all_agents():
    orch = Orchestrator()
    result = orch.run_task("reduce churn")
    outputs = result["outputs"]
    for key in ("audit", "risk", "deploy", "monitor", "cost"):
        assert "reduce churn" in outputs[key].lower(), f"{key} output missing objective"
