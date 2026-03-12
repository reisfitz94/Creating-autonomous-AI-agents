from typing import Dict, Any
import os
import random

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_BEARER = os.getenv("TWITTER_BEARER_TOKEN")


def fetch_twitter_sentiment(keywords: list) -> Dict[str, Any]:
    """Return crude sentiment estimates for a list of keywords.

    If Twitter credentials are set, make a simple search request and score
    tweets via a naive polarity measure.  Otherwise fall back to random
    values, which is useful for testing and offline development.
    """
    if not keywords:
        return {}
    # Keep request volume bounded and deterministic while supporting large inputs.
    keywords = [kw for kw in dict.fromkeys(keywords) if kw][:100]

    if TWITTER_BEARER:
        try:
            import tweepy

            client = tweepy.Client(bearer_token=TWITTER_BEARER)
            sentiments: Dict[str, Any] = {}
            for kw in keywords:
                query = f"{kw} -is:retweet lang:en"
                resp = client.search_recent_tweets(
                    query, max_results=10, tweet_fields=["text"]
                )
                texts = [t.text for t in resp.data] if resp.data else []
                # very simple sentiment: count positive/negative words
                score = 0.0
                for t in texts:
                    score += t.lower().count("good")
                    score -= t.lower().count("bad")
                sentiments[kw] = {"sentiment": score}
            return sentiments
        except Exception:
            pass
    # fallback
    return {kw: {"sentiment": random.uniform(-1, 1)} for kw in keywords}
