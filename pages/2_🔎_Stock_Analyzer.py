"""Stock Analyzer — price chart, fundamentals, neutral scores, AI notes."""
from __future__ import annotations

import streamlit as st

from lib.charts import gauge, price_chart
from lib.claude_analyst import active_provider, analyze
from lib.logos import logo_html
from lib.market_data import (
    PERIOD_MAP,
    get_fundamentals,
    get_history,
    get_prev_close,
    get_quote,
)
from lib.signals import at_a_glance, fundamental_score, technical_score
from lib.ui import footer, setup_page, sidebar

setup_page("Stock Analyzer", "🔎")
sidebar(active_provider())

st.title("🔎 Stock Analyzer")

c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    symbol = st.text_input("Ticker", value="AAPL").upper().strip()
with c2:
    period = st.selectbox("Period", list(PERIOD_MAP.keys()), index=5)
with c3:
    view = st.selectbox("View", ["line", "area", "candlestick", "ohlc"])

if not symbol:
    st.stop()

quote = get_quote(symbol)
hcol, mcol = st.columns([1, 5])
with hcol:
    st.markdown(logo_html(symbol, 56), unsafe_allow_html=True)
with mcol:
    if quote.ok:
        st.metric(
            symbol,
            f"{quote.price:,.2f} {quote.currency}",
            f"{quote.change_pct:+.2f}%" if quote.change_pct is not None else "",
        )
    else:
        st.metric(symbol, "—", "")
        st.caption("Live quote unavailable here — run locally with internet access.")

# 1D charts baseline on yesterday's close so overnight gaps read correctly.
df = get_history(symbol, period)
baseline = get_prev_close(symbol) if period == "1D" and view == "line" else None
st.plotly_chart(
    price_chart(df, view=view, title=f"{symbol} · {period}", baseline_price=baseline),
    use_container_width=True,
)

st.divider()
fund = get_fundamentals(symbol)
tech_card = technical_score(df)
fund_card = fundamental_score(fund.info if fund.ok else {})

g1, g2, g3 = st.columns(3)
with g1:
    st.plotly_chart(gauge(tech_card.score, "Technical composite"), use_container_width=True)
with g2:
    st.plotly_chart(gauge(fund_card.score, "Fundamental composite"), use_container_width=True)
with g3:
    st.markdown("**At a glance**")
    st.markdown(at_a_glance(tech_card, fund_card))

if fund.ok:
    st.subheader("Key fundamentals")
    info = fund.info
    fcols = st.columns(4)
    fields = [
        ("Market Cap", info.get("marketCap")),
        ("Trailing P/E", info.get("trailingPE")),
        ("EPS (ttm)", info.get("trailingEps")),
        ("Dividend Yield", info.get("dividendYield")),
        ("52W High", info.get("fiftyTwoWeekHigh")),
        ("52W Low", info.get("fiftyTwoWeekLow")),
        ("Beta", info.get("beta")),
        ("Profit Margin", info.get("profitMargins")),
    ]
    for i, (label, val) in enumerate(fields):
        with fcols[i % 4]:
            if isinstance(val, (int, float)):
                if label == "Market Cap":
                    disp = f"${val/1e9:,.1f}B"
                elif "Yield" in label or "Margin" in label:
                    disp = f"{val*100:.2f}%"
                else:
                    disp = f"{val:,.2f}"
            else:
                disp = "—"
            st.metric(label, disp)

st.divider()
st.subheader("🤖 Claude research summary")

info = fund.info if fund.ok else {}
ctx = {
    "symbol": symbol,
    "name": info.get("longName", symbol),
    "price": quote.price if quote.ok else None,
    "change_pct": quote.change_pct if quote.ok else None,
    "technical": {
        "score": tech_card.score,
        "label": tech_card.label,
        "factors": tech_card.factors,
    },
    "fundamental": {
        "score": fund_card.score,
        "label": fund_card.label,
        "factors": fund_card.factors,
    },
    "extra": {
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "marketCap": info.get("marketCap"),
        "trailingPE": info.get("trailingPE"),
        "forwardPE": info.get("forwardPE"),
        "profitMargins": info.get("profitMargins"),
        "revenueGrowth": info.get("revenueGrowth"),
        "returnOnEquity": info.get("returnOnEquity"),
        "dividendYield": info.get("dividendYield"),
        "beta": info.get("beta"),
        "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
        "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
        "businessSummary": (info.get("longBusinessSummary") or "")[:800],
    },
}


@st.cache_data(ttl=1800, show_spinner=False)
def _summary(sym: str, signature: str):
    # sym + signature form the cache key; signature changes when key metrics
    # change, so the summary regenerates when the underlying data moves.
    return analyze(ctx)


sig = f"{ctx['price']}|{tech_card.score}|{fund_card.score}"
with st.spinner("Generating summary with Claude Sonnet 4.6…"):
    text, provider = _summary(symbol, sig)
st.caption(f"Provider: {provider}")
st.markdown(text)
if st.button("↻ Regenerate summary"):
    _summary.clear()
    st.rerun()

footer()
