"""Macro helpers built on top of FRED series (neutral framing only)."""
from __future__ import annotations

import pandas as pd

from lib.rates import SERIES, get_series


def latest_value(series_id: str) -> tuple[float | None, str]:
    """Return (latest value, label). Value is None if unavailable."""
    label = SERIES.get(series_id, series_id)
    res = get_series(series_id, label)
    if not res.ok or res.data is None or res.data.empty:
        return None, label
    s = res.data.dropna()
    if s.empty:
        return None, label
    return float(s.iloc[-1]), label


def yield_curve() -> pd.DataFrame:
    """Assemble a small yield-curve snapshot from available FRED series."""
    rows = []
    for sid in ("DGS2", "DGS10"):
        val, label = latest_value(sid)
        if val is not None:
            rows.append({"Series": label, "Value": val})
    return pd.DataFrame(rows)


def describe_curve(spread: float | None) -> str:
    """Neutral, factual description of the 10Y-2Y spread. No advice."""
    if spread is None:
        return "10Y-2Y spread data is unavailable."
    if spread < 0:
        return (
            f"The 10Y-2Y spread is {spread:.2f} (inverted — the 2-year yield "
            "exceeds the 10-year). Historically this configuration has drawn "
            "attention as a macro indicator; this is context, not a forecast."
        )
    return (
        f"The 10Y-2Y spread is {spread:.2f} (positive — longer-dated yields "
        "exceed shorter-dated). Presented for context only."
    )
