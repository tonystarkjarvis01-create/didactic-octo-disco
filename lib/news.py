"""Headlines via yfinance ``Ticker.news``. Neutral presentation, no opinions."""
from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

try:
    import yfinance as yf
except Exception:  # pragma: no cover
    yf = None


@st.cache_data(ttl=600, show_spinner=False)
def get_news(symbol: str, limit: int = 15) -> list[dict]:
    """Return a list of normalized headline dicts. Empty list on failure."""
    if yf is None:
        return []
    try:
        raw = yf.Ticker(symbol).news or []
    except Exception:
        return []

    items: list[dict] = []
    for n in raw[:limit]:
        # yfinance has used both flat and nested ("content") shapes over time.
        content = n.get("content", n)
        title = content.get("title") or n.get("title")
        if not title:
            continue
        link = (
            (content.get("canonicalUrl") or {}).get("url")
            or content.get("clickThroughUrl", {}).get("url")
            or n.get("link")
            or "#"
        )
        publisher = (
            (content.get("provider") or {}).get("displayName")
            or n.get("publisher")
            or "—"
        )
        ts = n.get("providerPublishTime") or content.get("pubDate")
        when = _format_time(ts)
        items.append({"title": title, "link": link, "publisher": publisher, "when": when})
    return items


def _format_time(ts) -> str:
    if ts is None:
        return ""
    try:
        if isinstance(ts, (int, float)):
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        else:
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return str(ts)
