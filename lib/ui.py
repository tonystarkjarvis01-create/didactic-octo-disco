"""Shared UI helpers: page setup, sidebar, footer disclosure, and CSS."""
from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from lib.config import APP_NAME, APP_TAGLINE, DISCLOSURE

_CSS = """
<style>
.block-container {padding-top: 2rem; max-width: 1200px;}
[data-testid="stMetricValue"] {font-size: 1.6rem;}
.sma-footer {
    margin-top: 3rem; padding: 1rem 0; border-top: 1px solid #2a2e36;
    font-size: 0.8rem; color: #9aa0aa; line-height: 1.4;
}
.sma-badge {
    display: inline-block; padding: 2px 8px; border-radius: 6px;
    background: #1a1d24; border: 1px solid #2a2e36; font-size: 0.75rem;
    color: #9aa0aa; margin-left: 6px;
}
.pos {color: #16c784;} .neg {color: #ea3943;}
</style>
"""


def setup_page(title: str, icon: str = "📊") -> None:
    """Configure a Streamlit page with consistent title, layout, and CSS."""
    st.set_page_config(
        page_title=f"{title} · {APP_NAME}",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(_CSS, unsafe_allow_html=True)
    # Live reset on first access of each new visitor session, so everyone
    # lands on freshly-fetched data rather than a previous visitor's cache.
    if not st.session_state.get("_session_inited"):
        st.cache_data.clear()
        st.session_state["_session_inited"] = True
        st.session_state["_last_refresh"] = datetime.now(timezone.utc)


def refresh_data() -> None:
    """Clear all cached data so the next run refetches live data."""
    st.cache_data.clear()
    st.session_state["_last_refresh"] = datetime.now(timezone.utc)


def sidebar(ai_provider: str | None = None) -> None:
    """Render the shared sidebar, including the top-left Refresh Data control."""
    with st.sidebar:
        # Top-left refresh: clears caches and reruns so every page refetches.
        if st.button("🔄 Refresh Data", use_container_width=True, type="primary"):
            refresh_data()
            st.rerun()
        from lib.market_data import latest_session_date

        session_date = latest_session_date()
        if session_date:
            st.caption(f"📅 Market data as of: **{session_date}**")
            st.caption("(latest completed trading session — markets are closed weekends & holidays)")
        last = st.session_state.get("_last_refresh")
        if last is not None:
            st.caption(f"Last refreshed: {last.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        else:
            st.caption("Showing latest available data.")
        st.divider()

        st.markdown(f"### {APP_NAME}")
        st.caption(APP_TAGLINE)
        if ai_provider:
            st.markdown(f"AI provider: `{ai_provider}`")
        st.divider()
        st.caption(
            "Educational use only. No buy/sell/hold recommendations are "
            "offered anywhere in this app."
        )


def footer() -> None:
    """Render the compliance disclosure footer (required on every page)."""
    st.markdown(f"<div class='sma-footer'>{DISCLOSURE}</div>", unsafe_allow_html=True)


def colored_delta(value: float, suffix: str = "%") -> str:
    cls = "pos" if value >= 0 else "neg"
    sign = "+" if value >= 0 else ""
    return f"<span class='{cls}'>{sign}{value:.2f}{suffix}</span>"
