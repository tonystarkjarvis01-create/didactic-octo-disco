"""News — neutral headline feed for a ticker."""
from __future__ import annotations

import streamlit as st

from lib.claude_analyst import active_provider
from lib.news import get_news
from lib.ui import footer, setup_page, sidebar

setup_page("News", "📰")
sidebar(active_provider())

st.title("📰 News")
st.caption("Recent headlines. Links go to original publishers; no commentary added.")

symbol = st.text_input("Ticker", value="AAPL").upper().strip()
if not symbol:
    st.stop()

items = get_news(symbol)
if not items:
    st.info(
        "No headlines available (the news source may be blocked in this "
        "environment). Run locally with internet access."
    )
else:
    for it in items:
        st.markdown(f"#### [{it['title']}]({it['link']})")
        meta = " · ".join(x for x in [it.get("publisher"), it.get("when")] if x)
        if meta:
            st.caption(meta)
        st.divider()

footer()
