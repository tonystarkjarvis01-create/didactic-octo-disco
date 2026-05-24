"""ETF cost/peer comparison helpers (descriptive only)."""
from __future__ import annotations

import pandas as pd

from lib.market_data import get_etf_profile

# Small curated peer groups by broad exposure.
PEER_GROUPS: dict[str, list[str]] = {
    "US Total Market": ["VTI", "ITOT", "SCHB"],
    "S&P 500": ["VOO", "IVV", "SPY", "SPLG"],
    "Nasdaq 100": ["QQQ", "QQQM"],
    "Developed ex-US": ["VEA", "IEFA", "SCHF"],
    "Emerging Markets": ["VWO", "IEMG", "SCHE"],
    "US Aggregate Bond": ["BND", "AGG", "SCHZ"],
}


def find_peers(symbol: str) -> list[str]:
    sym = symbol.upper()
    for peers in PEER_GROUPS.values():
        if sym in peers:
            return peers
    return [sym]


def cost_comparison(symbol: str) -> pd.DataFrame:
    """Compare expense ratios across an ETF's peer group."""
    rows = []
    for peer in find_peers(symbol):
        prof = get_etf_profile(peer)
        er = prof.get("expense_ratio")
        rows.append(
            {
                "Symbol": peer,
                "Name": prof.get("name", peer),
                "Expense Ratio": f"{er*100:.2f}%" if isinstance(er, (int, float)) else "—",
                "_er_num": er if isinstance(er, (int, float)) else None,
            }
        )
    df = pd.DataFrame(rows)
    if "_er_num" in df and df["_er_num"].notna().any():
        df = df.sort_values("_er_num", na_position="last")
    return df.drop(columns=["_er_num"], errors="ignore").reset_index(drop=True)


def annual_cost_on(amount: float, expense_ratio: float | None) -> float | None:
    """Dollar cost per year on a given amount for a fund's expense ratio."""
    if expense_ratio is None:
        return None
    return amount * expense_ratio
