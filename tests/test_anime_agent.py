from ai_anime_agent.agent import AnimeAgent


def test_search_and_select():
    catalog = [
        {"title": "Naruto Ep 1", "url": "u1"},
        {"title": "Naruto Ep 2", "url": "u2"},
        {"title": "Bleach Ep 1", "url": "u3"},
    ]
    agent = AnimeAgent(catalog)
    results = agent.search("naruto")
    assert len(results) == 2
    sel = agent.select(1)
    assert sel["url"] == "u2"
    try:
        agent.select(10)
        assert False, "should have raised"
    except IndexError:
        pass


def test_search_jikan(monkeypatch):
    monkeypatch.setenv("USE_JIKAN", "1")

    class FakeResp:
        def __init__(self, data):
            self._data = data

        def json(self):
            return {"data": self._data}

    def fake_get(url, params, timeout):
        assert "jikan" in url
        return FakeResp([{"title": "Naruto", "url": "http://n"}])

    import requests

    monkeypatch.setattr(requests, "get", fake_get)

    agent = AnimeAgent([])
    results = agent.search("naruto")
    assert results == [{"title": "Naruto", "url": "http://n"}]


def test_search_jikan_filters_invalid_items(monkeypatch):
    monkeypatch.setenv("USE_JIKAN", "1")

    class FakeResp:
        def __init__(self, data):
            self._data = data

        def json(self):
            return {"data": self._data}

    def fake_get(url, params, timeout):
        return FakeResp(
            [
                {"title": "Valid", "url": "https://example.com/a"},
                {"title": "Bad URL", "url": "javascript:alert(1)"},
                {"title": "", "url": "https://example.com/b"},
            ]
        )

    import requests

    monkeypatch.setattr(requests, "get", fake_get)

    agent = AnimeAgent([])
    results = agent.search("naruto")
    assert results == [{"title": "Valid", "url": "https://example.com/a"}]


def test_anime_cli(monkeypatch, capsys):
    from ai_anime_agent import cli

    # patch catalogue search to return known result
    monkeypatch.setattr(
        cli.AnimeAgent, "search", lambda self, q: [{"title": "X", "url": "U"}]
    )
    import builtins

    monkeypatch.setattr(builtins, "input", lambda prompt: "0")
    monkeypatch.setattr("sys.argv", ["ai_anime_agent", "x"])
    cli.main()
    out = capsys.readouterr().out
    assert "Opening URL: U" in out
