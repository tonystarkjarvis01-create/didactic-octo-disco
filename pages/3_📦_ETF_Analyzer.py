"""ETF Analyzer — profile, holdings, cost-vs-peers, and risk metrics."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from lib.charts import price_chart
from lib.claude_analyst import active_provider
from lib.etf_peers import cost_comparison
from lib.market_data import PERIOD_MAP, get_etf_profile, get_history
from lib.risk import metrics_from_history
from lib.ui import footer, setup_page, sidebar

setup_page("ETF Analyzer", "📦")
sidebar(active_provider())

st.title("📦 ETF Analyzer")

c1, c2 = st.columns([2, 1])
with c1:
    symbol = st.text_input("ETF ticker", value="VOO").upper().strip()
with c2:
    period = st.selectbox("Period", list(PERIOD_MAP.keys()), index=5)

if not symbol:
    st.stop()

profile = get_etf_profile(symbol)
df = get_history(symbol, period)

st.subheader(profile.get("name", symbol) if profile else symbol)
pcols = st.columns(4)
with pcols[0]:
    st.metric("Category", profile.get("category", "—") if profile else "—")
with pcols[1]:
    er = profile.get("expense_ratio") if profile else None
    st.metric("Expense Ratio", f"{er*100:.2f}%" if isinstance(er, (int, float)) else "—")
with pcols[2]:
    ta = profile.get("total_assets") if profile else None
    st.metric("Total Assets", f"${ta/1e9:,.1f}B" if isinstance(ta, (int, float)) else "—")
with pcols[3]:
    y = profile.get("yield") if profile else None
    st.metric("Yield", f"{y*100:.2f}%" if isinstance(y, (int, float)) else "—")

st.plotly_chart(
    price_chart(df, view="area", title=f"{symbol} · {period}"),
    use_container_width=True,
)

st.divider()
st.subheader("Cost vs peers")
peers = cost_comparison(symbol)
if peers.empty:
    st.info("Peer cost data unavailable here.")
else:
    st.dataframe(peers, use_container_width=True, hide_index=True)
    st.caption(
        "Expense ratios are recurring fund costs. Lower cost is a factual "
        "attribute, not a recommendation."
    )

st.divider()
st.subheader("Holdings & sectors")
hc1, hc2 = st.columns(2)
with hc1:
    top = profile.get("top_holdings") if profile else None
    if isinstance(top, pd.DataFrame) and not top.empty:
        st.markdown("**Top holdings**")
        st.dataframe(top, use_container_width=True)
    else:
        st.caption("Top holdings unavailable here.")
with hc2:
    sectors = profile.get("sector_weights") if profile else None
    if isinstance(sectors, (pd.Series, pd.DataFrame)) and len(sectors):
        st.markdown("**Sector weights**")
        st.dataframe(sectors, use_container_width=True)
    else:
        st.caption("Sector weights unavailable here.")

st.divider()
st.subheader("Risk metrics")
if df.empty:
    st.info("Risk metrics require price history (unavailable here).")
else:
    m = metrics_from_history(df["Close"])
    rcols = st.columns(4)
    with rcols[0]:
        st.metric("Annual return", f"{m.annual_return*100:.1f}%" if m.annual_return is not None else "—")
    with rcols[1]:
        st.metric("Annual volatility", f"{m.annual_vol*100:.1f}%" if m.annual_vol is not None else "—")
    with rcols[2]:
        st.metric("Sharpe (rf=0)", f"{m.sharpe:.2f}" if m.sharpe is not None else "—")
    with rcols[3]:
        st.metric("Max drawdown", f"{m.max_drawdown*100:.1f}%" if m.max_drawdown is not None else "—")

footer()
