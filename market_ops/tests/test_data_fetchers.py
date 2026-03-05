from market_ops.data.finance import fetch_yahoo
from market_ops.data.social import fetch_twitter_sentiment
from market_ops.data.news import fetch_news_headlines


def test_fetchers():
    assert "AAPL" in fetch_yahoo(["AAPL"])
    assert "bitcoin" in fetch_twitter_sentiment(["bitcoin"])
    assert len(fetch_news_headlines(["cnn"])) == 1


def test_social_with_tweepy(monkeypatch):
    # simulate tweepy.Client returning fake tweets
    class FakeTweet:
        def __init__(self, text):
            self.text = text

    class FakeResp:
        def __init__(self, data):
            self.data = data

    class FakeClient:
        def __init__(self, bearer_token=None):
            pass

        def search_recent_tweets(self, query, max_results, tweet_fields):
            return FakeResp([FakeTweet("good day"), FakeTweet("bad day")])

    monkeypatch.setenv("TWITTER_BEARER_TOKEN", "dummy")
    # inject a fake tweepy module with Client class
    import sys

    fake_module = type("m", (), {"Client": FakeClient})
    sys.modules["tweepy"] = fake_module
    result = fetch_twitter_sentiment(["test"])
    assert "test" in result
    assert isinstance(result["test"]["sentiment"], float)
