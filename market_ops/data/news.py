from typing import List, Dict, Any
import requests
from xml.etree import ElementTree as ET


def fetch_news_headlines(sources: List[str]) -> List[Dict[str, Any]]:
    """Fetch headlines from given RSS feed URLs (sources)."""
    headlines: List[Dict[str, Any]] = []
    for src in sources:
        try:
            resp = requests.get(src, timeout=5)
            tree = ET.fromstring(resp.content)
            for item in tree.findall(".//item")[:5]:
                title = (
                    item.find("title").text if item.find("title") is not None else ""
                )
                headlines.append({"source": src, "headline": title})
        except Exception:
            headlines.append({"source": src, "headline": "<error>"})
    return headlines
