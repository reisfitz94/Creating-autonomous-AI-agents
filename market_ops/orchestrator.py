import logging
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class MarketOpsCommander:
    """High-level orchestrator for market operations agent."""

    def __init__(
        self,
        data_sources: Optional[List[str]] = None,
        db_path: Optional[str] = None,
        max_workers: int = 3,
        max_logs: int = 5000,
    ):
        self.data_sources = data_sources or []
        self.memory: Dict[str, Any] = {"logs": []}
        self.max_workers = max(1, int(max_workers))
        self.max_logs = max(100, int(max_logs))
        self.db_conn = None
        if db_path:
            from .db import get_connection, init_schema, load_strategy

            self.db_conn = get_connection(db_path)
            init_schema(self.db_conn)
            # recover previous strategy if available
            self.memory["strategy"] = load_strategy(self.db_conn)
        else:
            self.memory["strategy"] = {}

    def log(self, msg: str):
        text = str(msg)
        self.memory["logs"].append(text)
        if len(self.memory["logs"]) > self.max_logs:
            self.memory["logs"] = self.memory["logs"][-self.max_logs :]
        logger.info(text)
        # also record to DB if available
        if self.db_conn:
            from .db import log_event

            log_event(self.db_conn, "log", text)

    def fetch_financial_data(self):
        from .data.finance import fetch_yahoo

        self.log("fetch_financial_data called")
        return fetch_yahoo(["AAPL", "GOOG"])

    def fetch_social_sentiment(self):
        from .data.social import fetch_twitter_sentiment

        self.log("fetch_social_sentiment called")
        return fetch_twitter_sentiment(["AAPL", "GOOG"])

    def fetch_news(self):
        from .data.news import fetch_news_headlines

        self.log("fetch_news called")
        return fetch_news_headlines(["cnn", "reuters"])

    def score_opportunities(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        from .models.scoring import simple_opportunity_score

        self.log("score_opportunities called")
        return simple_opportunity_score(data)

    def run_loop(self):
        self.log("starting run loop")

        def _safe_fetch(name: str, fn):
            try:
                return fn()
            except Exception as e:
                self.log(f"{name} failed: {e}")
                return {} if name != "news" else []

        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            f_fin = pool.submit(_safe_fetch, "finance", self.fetch_financial_data)
            f_sent = pool.submit(_safe_fetch, "sentiment", self.fetch_social_sentiment)
            f_news = pool.submit(_safe_fetch, "news", self.fetch_news)
            fin = f_fin.result()
            sent = f_sent.result()
            news = f_news.result()

        combined = {"fin": fin, "sent": sent, "news": news}
        ops = self.score_opportunities(combined)
        self.log(f"found {len(ops)} opportunities")
        # simple reinforcement: update stored strategy based on first opportunity's score
        if ops:
            self.memory.setdefault("strategy", {})
            top = ops[0]
            symbol = top.get("symbol")
            score = top.get("score", 0.0)
            if symbol is not None:
                self.memory["strategy"][symbol] = score
            from .models.reinforcement import update_strategy

            # pretend the outcome is proportional to the score
            outcome = score
            self.memory["strategy"] = update_strategy(self.memory["strategy"], outcome)
            # persist strategy to DB if available
            if self.db_conn:
                from .db import save_strategy

                save_strategy(self.db_conn, self.memory["strategy"])
        return ops
