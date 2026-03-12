from typing import List, Dict, Any
import requests  # type: ignore[import-untyped]
from xml.etree import ElementTree as ET


def fetch_news_headlines(sources: List[str]) -> List[Dict[str, Any]]:
    """Fetch headlines from given RSS feed URLs (sources)."""
    if not sources:
        return []
    headlines: List[Dict[str, Any]] = []
    for src in sources:
        if not str(src).startswith(("http://", "https://")):
            headlines.append({"source": src, "headline": "<error>"})
            continue
        try:
            resp = requests.get(src, timeout=5)
            resp.raise_for_status()
            tree = ET.fromstring(resp.content)
            for item in tree.findall(".//item")[:5]:
                title_el = item.find("title")
                title = title_el.text if title_el is not None else ""
                headlines.append({"source": src, "headline": title})
        except Exception:
            headlines.append({"source": src, "headline": "<error>"})
    return headlines
