"""Self-contained HTML report builder — no extra dependencies.

Returns a single HTML string with inline styles + Plotly figures embedded
via plotly's `to_html(full_html=False, include_plotlyjs="cdn")`.
"""
from __future__ import annotations

import datetime as dt
from html import escape

import pandas as pd
import plotly.graph_objects as go


def _fig_to_html(fig: go.Figure) -> str:
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"displayModeBar": False})


def build_report(
    *,
    title: str,
    period: tuple[dt.date, dt.date],
    summary_df: pd.DataFrame,
    portfolio_metrics: dict,
    figures: dict[str, go.Figure],
) -> str:
    """Assemble a one-page HTML report. Plotly.js is loaded via CDN."""
    start, end = period
    rows = "".join(
        f"<tr><td>{escape(idx)}</td>"
        + "".join(f"<td>{v}</td>" for v in row)
        + "</tr>"
        for idx, row in zip(summary_df.index.astype(str), summary_df.round(3).astype(str).values)
    )
    head = "".join(f"<th>{escape(c)}</th>" for c in summary_df.columns)

    metric_rows = "".join(
        f"<div class='m'><span>{escape(k)}</span><b>{escape(v)}</b></div>"
        for k, v in portfolio_metrics.items()
    )

    figures_html = "".join(
        f"<section><h2>{escape(name)}</h2>{_fig_to_html(fig)}</section>"
        for name, fig in figures.items()
    )

    return f"""<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8">
<title>{escape(title)}</title>
<script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>
<style>
  :root {{ --fg:#09090b; --muted:#52525b; --border:#e4e4e7; --bg:#ffffff; --soft:#f4f4f5; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: Inter, -apple-system, sans-serif; color: var(--fg); background: var(--bg);
         margin: 0; padding: 40px 56px; max-width: 1100px; }}
  h1 {{ font-size: 28px; font-weight: 600; letter-spacing: -0.02em; margin: 0 0 4px; }}
  h2 {{ font-size: 18px; font-weight: 600; margin: 32px 0 12px; }}
  .sub {{ color: var(--muted); font-size: 13px; margin-bottom: 28px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px;
          border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }}
  th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid var(--soft); }}
  th {{ background: var(--soft); color: var(--muted); font-weight: 500; }}
  .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 16px 0 24px; }}
  .m {{ border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; }}
  .m span {{ display:block; color: var(--muted); font-size: 11px; text-transform: uppercase;
             letter-spacing: 0.04em; margin-bottom: 4px; }}
  .m b {{ font-size: 18px; font-weight: 600; font-variant-numeric: tabular-nums; }}
  footer {{ margin-top: 40px; color: var(--muted); font-size: 11px; border-top: 1px solid var(--border); padding-top: 12px; }}
</style></head>
<body>
  <h1>{escape(title)}</h1>
  <div class='sub'>분석 기간 {start} → {end} · 생성일 {dt.date.today()}</div>
  <h2>포트폴리오 지표</h2>
  <div class='metrics'>{metric_rows}</div>
  <h2>자산 요약</h2>
  <table><thead><tr><th>자산</th>{head}</tr></thead><tbody>{rows}</tbody></table>
  {figures_html}
  <footer>Mean-Variance Portfolio Dashboard · Modern Portfolio Theory (Markowitz, 1952)
  · 무위험금리 0% 가정 · 연환산 252영업일 기준</footer>
</body></html>"""
