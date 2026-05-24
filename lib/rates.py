"""FRED API access (optional). Returns empty results when no key/network."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from lib.config import fred_key

# Curated FRED series for the macro page.
SERIES: dict[str, str] = {
    "FEDFUNDS": "Federal Funds Rate",
    "DGS10": "10-Year Treasury Yield",
    "DGS2": "2-Year Treasury Yield",
    "T10Y2Y": "10Y-2Y Spread",
    "CPIAUCSL": "CPI (All Urban)",
    "UNRATE": "Unemployment Rate",
    "GDPC1": "Real GDP",
    "UMCSENT": "Consumer Sentiment",
}


@dataclass
class FredResult:
    series_id: str
    label: str
    data: pd.Series | None = None
    ok: bool = False
    error: str = ""


def _fred():
    key = fred_key()
    if not key:
        return None, "No FRED_API_KEY set (Macro page only — optional)."
    try:
        from fredapi import Fred

        return Fred(api_key=key), ""
    except Exception as e:
        return None, f"fredapi unavailable: {e}"


@st.cache_data(ttl=3600, show_spinner=False)
def get_series(series_id: str, label: str = "") -> FredResult:
    client, err = _fred()
    if client is None:
        return FredResult(series_id, label or series_id, ok=False, error=err)
    try:
        s = client.get_series(series_id)
        return FredResult(series_id, label or series_id, data=s, ok=True)
    except Exception as e:
        return FredResult(series_id, label or series_id, ok=False, error=str(e)[:120])


def has_key() -> bool:
    return fred_key() is not None
