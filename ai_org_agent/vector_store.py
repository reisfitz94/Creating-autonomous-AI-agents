from typing import List, Dict, Any, Optional


class VectorStore:
    """Very lightweight in-memory vector store for demonstration purposes."""

    def __init__(self):
        self.items: List[Dict[str, Any]] = []

    def add(self, text: str, metadata: Optional[Dict[str, Any]] = None):
        self.items.append({"text": text, "metadata": metadata or {}})

    def search(self, query: str) -> Optional[Dict[str, Any]]:
        for item in self.items:
            if query in item["text"]:
                return item
        return None
