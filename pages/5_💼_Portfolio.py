"""Portfolio — a personal watch list with descriptive risk metrics."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from lib.claude_analyst import active_provider
from lib.market_data import get_history, get_quote
from lib.portfolio import add, load, remove
from lib.risk import correlation_matrix, metrics_from_history, portfolio_returns
from lib.ui import footer, setup_page, sidebar

setup_page("Portfolio", "💼")
sidebar(active_provider())

st.title("💼 Portfolio")
st.caption(
    "Track positions you're researching. This is a tracking tool only — it "
    "offers no targets, suggestions, or recommendations."
)

positions = load()

with st.form("add_position", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        sym = st.text_input("Ticker")
    with c2:
        shares = st.number_input("Shares", min_value=0.0, step=1.0)
    with c3:
        cost = st.number_input("Cost / share", min_value=0.0, step=1.0)
    with c4:
        st.write("")
        submitted = st.form_submit_button("Add / update")
    if submitted and sym and shares > 0:
        positions = add(positions, sym, shares, cost)
        st.rerun()

if not positions:
    st.info("No positions yet. Add one above.")
    footer()
    st.stop()

rows = []
prices = {}
for p in positions:
    q = get_quote(p.symbol)
    price = q.price if q.ok else None
    if price is not None:
        prices[p.symbol] = price
    value = price * p.shares if price is not None else None
    basis = p.cost_basis * p.shares
    pnl = (value - basis) if value is not None else None
    rows.append(
        {
            "Symbol": p.symbol,
            "Shares": p.shares,
            "Cost/sh": p.cost_basis,
            "Price": price,
            "Value": value,
            "Unrealized P/L": pnl,
            "P/L %": (pnl / basis * 100) if (pnl is not None and basis) else None,
        }
    )

df = pd.DataFrame(rows)
st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Cost/sh": st.column_config.NumberColumn(format="%.2f"),
        "Price": st.column_config.NumberColumn(format="%.2f"),
        "Value": st.column_config.NumberColumn(format="%.2f"),
        "Unrealized P/L": st.column_config.NumberColumn(format="%.2f"),
        "P/L %": st.column_config.NumberColumn(format="%.2f%%"),
    },
)

total_value = df["Value"].dropna().sum()
total_cost = (df["Shares"] * df["Cost/sh"]).sum()
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Total value", f"${total_value:,.2f}" if total_value else "—")
with m2:
    st.metric("Total cost", f"${total_cost:,.2f}")
with m3:
    if total_value:
        st.metric("Unrealized P/L", f"${total_value-total_cost:,.2f}",
                  f"{(total_value-total_cost)/total_cost*100:+.2f}%" if total_cost else "")

rem = st.selectbox("Remove position", ["—"] + [p.symbol for p in positions])
if st.button("Remove") and rem != "—":
    positions = remove(positions, rem)
    st.rerun()

st.divider()
st.subheader("Portfolio risk")
hist_frame = {}
for p in positions:
    h = get_history(p.symbol, "1Y")
    if not h.empty:
        hist_frame[p.symbol] = h["Close"]

if len(hist_frame) >= 1:
    wide = pd.DataFrame(hist_frame).dropna()
    weights = {p.symbol: (prices.get(p.symbol, p.cost_basis) * p.shares) for p in positions}
    pr = portfolio_returns(wide, weights)
    if not pr.empty:
        equity = (1 + pr).cumprod()
        pm = metrics_from_history(equity)
        rc = st.columns(4)
        with rc[0]:
            st.metric("Annual return", f"{pm.annual_return*100:.1f}%" if pm.annual_return is not None else "—")
        with rc[1]:
            st.metric("Annual volatility", f"{pm.annual_vol*100:.1f}%" if pm.annual_vol is not None else "—")
        with rc[2]:
            st.metric("Sharpe (rf=0)", f"{pm.sharpe:.2f}" if pm.sharpe is not None else "—")
        with rc[3]:
            st.metric("Max drawdown", f"{pm.max_drawdown*100:.1f}%" if pm.max_drawdown is not None else "—")
    if wide.shape[1] >= 2:
        st.markdown("**Correlation matrix**")
        st.dataframe(correlation_matrix(wide).round(2), use_container_width=True)
else:
    st.info("Risk metrics require price history (unavailable here).")

footer()
