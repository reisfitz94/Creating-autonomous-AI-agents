from typing import List, Dict, Any
import os
import requests


class AnimeAgent:
    """Allows searching and selecting anime videos from a catalogue or API."""

    def __init__(self, catalogue: List[Dict[str, Any]] = None):
        # catalogue items have 'title' and 'url'
        self.catalogue = catalogue or []

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Return list of entries matching the query.

        If the environment variable ``USE_JIKAN`` is set the method will attempt
        to query the Jikan API (a public MyAnimeList wrapper).  Otherwise it
        falls back to the local catalogue.
        """
        if os.getenv("USE_JIKAN"):
            try:
                resp = requests.get(
                    "https://api.jikan.moe/v4/anime",
                    params={"q": query, "limit": 5},
                    timeout=5,
                )
                data = resp.json().get("data", [])
                return [
                    {"title": item.get("title"), "url": item.get("url")}
                    for item in data
                ]
            except Exception:
                pass
        # fallback to catalogue search
        q = query.lower()
        return [item for item in self.catalogue if q in item.get("title", "").lower()]

    def select(self, index: int) -> Dict[str, Any]:
        """Pick an entry by index from the last search results."""
        if index < 0 or index >= len(self.catalogue):
            raise IndexError("Selection index out of range")
        return self.catalogue[index]
