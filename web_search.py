"""
Web search fallback using DuckDuckGo Instant Answer API.

No API key required. Used only when RAG + local KB both miss.
Returns a concise answer string or None if search fails/returns nothing.
"""
import logging
import urllib.parse
import urllib.request
import json
from typing import Optional

logger = logging.getLogger(__name__)

_DDG_URL = "https://api.duckduckgo.com/"
_TIMEOUT = 6  # seconds — keep low to not block the UI thread


def search(query: str, max_chars: int = 600) -> Optional[str]:
    """
    Query DuckDuckGo Instant Answer API (no key needed, no scraping).
    Returns a plain-text answer snippet or None.
    """
    params = urllib.parse.urlencode({
        "q": query,
        "format": "json",
        "no_html": "1",
        "skip_disambig": "1",
        "no_redirect": "1",
    })
    url = f"{_DDG_URL}?{params}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SilentStrategist/1.0"})
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        logger.warning(f"Web search request failed: {e}")
        return None

    # Priority: AbstractText > Answer > first RelatedTopic summary
    text = (
        data.get("AbstractText")
        or data.get("Answer")
        or _first_topic(data.get("RelatedTopics", []))
    )

    if not text:
        logger.debug("Web search returned no useful content for query: %s", query[:60])
        return None

    text = text.strip()
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0] + "..."

    logger.info(f"Web search found result ({len(text)} chars) for: {query[:60]}")
    return text


def _first_topic(topics: list) -> Optional[str]:
    for t in topics:
        if isinstance(t, dict):
            text = t.get("Text") or t.get("Result", "")
            if text and len(text) > 20:
                return text
    return None
