"""Macro — FRED-backed rates, inflation, and labor context (optional key)."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from lib.charts import GRID
from lib.claude_analyst import active_provider
from lib.macro import describe_curve, latest_value
from lib.rates import SERIES, get_series, has_key
from lib.ui import footer, setup_page, sidebar

setup_page("Macro", "🏛️")
sidebar(active_provider())

st.title("🏛️ Macro")
st.caption("Macroeconomic context from FRED. Presented neutrally, for research only.")

if not has_key():
    st.info(
        "No `FRED_API_KEY` is set, so live macro series can't be fetched. This is "
        "the only page that needs a key — get a free one at "
        "https://fred.stlouisfed.org and add it to your `.env`."
    )

st.subheader("Latest readings")
cols = st.columns(4)
for i, sid in enumerate(SERIES):
    val, label = latest_value(sid)
    with cols[i % 4]:
        st.metric(label, f"{val:,.2f}" if val is not None else "—")

st.divider()
st.subheader("Yield-curve context")
ten, _ = latest_value("DGS10")
two, _ = latest_value("DGS2")
spread = (ten - two) if (ten is not None and two is not None) else None
st.markdown(describe_curve(spread))

st.divider()
st.subheader("Series explorer")
choice = st.selectbox("FRED series", list(SERIES.keys()), format_func=lambda s: f"{SERIES[s]} ({s})")
res = get_series(choice, SERIES[choice])
if res.ok and res.data is not None and not res.data.empty:
    s = res.data.dropna().tail(600)
    fig = go.Figure(go.Scatter(x=s.index, y=s.values, mode="lines", line=dict(color="#4c8bf5")))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
        height=400, margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(gridcolor=GRID), yaxis=dict(gridcolor=GRID),
        title=res.label,
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info(res.error or "Series unavailable.")

footer()
