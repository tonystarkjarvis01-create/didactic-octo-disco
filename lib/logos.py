"""Company logo loading.

Maps tickers to brand domains and loads bundled PNGs as base64 data URLs for
inline embedding. Falls back to ticker initials when a logo is missing.
"""
from __future__ import annotations

import base64
from pathlib import Path

LOGO_DIR = Path(__file__).resolve().parent.parent / "assets" / "logos"

# Ticker -> brand domain (used by scripts/fetch_logos.py and Clearbit-style sources).
TICKER_DOMAINS: dict[str, str] = {
    "AAPL": "apple.com", "MSFT": "microsoft.com", "GOOGL": "google.com",
    "GOOG": "google.com", "AMZN": "amazon.com", "META": "meta.com",
    "NVDA": "nvidia.com", "TSLA": "tesla.com", "NFLX": "netflix.com",
    "AMD": "amd.com", "INTC": "intel.com", "ORCL": "oracle.com",
    "CRM": "salesforce.com", "ADBE": "adobe.com", "CSCO": "cisco.com",
    "IBM": "ibm.com", "QCOM": "qualcomm.com", "TXN": "ti.com",
    "JPM": "jpmorganchase.com", "BAC": "bankofamerica.com", "WFC": "wellsfargo.com",
    "GS": "goldmansachs.com", "MS": "morganstanley.com", "V": "visa.com",
    "MA": "mastercard.com", "PYPL": "paypal.com", "AXP": "americanexpress.com",
    "JNJ": "jnj.com", "PFE": "pfizer.com", "MRK": "merck.com",
    "ABBV": "abbvie.com", "UNH": "unitedhealthgroup.com", "LLY": "lilly.com",
    "KO": "coca-cola.com", "PEP": "pepsico.com", "PG": "pg.com",
    "WMT": "walmart.com", "COST": "costco.com", "MCD": "mcdonalds.com",
    "NKE": "nike.com", "SBUX": "starbucks.com", "DIS": "disney.com",
    "XOM": "exxonmobil.com", "CVX": "chevron.com", "BA": "boeing.com",
    "CAT": "caterpillar.com", "GE": "ge.com", "F": "ford.com",
    "GM": "gm.com", "T": "att.com", "VZ": "verizon.com",
}


def _data_url(path: Path) -> str | None:
    try:
        raw = path.read_bytes()
        b64 = base64.b64encode(raw).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except Exception:
        return None


def logo_data_url(ticker: str) -> str | None:
    """Return a base64 data URL for the ticker's bundled logo, or None."""
    p = LOGO_DIR / f"{ticker.upper()}.png"
    if p.exists():
        return _data_url(p)
    return None


def initials_badge(ticker: str) -> str:
    """HTML fallback badge showing ticker initials when no logo exists."""
    letters = ticker.upper()[:4]
    return (
        f"<div style='width:40px;height:40px;border-radius:8px;background:#1a1d24;"
        f"border:1px solid #2a2e36;display:flex;align-items:center;justify-content:"
        f"center;font-weight:600;color:#9aa0aa;font-size:0.7rem'>{letters}</div>"
    )


def logo_html(ticker: str, size: int = 40) -> str:
    """Return an <img> tag for the logo, or an initials badge fallback."""
    url = logo_data_url(ticker)
    if url:
        return (
            f"<img src='{url}' width='{size}' height='{size}' "
            f"style='border-radius:8px;object-fit:contain;background:#fff;padding:2px'/>"
        )
    return initials_badge(ticker)
