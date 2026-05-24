"""Neutral technical & fundamental scoring.

These produce *descriptive* 0-100 composite scores and an "At a glance"
summary. They are explicitly NOT buy/sell/hold signals — wording is kept
factual and the disclosure footer reinforces this on every page.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class ScoreCard:
    score: float  # 0-100, neutral composite
    label: str  # neutral band label
    factors: list[tuple[str, str]] = field(default_factory=list)  # (name, note)


def _band(score: float) -> str:
    """Neutral descriptive bands — deliberately not action words."""
    if score >= 75:
        return "Strong readings"
    if score >= 55:
        return "Firm readings"
    if score >= 45:
        return "Mixed readings"
    if score >= 25:
        return "Soft readings"
    return "Weak readings"


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def technical_score(df: pd.DataFrame) -> ScoreCard:
    """Composite of trend (vs 50/200 SMA), momentum (RSI), and recent return."""
    if df is None or df.empty or "Close" not in df or len(df) < 20:
        return ScoreCard(50.0, "Insufficient data", [("data", "Not enough history")])

    close = df["Close"].dropna()
    factors: list[tuple[str, str]] = []
    points: list[float] = []

    sma50 = close.rolling(min(50, len(close))).mean().iloc[-1]
    sma200 = close.rolling(min(200, len(close))).mean().iloc[-1]
    last = close.iloc[-1]

    if not np.isnan(sma50):
        above = last >= sma50
        points.append(65 if above else 35)
        factors.append(("Price vs 50-period avg", "above" if above else "below"))
    if not np.isnan(sma200):
        above = last >= sma200
        points.append(70 if above else 30)
        factors.append(("Price vs 200-period avg", "above" if above else "below"))

    r = rsi(close).iloc[-1]
    if not np.isnan(r):
        # Map RSI to a centered contribution; extremes noted factually.
        pts = float(np.clip(r, 0, 100))
        points.append(pts)
        note = "elevated" if r > 70 else ("subdued" if r < 30 else "neutral")
        factors.append((f"RSI(14) = {r:.0f}", note))

    ret = (last / close.iloc[max(0, len(close) - 20)] - 1) * 100
    points.append(float(np.clip(50 + ret, 0, 100)))
    factors.append(("~20-period return", f"{ret:+.1f}%"))

    score = float(np.mean(points)) if points else 50.0
    return ScoreCard(round(score, 1), _band(score), factors)


def fundamental_score(info: dict) -> ScoreCard:
    """Composite from valuation, profitability, and growth fields (when present)."""
    if not info:
        return ScoreCard(50.0, "Insufficient data", [("data", "No fundamentals")])

    factors: list[tuple[str, str]] = []
    points: list[float] = []

    pe = info.get("trailingPE")
    if isinstance(pe, (int, float)) and pe > 0:
        pts = float(np.clip(100 - (pe - 15) * 2, 0, 100))
        points.append(pts)
        factors.append((f"Trailing P/E = {pe:.1f}", "context only"))

    margin = info.get("profitMargins")
    if isinstance(margin, (int, float)):
        pts = float(np.clip(50 + margin * 200, 0, 100))
        points.append(pts)
        factors.append((f"Profit margin = {margin*100:.1f}%", ""))

    growth = info.get("revenueGrowth")
    if isinstance(growth, (int, float)):
        pts = float(np.clip(50 + growth * 200, 0, 100))
        points.append(pts)
        factors.append((f"Revenue growth = {growth*100:.1f}%", ""))

    roe = info.get("returnOnEquity")
    if isinstance(roe, (int, float)):
        pts = float(np.clip(50 + roe * 150, 0, 100))
        points.append(pts)
        factors.append((f"Return on equity = {roe*100:.1f}%", ""))

    score = float(np.mean(points)) if points else 50.0
    return ScoreCard(round(score, 1), _band(score), factors)


def at_a_glance(tech: ScoreCard, fund: ScoreCard) -> str:
    """Neutral one-paragraph summary. Factual, no recommendation."""
    return (
        f"Technical readings are **{tech.label.lower()}** "
        f"(composite {tech.score:.0f}/100) and fundamental readings are "
        f"**{fund.label.lower()}** (composite {fund.score:.0f}/100). "
        "These composites summarize publicly available metrics for research "
        "context only and are not a recommendation to take any action."
    )
