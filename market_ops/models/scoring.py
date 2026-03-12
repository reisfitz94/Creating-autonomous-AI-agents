from typing import Dict, Any, List
import os

try:
    import openai
except ImportError:
    openai = None


def simple_opportunity_score(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Produce a list of scored "opportunities" based on combined data.

    The algorithm is intentionally simplistic: it combines the financial
    percent change, a sentiment score and a crude news count into a single
    score.  If the environment variable ``USE_LLM`` is set and ``openai`` is
    installed, the function will delegate to an OpenAI ChatCompletion call to
    score the opportunities instead of the heuristic.
    """
    fin = data.get("fin", {}) or {}
    sent = data.get("sent", {}) or {}
    news = data.get("news", []) or []

    # basic heuristics
    scores: List[Dict[str, Any]] = []
    for symbol, info in fin.items():
        raw = info.get("change", 0.0) or 0.0
        try:
            pct_change = float(raw) / 100.0  # convert from percent
        except (TypeError, ValueError):
            pct_change = 0.0
        try:
            sentiment = float(sent.get(symbol, {}).get("sentiment", 0.0) or 0.0)
        except (TypeError, ValueError):
            sentiment = 0.0
        news_count = sum(
            1 for item in news if symbol.lower() in item.get("headline", "").lower()
        )
        score = pct_change * 0.5 + sentiment * 0.3 + news_count * 0.2
        scores.append(
            {
                "symbol": symbol,
                "score": score,
                "details": {
                    "pct_change": pct_change,
                    "sentiment": sentiment,
                    "news_count": news_count,
                },
            }
        )

    # sort descending
    scores.sort(key=lambda x: x["score"], reverse=True)

    # optionally call LLM for the final decision
    if os.getenv("USE_LLM") and openai:
        key = os.getenv("OPENAI_API_KEY")
        if key:
            openai.api_key = key
            try:
                llm_input = scores[:50]
                prompt = f"Score these market opportunities and return strict JSON list with keys symbol and score:\n{llm_input}"
                resp = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150,
                )
                text = resp.choices[0].message.content.strip()
                # naive parse: expect JSON list similar to scores
                import json

                llm_scores = json.loads(text)
                if isinstance(llm_scores, list):
                    cleaned: List[Dict[str, Any]] = []
                    for row in llm_scores:
                        if not isinstance(row, dict):
                            continue
                        symbol = row.get("symbol")
                        try:
                            score = float(row.get("score", 0.0))
                        except (TypeError, ValueError):
                            score = 0.0
                        if symbol:
                            cleaned.append({"symbol": symbol, "score": score})
                    if cleaned:
                        return cleaned
            except Exception:
                # fall back to heuristic
                pass

    return scores
