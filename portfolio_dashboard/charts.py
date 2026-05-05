"""Plotly chart builders following the visualization spec."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .config import ASSETS, COLORS

PLOT_BG = COLORS["card"]
PAPER_BG = COLORS["card"]
GRID = COLORS["divider"]
TEXT = COLORS["text"]
MUTED = COLORS["muted"]


def _base_layout(**overrides) -> dict:
    base = dict(
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(color=TEXT, family="-apple-system, Segoe UI, sans-serif"),
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=GRID, borderwidth=1),
        hoverlabel=dict(bgcolor=COLORS["bg"], bordercolor=GRID, font=dict(color=TEXT)),
    )
    base.update(overrides)
    return base


def price_line_chart(normalized: pd.DataFrame, returns: pd.DataFrame) -> go.Figure:
    """2-1: Normalized price line chart (first day = 100)."""
    fig = go.Figure()
    for ticker in normalized.columns:
        ret = returns[ticker].reindex(normalized.index).fillna(0) * 100
        fig.add_trace(
            go.Scatter(
                x=normalized.index,
                y=normalized[ticker],
                name=ticker,
                mode="lines",
                line=dict(color=ASSETS[ticker]["color"], width=2),
                customdata=np.stack([ret.values], axis=-1),
                hovertemplate=(
                    f"<b>{ticker}</b><br>"
                    "%{x|%Y-%m-%d}<br>"
                    "정규화: %{y:.2f}<br>"
                    "당일 수익률: %{customdata[0]:+.2f}%<extra></extra>"
                ),
            )
        )
    fig.update_layout(
        **_base_layout(
            title="자산 가격 추이 (정규화, 시작일=100)",
            height=420,
            xaxis=dict(gridcolor=GRID, rangeslider=dict(visible=True, bgcolor=COLORS["bg"])),
            yaxis=dict(gridcolor=GRID, title="정규화 가격"),
            legend=dict(orientation="h", x=1, y=1.08, xanchor="right", bgcolor="rgba(0,0,0,0)"),
        )
    )
    return fig


def correlation_heatmap(corr: pd.DataFrame) -> go.Figure:
    """2-2: Correlation heatmap with RdBu_r palette, fixed -1..1."""
    z = corr.values
    text = [[f"{v:.2f}" for v in row] for row in z]
    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=list(corr.columns),
            y=list(corr.index),
            zmin=-1.0,
            zmax=1.0,
            colorscale="RdBu_r",
            text=text,
            texttemplate="%{text}",
            textfont=dict(color="white", size=14),
            hovertemplate="%{y} ↔ %{x}<br>상관계수: %{z:.3f}<extra></extra>",
            colorbar=dict(title=dict(text="상관계수", font=dict(color=TEXT)), tickfont=dict(color=TEXT)),
        )
    )
    fig.update_layout(
        **_base_layout(
            title="자산 간 상관관계 히트맵",
            height=480,
            width=480,
            xaxis=dict(side="bottom", showgrid=False),
            yaxis=dict(autorange="reversed", showgrid=False),
        )
    )
    return fig


def efficient_frontier_scatter(
    sims: pd.DataFrame,
    *,
    current: dict | None = None,
    max_sharpe: dict | None = None,
    min_vol: dict | None = None,
) -> go.Figure:
    """2-3: Scatter of simulated portfolios coloured by Sharpe (Viridis)."""
    fig = go.Figure()
    fig.add_trace(
        go.Scattergl(
            x=sims["vol"] * 100,
            y=sims["ret"] * 100,
            mode="markers",
            marker=dict(
                size=5,
                color=sims["sharpe"],
                colorscale="Viridis",
                showscale=True,
                opacity=0.5,
                colorbar=dict(title=dict(text="샤프 지수", font=dict(color=TEXT)), tickfont=dict(color=TEXT)),
            ),
            name="시뮬레이션",
            hovertemplate="변동성: %{x:.2f}%<br>수익률: %{y:.2f}%<extra></extra>",
        )
    )

    def _marker(point: dict, color: str, label: str, symbol: str = "star") -> None:
        fig.add_trace(
            go.Scatter(
                x=[point["vol"] * 100],
                y=[point["ret"] * 100],
                mode="markers",
                marker=dict(size=22, color=color, symbol=symbol, line=dict(color="white", width=1.5)),
                name=label,
                hovertemplate=(
                    f"<b>{label}</b><br>변동성: %{{x:.2f}}%<br>수익률: %{{y:.2f}}%"
                    f"<br>샤프: {point.get('sharpe', 0):.3f}<extra></extra>"
                ),
            )
        )

    if max_sharpe:
        _marker(max_sharpe, COLORS["optimal"], "최대 샤프", "star")
    if min_vol:
        _marker(min_vol, "#26C6DA", "최소 변동성", "diamond")
    if current:
        _marker(current, "#FF7043", "현재 포트폴리오", "circle")

    fig.update_layout(
        **_base_layout(
            title="Efficient Frontier (몬테카를로 시뮬레이션)",
            height=560,
            xaxis=dict(gridcolor=GRID, title="연간 변동성 (위험) %"),
            yaxis=dict(gridcolor=GRID, title="연간 기대수익률 %"),
            legend=dict(x=0.01, y=0.99, bgcolor="rgba(15,17,23,0.6)"),
        )
    )
    return fig


def weights_donut(weights: dict[str, float], port_ret: float, port_vol: float) -> go.Figure:
    """2-4: Donut showing portfolio weights with center stats."""
    labels = list(weights.keys())
    values = [weights[t] * 100 for t in labels]
    colors = [ASSETS[t]["color"] for t in labels]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.62,
            marker=dict(colors=colors, line=dict(color=COLORS["bg"], width=2)),
            textinfo="label+percent",
            textfont=dict(color="white", size=13),
            hovertemplate="<b>%{label}</b><br>비중: %{value:.2f}%<extra></extra>",
            sort=False,
            direction="clockwise",
        )
    )
    center = (
        f"<b style='font-size:18px'>수익률 {port_ret*100:+.2f}%</b><br>"
        f"<span style='color:{MUTED}'>변동성 {port_vol*100:.2f}%</span>"
    )
    fig.update_layout(
        **_base_layout(
            title="포트폴리오 비중",
            height=360,
            showlegend=False,
            annotations=[dict(text=center, x=0.5, y=0.5, showarrow=False, font=dict(color=TEXT))],
        )
    )
    return fig


def drawdown_chart(prices: pd.Series, ticker: str) -> go.Figure:
    dd = (prices / prices.cummax() - 1.0) * 100
    fig = go.Figure(
        go.Scatter(
            x=dd.index,
            y=dd.values,
            mode="lines",
            line=dict(color=COLORS["negative"], width=1.5),
            fill="tozeroy",
            fillcolor="rgba(198,40,40,0.25)",
            name=f"{ticker} MDD",
            hovertemplate="%{x|%Y-%m-%d}<br>낙폭: %{y:.2f}%<extra></extra>",
        )
    )
    fig.update_layout(
        **_base_layout(
            title=f"{ticker} 낙폭 (Drawdown)",
            height=260,
            yaxis=dict(gridcolor=GRID, title="낙폭 %", ticksuffix="%"),
        )
    )
    return fig
