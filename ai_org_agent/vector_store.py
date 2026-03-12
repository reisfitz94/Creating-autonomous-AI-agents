from collections import defaultdict
from typing import List, Dict, Any, Optional, Set


class VectorStore:
    """Very lightweight in-memory vector store for demonstration purposes."""

    def __init__(self, max_items: int = 10000):
        self.items: List[Dict[str, Any]] = []
        self.max_items = max(1, int(max_items))
        self._token_index: Dict[str, Set[int]] = defaultdict(set)

    def _tokenize(self, text: str) -> Set[str]:
        return {tok for tok in (text or "").lower().split() if tok}

    def _rebuild_index(self):
        self._token_index.clear()
        for idx, item in enumerate(self.items):
            for tok in self._tokenize(item.get("text", "")):
                self._token_index[tok].add(idx)

    def _trim_if_needed(self):
        if len(self.items) <= self.max_items:
            return
        excess = len(self.items) - self.max_items
        if excess <= 0:
            return
        self.items = self.items[excess:]
        # Keep index coherent after trimming old entries.
        self._rebuild_index()

    def add(self, text: str, metadata: Optional[Dict[str, Any]] = None):
        item = {"text": text or "", "metadata": metadata or {}}
        self.items.append(item)
        idx = len(self.items) - 1
        for tok in self._tokenize(str(item["text"])):
            self._token_index[tok].add(idx)
        self._trim_if_needed()

    def add_many(self, entries: List[Dict[str, Any]]):
        for entry in entries:
            self.add(entry.get("text", ""), metadata=entry.get("metadata", {}))

    def search(self, query: str) -> Optional[Dict[str, Any]]:
        normalized = (query or "").lower().strip()
        if not normalized:
            return None

        candidates: Set[int] = set()
        for tok in self._tokenize(normalized):
            candidates.update(self._token_index.get(tok, set()))

        if candidates:
            for idx in sorted(candidates, reverse=True):
                item = self.items[idx]
                if normalized in item.get("text", "").lower():
                    return item

        # Fallback for substring matches not captured by token index.
        for item in reversed(self.items):
            if normalized in item.get("text", "").lower():
                return item
        return None
