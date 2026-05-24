"""Plotly chart builders.

Supports four views (line / area / candlestick / OHLC). For intraday (1D)
charts a ``baseline_price`` (yesterday's close) splits the line into green
(above baseline) and red (below baseline) segments so overnight gaps read
correctly.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

GREEN = "#16c784"
RED = "#ea3943"
BLUE = "#4c8bf5"
GRID = "#23262d"

_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117",
    margin=dict(l=10, r=10, t=30, b=10),
    height=420,
    xaxis=dict(gridcolor=GRID, showspikes=True, spikemode="across"),
    yaxis=dict(gridcolor=GRID),
    hovermode="x unified",
)


def _empty(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(**_LAYOUT)
    fig.add_annotation(
        text=msg, showarrow=False, font=dict(color="#9aa0aa", size=14)
    )
    return fig


def _split_by_baseline(x, y, baseline: float) -> list[go.Scatter]:
    """Return scatter traces colored green above / red below ``baseline``.

    Inserts interpolated crossing points so each colored segment terminates
    exactly on the baseline rather than over/undershooting it.
    """
    x = list(x)
    y = list(y)
    segs_x: list = []
    segs_y: list = []
    colors: list = []
    cur_x = [x[0]]
    cur_y = [y[0]]
    cur_above = y[0] >= baseline

    for i in range(1, len(y)):
        above = y[i] >= baseline
        if above != cur_above:
            # interpolate crossing on x where y == baseline
            y0, y1 = y[i - 1], y[i]
            frac = (baseline - y0) / (y1 - y0) if y1 != y0 else 0.0
            try:
                cross_x = x[i - 1] + (x[i] - x[i - 1]) * frac
            except Exception:
                cross_x = x[i]
            cur_x.append(cross_x)
            cur_y.append(baseline)
            segs_x.append(cur_x)
            segs_y.append(cur_y)
            colors.append(GREEN if cur_above else RED)
            cur_x = [cross_x, x[i]]
            cur_y = [baseline, y[i]]
            cur_above = above
        else:
            cur_x.append(x[i])
            cur_y.append(y[i])
    segs_x.append(cur_x)
    segs_y.append(cur_y)
    colors.append(GREEN if cur_above else RED)

    traces = []
    for sx, sy, c in zip(segs_x, segs_y, colors):
        traces.append(
            go.Scatter(
                x=sx, y=sy, mode="lines", line=dict(color=c, width=2),
                showlegend=False, hovertemplate="%{y:.2f}<extra></extra>",
            )
        )
    return traces


def price_chart(
    df: pd.DataFrame,
    view: str = "line",
    title: str = "",
    baseline_price: float | None = None,
) -> go.Figure:
    """Build a price chart in the requested view.

    ``view`` is one of: line, area, candlestick, ohlc.
    ``baseline_price`` enables the intraday green/red zero-crossing split for
    the line view (typically yesterday's close on a 1D chart).
    """
    if df is None or df.empty or "Close" not in df:
        return _empty("Live data unavailable — run locally with internet access.")

    fig = go.Figure()
    x = df.index

    if view == "candlestick" and {"Open", "High", "Low", "Close"} <= set(df.columns):
        fig.add_trace(
            go.Candlestick(
                x=x, open=df["Open"], high=df["High"], low=df["Low"],
                close=df["Close"], increasing_line_color=GREEN,
                decreasing_line_color=RED, name="",
            )
        )
    elif view == "ohlc" and {"Open", "High", "Low", "Close"} <= set(df.columns):
        fig.add_trace(
            go.Ohlc(
                x=x, open=df["Open"], high=df["High"], low=df["Low"],
                close=df["Close"], increasing_line_color=GREEN,
                decreasing_line_color=RED, name="",
            )
        )
    elif view == "area":
        up = df["Close"].iloc[-1] >= df["Close"].iloc[0]
        col = GREEN if up else RED
        fig.add_trace(
            go.Scatter(
                x=x, y=df["Close"], mode="lines", line=dict(color=col, width=2),
                fill="tozeroy", fillcolor=f"rgba({'22,199,132' if up else '234,57,67'},0.12)",
                showlegend=False, hovertemplate="%{y:.2f}<extra></extra>",
            )
        )
        fig.update_yaxes(autorange=True)
    else:  # line
        if baseline_price is not None:
            for tr in _split_by_baseline(x, df["Close"].tolist(), baseline_price):
                fig.add_trace(tr)
            fig.add_hline(
                y=baseline_price, line_dash="dot", line_color="#5a6072",
                annotation_text="prev close", annotation_position="right",
            )
        else:
            up = df["Close"].iloc[-1] >= df["Close"].iloc[0]
            fig.add_trace(
                go.Scatter(
                    x=x, y=df["Close"], mode="lines",
                    line=dict(color=GREEN if up else RED, width=2),
                    showlegend=False, hovertemplate="%{y:.2f}<extra></extra>",
                )
            )

    fig.update_layout(**_LAYOUT, title=title, xaxis_rangeslider_visible=False)
    return fig


def sparkline(values: list[float] | pd.Series, up: bool | None = None) -> go.Figure:
    """Tiny inline trend line for cards."""
    vals = list(values)
    if not vals:
        return _empty("")
    if up is None:
        up = vals[-1] >= vals[0]
    fig = go.Figure(
        go.Scatter(
            y=vals, mode="lines", line=dict(color=GREEN if up else RED, width=1.5),
            showlegend=False, hoverinfo="skip",
        )
    )
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=0, b=0),
        height=50, xaxis=dict(visible=False), yaxis=dict(visible=False),
    )
    return fig


def gauge(value: float, title: str = "", vmin: float = 0, vmax: float = 100) -> go.Figure:
    """Neutral score gauge (e.g. 0-100 composite). No advice implied."""
    frac = (value - vmin) / (vmax - vmin) if vmax != vmin else 0.5
    color = RED if frac < 0.33 else (BLUE if frac < 0.66 else GREEN)
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            title={"text": title, "font": {"size": 14}},
            gauge={
                "axis": {"range": [vmin, vmax]},
                "bar": {"color": color},
                "bgcolor": "#1a1d24",
                "bordercolor": GRID,
            },
        )
    )
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        height=220, margin=dict(l=20, r=20, t=40, b=10),
    )
    return fig
