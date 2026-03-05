from ai_org_agent.orchestrator import Orchestrator


def test_execute_tool_safe():
    orch = Orchestrator()
    assert orch.execute_tool("1 + 2 * 3") == 7
    # disallowed name
    res = orch.execute_tool("__import__('os').system('echo hi')")
    assert isinstance(res, str) and "tool_error" in res


def test_self_critique():
    orch = Orchestrator()
    # with the current critique rules short strings are rejected
    assert not orch.self_critique("this is fine")
    assert not orch.self_critique("error occurred")
    assert not orch.self_critique("")
    # long healthy output should pass
    assert orch.self_critique("a" * 100)
