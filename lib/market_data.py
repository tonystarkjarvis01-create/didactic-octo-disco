"""Market data access via yfinance, with graceful offline degradation.

Every public function returns either real data or a clearly-flagged empty
result; none of them raise on network failure, so pages stay usable offline.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
import streamlit as st

try:
    import yfinance as yf
except Exception:  # pragma: no cover - dependency missing
    yf = None

# Real index/commodity/crypto tickers (not ETF proxies).
INDEX_TICKERS: dict[str, str] = {
    "^GSPC": "S&P 500",
    "^NDX": "Nasdaq 100",
    "^DJI": "Dow Jones",
    "^RUT": "Russell 2000",
    "^VIX": "VIX (Volatility)",
    "^TNX": "10Y Treasury Yield",
    "GC=F": "Gold",
    "CL=F": "Crude Oil (WTI)",
    "BTC-USD": "Bitcoin",
    "DX-Y.NYB": "US Dollar Index",
}

# S&P sector SPDR ETFs.
SECTOR_ETFS: dict[str, str] = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLV": "Health Care",
    "XLE": "Energy",
    "XLY": "Consumer Discretionary",
    "XLP": "Consumer Staples",
    "XLI": "Industrials",
    "XLB": "Materials",
    "XLU": "Utilities",
    "XLRE": "Real Estate",
    "XLC": "Communication Services",
}

# Streamlit period selector -> (yf period, yf interval).
PERIOD_MAP: dict[str, tuple[str, str]] = {
    "1D": ("1d", "5m"),
    "5D": ("5d", "15m"),
    "1M": ("1mo", "1d"),
    "6M": ("6mo", "1d"),
    "YTD": ("ytd", "1d"),
    "1Y": ("1y", "1d"),
    "5Y": ("5y", "1wk"),
    "MAX": ("max", "1mo"),
}


@dataclass
class Quote:
    symbol: str
    name: str = ""
    price: float | None = None
    prev_close: float | None = None
    currency: str = "USD"
    ok: bool = False
    error: str = ""

    @property
    def change(self) -> float | None:
        if self.price is None or self.prev_close in (None, 0):
            return None
        return self.price - self.prev_close

    @property
    def change_pct(self) -> float | None:
        if self.change is None or not self.prev_close:
            return None
        return self.change / self.prev_close * 100.0


def _offline(symbol: str, msg: str = "Live data unavailable") -> Quote:
    return Quote(symbol=symbol, ok=False, error=msg)


@st.cache_data(ttl=45, show_spinner=False)
def get_quote(symbol: str, name: str = "") -> Quote:
    """Fetch a single quote. Never raises."""
    if yf is None:
        return _offline(symbol, "yfinance not installed")
    try:
        t = yf.Ticker(symbol)
        fi = getattr(t, "fast_info", {}) or {}
        price = fi.get("last_price") or fi.get("lastPrice")
        prev = fi.get("previous_close") or fi.get("previousClose")
        if price is None:
            hist = t.history(period="2d")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
                prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price
        if price is None:
            return _offline(symbol, "No price returned")
        return Quote(
            symbol=symbol,
            name=name or symbol,
            price=float(price),
            prev_close=float(prev) if prev else float(price),
            currency=fi.get("currency", "USD") or "USD",
            ok=True,
        )
    except Exception as e:  # network blocked / bad symbol
        return _offline(symbol, str(e)[:120])


def get_quotes(symbols: dict[str, str]) -> list[Quote]:
    """Fetch many quotes (symbol -> display name)."""
    return [get_quote(sym, name) for sym, name in symbols.items()]


@st.cache_data(ttl=120, show_spinner=False)
def get_history(symbol: str, period_label: str = "1Y") -> pd.DataFrame:
    """Return OHLCV history for a period label. Empty frame on failure."""
    if yf is None:
        return pd.DataFrame()
    period, interval = PERIOD_MAP.get(period_label, ("1y", "1d"))
    try:
        df = yf.Ticker(symbol).history(period=period, interval=interval)
        return df if df is not None else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=600, show_spinner=False)
def get_prev_close(symbol: str) -> float | None:
    """Yesterday's close — used to baseline 1D charts across overnight gaps."""
    if yf is None:
        return None
    try:
        hist = yf.Ticker(symbol).history(period="5d", interval="1d")
        if len(hist) >= 2:
            return float(hist["Close"].iloc[-2])
        if len(hist) == 1:
            return float(hist["Close"].iloc[-1])
    except Exception:
        return None
    return None


@dataclass
class Fundamentals:
    symbol: str
    info: dict = field(default_factory=dict)
    ok: bool = False
    error: str = ""

    def get(self, key: str, default=None):
        return self.info.get(key, default)


@st.cache_data(ttl=600, show_spinner=False)
def get_fundamentals(symbol: str) -> Fundamentals:
    if yf is None:
        return Fundamentals(symbol, ok=False, error="yfinance not installed")
    try:
        info = yf.Ticker(symbol).info or {}
        if not info:
            return Fundamentals(symbol, ok=False, error="No fundamentals returned")
        return Fundamentals(symbol, info=info, ok=True)
    except Exception as e:
        return Fundamentals(symbol, ok=False, error=str(e)[:120])


@st.cache_data(ttl=600, show_spinner=False)
def get_etf_profile(symbol: str) -> dict:
    """ETF metadata: holdings, expense ratio, category. Empty dict on failure."""
    if yf is None:
        return {}
    try:
        t = yf.Ticker(symbol)
        info = t.info or {}
        out = {
            "name": info.get("longName") or info.get("shortName") or symbol,
            "category": info.get("category", "—"),
            "expense_ratio": info.get("annualReportExpenseRatio")
            or info.get("netExpenseRatio"),
            "total_assets": info.get("totalAssets"),
            "yield": info.get("yield"),
        }
        try:
            funds = t.funds_data
            out["top_holdings"] = funds.top_holdings
            out["sector_weights"] = funds.sector_weightings
        except Exception:
            pass
        return out
    except Exception:
        return {}


@st.cache_data(ttl=120, show_spinner=False)
def get_movers(symbols: list[str]) -> pd.DataFrame:
    """Build a sorted gainers/losers table from a symbol list."""
    rows = []
    for sym in symbols:
        q = get_quote(sym)
        if q.ok and q.change_pct is not None:
            rows.append({"Symbol": sym, "Price": q.price, "Change %": q.change_pct})
    if not rows:
        return pd.DataFrame(columns=["Symbol", "Price", "Change %"])
    return pd.DataFrame(rows).sort_values("Change %", ascending=False).reset_index(drop=True)
