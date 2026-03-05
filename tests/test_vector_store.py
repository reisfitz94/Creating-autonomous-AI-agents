from ai_org_agent.vector_store import VectorStore


def test_vector_store_add_search():
    vs = VectorStore()
    vs.add("hello world", metadata={"role": "test"})
    found = vs.search("hello")
    assert found is not None
    assert found["metadata"]["role"] == "test"
    assert vs.search("missing") is None
