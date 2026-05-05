"""Plotly chart builders.

All chart functions read colors from the module-level `_C` dict, which is
updated at render time by calling `set_theme(colors)` in app.py.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .config import COLORS

# Mutable theme dict — updated by set_theme() before each render
_C: dict = dict(COLORS)

# Convenience module-level vars — also updated by set_theme()
PLOT_BG = _C["card"]
PAPER_BG = _C["card"]
GRID = _C["divider"]
TEXT = _C["text"]
MUTED = _C["muted"]


def set_theme(colors: dict) -> None:
    """Switch the active color palette used by all chart functions."""
    global _C, PLOT_BG, PAPER_BG, GRID, TEXT, MUTED
    _C = dict(colors)
    PLOT_BG = PAPER_BG = _C["card"]
    GRID = _C["divider"]
    TEXT = _C["text"]
    MUTED = _C["muted"]


def _base_layout(**overrides) -> dict:
    base = dict(
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(color=TEXT, family="Inter, -apple-system, Segoe UI, sans-serif"),
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=GRID, borderwidth=1),
        hoverlabel=dict(bgcolor=_C["bg"], bordercolor=GRID, font=dict(color=TEXT)),
    )
    base.update(overrides)
    return base


def price_line_chart(
    normalized: pd.DataFrame,
    returns: pd.DataFrame,
    color_map: dict[str, str],
    benchmark_tickers: set[str] | None = None,
) -> go.Figure:
    """Normalized price line chart (first day = 100).

    Tickers listed in *benchmark_tickers* are rendered as dashed lines.
    """
    benchmark_tickers = benchmark_tickers or set()
    fig = go.Figure()
    for ticker in normalized.columns:
        is_bench = ticker in benchmark_tickers
        ret = (
            returns[ticker].reindex(normalized.index).fillna(0) * 100
            if ticker in returns.columns
            else pd.Series(0.0, index=normalized.index)
        )
        fig.add_trace(
            go.Scatter(
                x=normalized.index,
                y=normalized[ticker],
                name=ticker + (" (벤치마크)" if is_bench else ""),
                mode="lines",
                line=dict(
                    color=color_map.get(ticker, "#888"),
                    width=1.5 if is_bench else 2,
                    dash="dash" if is_bench else "solid",
                ),
                opacity=0.65 if is_bench else 1.0,
                customdata=np.stack([ret.values], axis=-1),
                hovertemplate=(
                    f"<b>{ticker}</b>{'&nbsp;(벤치마크)' if is_bench else ''}<br>"
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
            xaxis=dict(gridcolor=GRID, rangeslider=dict(visible=True, bgcolor=_C["bg"])),
            yaxis=dict(gridcolor=GRID, title="정규화 가격"),
            legend=dict(orientation="h", x=1, y=1.08, xanchor="right", bgcolor="rgba(0,0,0,0)"),
        )
    )
    return fig


def correlation_heatmap(corr: pd.DataFrame) -> go.Figure:
    z = corr.values
    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=list(corr.columns),
            y=list(corr.index),
            zmin=-1.0,
            zmax=1.0,
            colorscale="RdBu_r",
            hovertemplate="%{y} ↔ %{x}<br>상관계수: %{z:.3f}<extra></extra>",
            colorbar=dict(title=dict(text="상관계수", font=dict(color=TEXT)), tickfont=dict(color=TEXT)),
        )
    )
    annotations = []
    for i, row_label in enumerate(corr.index):
        for j, col_label in enumerate(corr.columns):
            val = z[i, j]
            text_color = "#000000" if abs(val) < 0.5 else "#ffffff"
            annotations.append(dict(
                x=col_label, y=row_label,
                text=f"{val:.2f}",
                showarrow=False,
                font=dict(color=text_color, size=14),
                xref="x", yref="y",
            ))
    fig.update_layout(
        **_base_layout(
            title="자산 간 상관관계 히트맵",
            height=480,
            xaxis=dict(side="bottom", showgrid=False),
            yaxis=dict(autorange="reversed", showgrid=False),
            annotations=annotations,
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
                marker=dict(size=18, color=color, symbol=symbol, line=dict(color=_C["bg"], width=2)),
                name=label,
                hovertemplate=(
                    f"<b>{label}</b><br>변동성: %{{x:.2f}}%<br>수익률: %{{y:.2f}}%"
                    f"<br>샤프: {point.get('sharpe', 0):.3f}<extra></extra>"
                ),
            )
        )

    if max_sharpe:
        _marker(max_sharpe, _C["optimal"], "최대 샤프", "star")
    if min_vol:
        _marker(min_vol, _C["min_vol_marker"], "최소 변동성", "diamond")
    if current:
        _marker(current, _C["current_marker"], "현재 포트폴리오", "circle")

    fig.update_layout(
        **_base_layout(
            title="Efficient Frontier (몬테카를로 시뮬레이션)",
            height=560,
            xaxis=dict(gridcolor=GRID, title="연간 변동성 (위험) %"),
            yaxis=dict(gridcolor=GRID, title="연간 기대수익률 %"),
            legend=dict(x=0.01, y=0.99, bgcolor=_C["card"], bordercolor=GRID, borderwidth=1),
        )
    )
    return fig


def weights_donut(
    weights: dict[str, float],
    port_ret: float,
    port_vol: float,
    color_map: dict[str, str],
) -> go.Figure:
    labels = list(weights.keys())
    values = [weights[t] * 100 for t in labels]
    colors = [color_map.get(t, "#888") for t in labels]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.62,
            marker=dict(colors=colors, line=dict(color=_C["bg"], width=2)),
            textinfo="label+percent",
            textfont=dict(color=TEXT, size=13),
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
            x=dd.index, y=dd.values, mode="lines",
            line=dict(color=_C["negative"], width=1.5),
            fill="tozeroy", fillcolor="rgba(198,40,40,0.25)",
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


# ── New charts ────────────────────────────────────────────────────────────────

def rolling_metrics_chart(rolling_df: pd.DataFrame) -> go.Figure:
    """Two-panel chart: rolling volatility (63d) and rolling Sharpe (252d)."""
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        subplot_titles=["롤링 변동성 (63일 기준, 연환산 %)", "롤링 샤프 지수 (252일 기준)"],
        vertical_spacing=0.12,
    )

    vol = rolling_df["rolling_vol"].dropna() * 100
    sharpe = rolling_df["rolling_sharpe"].dropna()

    fig.add_trace(go.Scatter(
        x=vol.index, y=vol.values, mode="lines",
        line=dict(color=_C["primary"], width=1.5), name="변동성",
        hovertemplate="%{x|%Y-%m-%d}<br>변동성: %{y:.2f}%<extra></extra>",
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=sharpe.index, y=sharpe.values, mode="lines",
        line=dict(color=_C["positive"], width=1.5), name="샤프",
        hovertemplate="%{x|%Y-%m-%d}<br>샤프: %{y:.3f}<extra></extra>",
    ), row=2, col=1)

    fig.add_hline(y=0, row=2, col=1, line=dict(color=_C["neutral"], width=1, dash="dot"))
    fig.add_hline(y=1, row=2, col=1, line=dict(color=_C["positive"], width=1, dash="dot"))

    fig.update_layout(
        paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
        font=dict(color=TEXT, family="Inter, -apple-system, Segoe UI, sans-serif"),
        margin=dict(l=40, r=20, t=60, b=40),
        height=440, showlegend=False,
        hoverlabel=dict(bgcolor=_C["bg"], bordercolor=GRID, font=dict(color=TEXT)),
    )
    fig.update_yaxes(gridcolor=GRID, ticksuffix="%", row=1, col=1)
    fig.update_yaxes(gridcolor=GRID, row=2, col=1)
    fig.update_xaxes(gridcolor=GRID)
    for ann in fig.layout.annotations:
        ann.update(font=dict(color=MUTED, size=12))
    return fig


def rebalancing_chart(strategies: dict[str, pd.Series]) -> go.Figure:
    """Cumulative return fan for buy-and-hold vs rebalancing strategies."""
    palette = [_C["stone"], _C["primary"], _C["positive"], _C["warning"]]
    widths = [2, 2.5, 2, 2]
    fig = go.Figure()
    for (name, series), color, width in zip(strategies.items(), palette, widths):
        cum_ret = (series - 1) * 100
        fig.add_trace(go.Scatter(
            x=series.index, y=cum_ret.values, mode="lines",
            name=name, line=dict(color=color, width=width),
            hovertemplate=f"<b>{name}</b><br>%{{x|%Y-%m-%d}}<br>누적 수익률: %{{y:+.2f}}%<extra></extra>",
        ))
    fig.update_layout(**_base_layout(
        title="리밸런싱 전략별 누적 수익률",
        height=420,
        yaxis=dict(gridcolor=GRID, title="누적 수익률 %", ticksuffix="%"),
        legend=dict(orientation="h", x=0, y=1.1, bgcolor="rgba(0,0,0,0)"),
    ))
    return fig


def forward_mc_chart(pct_df: pd.DataFrame, initial: float) -> go.Figure:
    """Fan chart for GBM forward Monte Carlo simulation."""
    idx = list(pct_df.index)
    fig = go.Figure()

    # Neutral blue-500 fan band — works on both light and dark canvases
    fig.add_trace(go.Scatter(
        x=idx + idx[::-1],
        y=list(pct_df["p95"]) + list(pct_df["p5"])[::-1],
        fill="toself", fillcolor="rgba(59,130,246,0.10)",
        line=dict(color="rgba(0,0,0,0)"), name="5–95%", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=idx + idx[::-1],
        y=list(pct_df["p75"]) + list(pct_df["p25"])[::-1],
        fill="toself", fillcolor="rgba(59,130,246,0.22)",
        line=dict(color="rgba(0,0,0,0)"), name="25–75%", hoverinfo="skip",
    ))
    for col, color, name, dash in [
        ("p95", _C["positive"], "최선 (95%)", "dot"),
        ("p5",  _C["negative"], "최악 (5%)",  "dot"),
    ]:
        fig.add_trace(go.Scatter(
            x=idx, y=pct_df[col].values, mode="lines",
            line=dict(color=color, width=1.2, dash=dash), name=name,
            hovertemplate=f"<b>{name}</b><br>%{{x|%Y-%m-%d}}<br>%{{y:,.0f}}원<extra></extra>",
        ))
    fig.add_trace(go.Scatter(
        x=idx, y=pct_df["p50"].values, mode="lines",
        line=dict(color=_C["primary"], width=2.5), name="중앙값 (50%)",
        hovertemplate="<b>중앙값</b><br>%{x|%Y-%m-%d}<br>%{y:,.0f}원<extra></extra>",
    ))
    fig.add_hline(
        y=initial, line=dict(color=_C["stone"], dash="dash", width=1),
        annotation_text="초기 투자금", annotation_font_color=_C["stone"],
    )
    fig.update_layout(**_base_layout(
        title="포트폴리오 미래 가치 시뮬레이션 (GBM · 500회)",
        height=460,
        yaxis=dict(gridcolor=GRID, title="포트폴리오 가치 (원)", tickformat=",.0f"),
        legend=dict(orientation="h", x=0, y=1.1, bgcolor="rgba(0,0,0,0)"),
    ))
    return fig
