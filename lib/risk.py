"""Descriptive risk metrics for single tickers, ETFs, and portfolios."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

TRADING_DAYS = 252


@dataclass
class RiskMetrics:
    annual_return: float | None = None
    annual_vol: float | None = None
    sharpe: float | None = None
    max_drawdown: float | None = None
    ok: bool = False


def _daily_returns(close: pd.Series) -> pd.Series:
    return close.dropna().pct_change().dropna()


def metrics_from_history(close: pd.Series, rf: float = 0.0) -> RiskMetrics:
    """Compute annualized return/vol/Sharpe and max drawdown from a price series."""
    rets = _daily_returns(close)
    if rets.empty:
        return RiskMetrics(ok=False)
    ann_ret = float((1 + rets.mean()) ** TRADING_DAYS - 1)
    ann_vol = float(rets.std() * np.sqrt(TRADING_DAYS))
    sharpe = (ann_ret - rf) / ann_vol if ann_vol else None
    cum = (1 + rets).cumprod()
    drawdown = float((cum / cum.cummax() - 1).min())
    return RiskMetrics(
        annual_return=ann_ret,
        annual_vol=ann_vol,
        sharpe=round(sharpe, 2) if sharpe is not None else None,
        max_drawdown=drawdown,
        ok=True,
    )


def portfolio_returns(price_frame: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    """Weighted daily returns from a wide price frame (columns = tickers)."""
    rets = price_frame.pct_change().dropna()
    cols = [c for c in rets.columns if c in weights]
    if not cols:
        return pd.Series(dtype=float)
    w = np.array([weights[c] for c in cols], dtype=float)
    w = w / w.sum() if w.sum() else w
    return rets[cols].mul(w, axis=1).sum(axis=1)


def correlation_matrix(price_frame: pd.DataFrame) -> pd.DataFrame:
    return price_frame.pct_change().dropna().corr()
