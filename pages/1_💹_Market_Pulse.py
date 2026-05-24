"""Market Pulse — indices, sector performance, and movers."""
from __future__ import annotations

import streamlit as st

from lib.claude_analyst import active_provider
from lib.market_data import (
    INDEX_TICKERS,
    SECTOR_ETFS,
    get_movers,
    get_quote,
)
from lib.ui import footer, setup_page, sidebar

setup_page("Market Pulse", "💹")
sidebar(active_provider())

st.title("💹 Market Pulse")
st.caption("Index levels, sector performance, and session movers — context only.")

st.subheader("Indices, commodities & crypto")
quotes = [get_quote(sym, name) for sym, name in INDEX_TICKERS.items()]
if not any(q.ok for q in quotes):
    st.info("Live data unavailable here — run locally with internet access.")
cols = st.columns(5)
for i, q in enumerate(quotes):
    with cols[i % 5]:
        st.metric(
            q.name,
            f"{q.price:,.2f}" if q.ok else "—",
            f"{q.change_pct:+.2f}%" if (q.ok and q.change_pct is not None) else "",
        )

st.divider()
st.subheader("Sector performance (SPDR ETFs)")
sectors = get_movers(list(SECTOR_ETFS.keys()))
if sectors.empty:
    st.info("Sector data unavailable here.")
else:
    sectors = sectors.copy()
    sectors["Sector"] = sectors["Symbol"].map(SECTOR_ETFS)
    st.dataframe(
        sectors[["Sector", "Symbol", "Price", "Change %"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Price": st.column_config.NumberColumn(format="%.2f"),
            "Change %": st.column_config.NumberColumn(format="%.2f%%"),
        },
    )

st.divider()
st.subheader("Movers")
watch = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "JPM", "XOM", "JNJ"]
movers = get_movers(watch)
if movers.empty:
    st.info("Mover data unavailable here.")
else:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Top gainers**")
        st.dataframe(movers.head(5), use_container_width=True, hide_index=True)
    with c2:
        st.markdown("**Top decliners**")
        st.dataframe(
            movers.tail(5).iloc[::-1], use_container_width=True, hide_index=True
        )

footer()
