from typing import List, Dict, Any, Optional
import os
import requests  # type: ignore[import-untyped]
from requests.adapters import HTTPAdapter  # type: ignore[import-untyped]

try:
    from urllib3.util.retry import Retry
except Exception:  # pragma: no cover - optional import compatibility
    Retry = None


class AnimeAgent:
    """Allows searching and selecting anime videos from a catalogue or API."""

    def __init__(self, catalogue: Optional[List[Dict[str, Any]]] = None):
        # catalogue items have 'title' and 'url'
        self.catalogue = catalogue or []
        self.last_results: List[Dict[str, Any]] = list(self.catalogue)
        self._cache: Dict[str, List[Dict[str, Any]]] = {}
        self._session = requests.Session()
        if Retry is not None:
            retries = Retry(
                total=2, backoff_factor=0.2, status_forcelist=[429, 500, 502, 503, 504]
            )
            self._session.mount("https://", HTTPAdapter(max_retries=retries))

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Return list of entries matching the query.

        If the environment variable ``USE_JIKAN`` is set the method will attempt
        to query the Jikan API (a public MyAnimeList wrapper).  Otherwise it
        falls back to the local catalogue.
        """
        normalized = (query or "").strip().lower()
        if not normalized:
            self.last_results = []
            return []

        if normalized in self._cache:
            self.last_results = self._cache[normalized]
            return list(self.last_results)

        if os.getenv("USE_JIKAN"):
            try:
                # Use requests.get for easier test mocking compatibility.
                resp = requests.get(
                    "https://api.jikan.moe/v4/anime",
                    params={"q": normalized, "limit": 20},
                    timeout=5,
                )
                data = resp.json().get("data", []) if resp is not None else []
                results = [
                    {"title": item.get("title"), "url": item.get("url")}
                    for item in data
                    if item.get("title") and item.get("url")
                ]
                self.last_results = results
                self._cache[normalized] = list(results)
                return results
            except Exception:
                pass
        # fallback to catalogue search
        results = [
            item
            for item in self.catalogue
            if normalized in item.get("title", "").lower()
        ]
        self.last_results = results
        self._cache[normalized] = list(results)
        return results

    def select(self, index: int) -> Dict[str, Any]:
        """Pick an entry by index from the last search results."""
        source = self.last_results if self.last_results else self.catalogue
        if index < 0 or index >= len(source):
            raise IndexError("Selection index out of range")
        return source[index]
