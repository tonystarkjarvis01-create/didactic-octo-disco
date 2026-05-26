"""Stock Market Analyst — landing page with a market snapshot."""
from __future__ import annotations

import streamlit as st

from lib.charts import sparkline
from lib.claude_analyst import active_provider
from lib.config import APP_NAME, APP_TAGLINE
from lib.market_data import INDEX_TICKERS, get_history, get_quote
from lib.ui import colored_delta, explain, footer, page_intro, setup_page, sidebar

setup_page("Home", "📊")
sidebar(active_provider())

st.title(f"📊 {APP_NAME}")
st.caption(APP_TAGLINE)
st.write(
    "A keyless, offline-friendly dashboard for exploring markets. Use the pages "
    "in the sidebar: **Market Pulse**, **Stock Analyzer**, **ETF Analyzer**, "
    "**Macro**, **Portfolio**, and **News**."
)

page_intro(
    "This is your market dashboard. Each tile below is a major market benchmark; "
    "the number is its latest level and the coloured value is how much it moved on "
    "the last session. Green = up, red = down. Use it to gauge the overall 'weather' "
    "of markets before you dig into individual stocks. (Toggle **Learning mode** off "
    "in the sidebar to hide these explainers.)"
)

st.subheader("Market snapshot")
explain(
    "How to read these benchmarks",
    "- **S&P 500 / Nasdaq 100 / Dow / Russell 2000** — US stock indices. "
    "Russell 2000 = small companies; Nasdaq 100 = big tech-heavy names. Together "
    "they show how broad the market's move is.\n"
    "- **VIX** — the 'fear gauge'. It *rises* when investors expect bigger swings, "
    "so a jumping VIX usually means stocks are falling.\n"
    "- **10Y Treasury yield** — the interest rate on US government debt. Rising "
    "yields make borrowing pricier and often pressure growth stocks.\n"
    "- **Gold** — often bid up when investors want safety. **Crude oil** — tied to "
    "the economy and inflation. **Bitcoin** — a risk-sensitive crypto benchmark.\n"
    "- **US Dollar Index (DXY)** — the dollar vs. other major currencies; a strong "
    "dollar can weigh on US exporters and commodities.",
)
quotes = [get_quote(sym, name) for sym, name in INDEX_TICKERS.items()]

if not any(q.ok for q in quotes):
    st.info(
        "Live market data is unavailable in this environment (the network "
        "allowlist may block Yahoo Finance). Run the app on a machine with "
        "internet access to populate quotes."
    )

cols = st.columns(5)
for i, q in enumerate(quotes):
    with cols[i % 5]:
        if q.ok:
            delta = q.change_pct if q.change_pct is not None else 0.0
            st.metric(q.name, f"{q.price:,.2f}", f"{delta:+.2f}%")
            hist = get_history(q.symbol, "1M")
            if not hist.empty:
                st.plotly_chart(
                    sparkline(hist["Close"]),
                    use_container_width=True,
                    config={"displayModeBar": False},
                    key=f"spark_{q.symbol}",
                )
        else:
            st.metric(q.name, "—", "")

footer()
