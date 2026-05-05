"""평균-분산 기반 투자 포트폴리오 분석 대시보드.

사용자가 직접 티커와 비중을 입력하여 자신의 포트폴리오를 분석할 수 있습니다.
Run: streamlit run app.py
"""
from __future__ import annotations

import datetime as dt
import textwrap

import numpy as np
import pandas as pd
import streamlit as st

from portfolio_dashboard import analysis, charts, data, portfolio, report
from portfolio_dashboard.config import (
    COLORS,
    DEFAULT_PERIOD_YEARS,
    DEFAULT_PORTFOLIO,
    EF_SIMULATIONS,
    TRADING_DAYS,
    color_for,
)
from portfolio_dashboard.presets import COMMON_TICKERS, PRESETS


# ---------- Alert helper ----------------------------------------------------
def alert(kind: str, msg: str) -> None:
    """Single entry-point for inline alerts; keeps tone/icon consistent."""
    {"info": st.info, "warn": st.warning, "error": st.error,
     "success": st.success}.get(kind, st.info)(msg)

st.set_page_config(
    page_title="Portfolio Analytics",
    page_icon="◐",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------- Theme-aware CSS builder (shadcn/ui · zinc) ---------------------
def _build_css(C: dict) -> str:
    return textwrap.dedent(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: {C['bg']};
  --card: {C['card']};
  --card-deep: {C['card_deep']};
  --border: {C['divider']};
  --border-soft: {C['divider_soft']};
  --fg: {C['text']};
  --muted-fg: {C['muted']};
  --stone: {C['stone']};
  --primary: {C['primary']};
  --primary-fg: {C['bg']};
  --positive: {C['positive']};
  --negative: {C['negative']};
  --warning: {C['warning']};
  --radius: 8px;
}}

html, body, [class*="css"], .stApp, .stMarkdown, p, span, div, li, label {{
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
  font-feature-settings: "cv11", "ss01", "cv02";
  letter-spacing: 0;
}}
code, kbd, pre, .stCode {{ font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace; }}

.stApp {{
  background-color: var(--bg) !important;
  color: var(--fg) !important;
  /* Override Streamlit's internal theme tokens so native widgets follow */
  --text-color: var(--fg);
  --default-textColor: var(--fg);
  --background-color: var(--bg);
  --secondary-background-color: var(--card-deep);
  --primary-color: var(--primary);
}}

/* Force foreground color on all text-bearing containers — Streamlit ships
   with high-specificity dark-theme rules that win over plain `color`. */
.stApp,
.stApp p, .stApp span, .stApp li, .stApp div,
.stApp label,
.stMarkdown, .stMarkdown *,
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] *,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] *,
.stToggle, .stToggle *, .stCheckbox, .stCheckbox *,
.stRadio, .stRadio *, .stSelectbox label,
[data-baseweb="checkbox"] *, [data-baseweb="radio"] * {{
  color: var(--fg) !important;
}}

/* Native alerts (st.warning/info/error/success) — keep tinted bg, fix text */
.stAlert, .stAlert *, [data-baseweb="notification"] * {{
  color: var(--fg) !important;
}}

h1, h2, h3, h4, h5, h6 {{
  font-family: 'Inter', sans-serif !important;
  color: var(--fg) !important;
  letter-spacing: -0.025em !important;
}}
h1 {{ font-size: 36px !important; line-height: 1.1 !important; font-weight: 600 !important; margin-bottom: 8px !important; }}
h2 {{ font-size: 24px !important; line-height: 1.2 !important; font-weight: 600 !important; }}
h3 {{ font-size: 18px !important; line-height: 1.3 !important; font-weight: 600 !important; }}
h4, h5, h6 {{ font-size: 15px !important; line-height: 1.4 !important; font-weight: 500 !important; }}

.section-eyebrow {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 500;
  color: var(--muted-fg);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  margin-bottom: 4px;
}}

/* shadcn Card */
.metric-card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px 20px;
  height: 100%;
}}
.metric-card h3 {{
  margin: 0 0 2px 0;
  font-size: 16px !important;
  font-weight: 600 !important;
  letter-spacing: -0.01em !important;
}}
.metric-card .sub {{
  color: var(--muted-fg);
  font-size: 12px;
  margin-bottom: 12px;
}}
.metric-row {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 7px 0;
  border-top: 1px solid var(--border-soft);
  font-size: 13px;
}}
.metric-row span:first-child {{ color: var(--muted-fg); cursor: default; }}
.metric-row span[title]:first-child {{ border-bottom: 1px dotted var(--stone); }}
/* Semantic colors — declared last + !important so the broad foreground
   override above doesn't swallow them. */
.stApp .pos, span.pos {{ color: var(--positive) !important; font-weight: 500; font-variant-numeric: tabular-nums; }}
.stApp .neg, span.neg {{ color: var(--negative) !important; font-weight: 500; font-variant-numeric: tabular-nums; }}
.stApp .neu, span.neu {{ color: var(--fg) !important; font-weight: 500; font-variant-numeric: tabular-nums; }}
.stApp .warn, span.warn {{ color: var(--warning) !important; font-weight: 500; font-variant-numeric: tabular-nums; }}
.stApp .section-eyebrow {{ color: var(--muted-fg) !important; }}
.stApp .metric-card .sub {{ color: var(--muted-fg) !important; }}
.stApp .metric-row span:first-child {{ color: var(--muted-fg) !important; }}
.stApp .badge-good {{ color: var(--positive) !important; }}
.stApp .badge-mid  {{ color: var(--warning) !important; }}
.stApp .badge-bad  {{ color: var(--negative) !important; }}

/* shadcn Badge — outline variant */
.badge {{
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  border: 1px solid var(--border);
  background: var(--card);
  margin-top: 8px;
}}
.badge-good {{ color: var(--positive); border-color: color-mix(in srgb, var(--positive) 35%, var(--border)); }}
.badge-mid  {{ color: var(--warning);  border-color: color-mix(in srgb, var(--warning) 35%, var(--border)); }}
.badge-bad  {{ color: var(--negative); border-color: color-mix(in srgb, var(--negative) 35%, var(--border)); }}

/* shadcn Button — default (primary). The selectors include all descendants
   so the broad `color: var(--fg)` cascade above doesn't leak in. */
.stButton > button, .stDownloadButton > button {{
  background-color: var(--primary) !important;
  border: 1px solid var(--primary) !important;
  border-radius: var(--radius) !important;
  font-family: 'Inter', sans-serif !important;
  font-weight: 500 !important;
  font-size: 14px !important;
  letter-spacing: 0 !important;
  height: 36px !important;
  padding: 8px 14px !important;
  box-shadow: 0 1px 2px 0 rgba(0,0,0,0.04);
  transition: opacity 120ms ease;
}}
.stButton > button, .stButton > button *,
.stDownloadButton > button, .stDownloadButton > button * {{
  color: var(--primary-fg) !important;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
  opacity: 0.9 !important;
}}
.stButton > button:focus, .stDownloadButton > button:focus {{
  outline: 2px solid var(--fg) !important;
  outline-offset: 2px;
}}

/* Slider — monochrome */
[data-baseweb="slider"] [role="slider"] {{
  background-color: var(--fg) !important;
  border-color: var(--fg) !important;
}}
[data-baseweb="slider"] > div > div > div {{ background-color: var(--fg) !important; }}

/* Sidebar */
section[data-testid="stSidebar"] {{
  background-color: var(--card-deep);
  border-right: 1px solid var(--border);
}}
section[data-testid="stSidebar"] .stButton > button {{
  height: 32px !important;
  padding: 6px 12px !important;
  font-size: 13px !important;
}}

/* shadcn Input */
.stDateInput input, .stTextInput input, .stNumberInput input,
.stSelectbox div[data-baseweb="select"] > div {{
  background-color: var(--bg) !important;
  color: var(--fg) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 14px !important;
  min-height: 36px !important;
}}
.stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus {{
  outline: 2px solid var(--fg) !important;
  outline-offset: -1px;
  border-color: var(--fg) !important;
}}

hr {{ border: none !important; border-top: 1px solid var(--border) !important; margin: 24px 0 !important; }}

.stCaption, [data-testid="stCaptionContainer"], small {{
  color: var(--muted-fg) !important;
  font-size: 12px !important;
}}

/* Alerts — shadcn-ish flat with border */
.stAlert {{
  border-radius: var(--radius) !important;
  border: 1px solid var(--border) !important;
  background: var(--card) !important;
}}

/* DataFrame (Glide grid uses internal theme — fall back to st.table where
   possible; this just keeps the wrapper from looking wrong) */
[data-testid="stDataFrame"] {{
  border-radius: var(--radius);
  overflow: hidden;
  border: 1px solid var(--border);
  background: var(--card) !important;
}}

/* Plotly chart container — strip any inherited dark background */
[data-testid="stPlotlyChart"], .js-plotly-plot, .plot-container {{
  background: transparent !important;
}}
[data-testid="element-container"] {{ background: transparent !important; }}

/* st.table — native HTML table, follows our cascade */
[data-testid="stTable"] table {{
  background: var(--card) !important;
  color: var(--fg) !important;
  border-collapse: separate;
  border-spacing: 0;
  width: 100%;
  font-size: 13px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}}
[data-testid="stTable"] th, [data-testid="stTable"] td {{
  background: var(--card) !important;
  color: var(--fg) !important;
  border-bottom: 1px solid var(--border-soft) !important;
  padding: 8px 12px !important;
  text-align: left !important;
}}
[data-testid="stTable"] thead th {{
  font-weight: 500 !important;
  color: var(--muted-fg) !important;
  font-size: 12px !important;
  text-transform: none;
}}
[data-testid="stTable"] tbody tr:last-child td {{ border-bottom: none !important; }}

/* Expander — flat with border */
[data-testid="stExpander"] {{
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  background: var(--card) !important;
}}
[data-testid="stExpander"] summary {{
  font-weight: 600;
  font-size: 15px;
}}

/* KPI strip — hero metrics row */
.kpi-strip {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin: 8px 0 4px 0;
}}
@media (max-width: 768px) {{
  .kpi-strip {{ grid-template-columns: repeat(2, 1fr); }}
}}
.kpi {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}}
.kpi-label {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 500;
  color: var(--muted-fg);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}}
.kpi-value {{
  font-size: 22px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.01em;
}}
.kpi-value.pos {{ color: var(--positive); }}
.kpi-value.neg {{ color: var(--negative); }}
.kpi-value.warn {{ color: var(--warning); }}
.kpi-value.neu {{ color: var(--fg); }}

/* Skeleton loader — shown while async data loads */
.skeleton {{
  background: linear-gradient(90deg, var(--border-soft) 25%, var(--border) 50%, var(--border-soft) 75%);
  background-size: 200% 100%;
  animation: skel 1.4s ease-in-out infinite;
  border-radius: var(--radius);
}}
@keyframes skel {{
  0%   {{ background-position: 200% 0; }}
  100% {{ background-position: -200% 0; }}
}}

/* Toggle / Checkbox — make handle visible in both themes */
[data-testid="stWidgetLabel"] label, .stToggle label {{ color: var(--fg); font-size: 14px; }}
.stCheckbox [role="checkbox"], .stToggle [role="checkbox"] {{
  border: 1px solid var(--border) !important;
  background: var(--card) !important;
}}
/* Native switch (newer Streamlit) */
[data-baseweb="checkbox"] > div:first-child {{
  border: 1px solid var(--border) !important;
}}
[data-baseweb="checkbox"][aria-checked="true"] > div:first-child,
[data-baseweb="checkbox"] input:checked + div {{
  background: var(--primary) !important;
  border-color: var(--primary) !important;
}}

/* Slider track visibility in light mode */
[data-baseweb="slider"] > div > div {{
  background: var(--border) !important;
}}
[data-baseweb="slider"] > div > div > div {{
  background: var(--primary) !important;
}}
</style>
""").strip()


# ---------- Session state init ---------------------------------------------
if "portfolio" not in st.session_state:
    st.session_state.portfolio = [dict(a) for a in DEFAULT_PORTFOLIO]
if "period_start" not in st.session_state:
    st.session_state.period_start = dt.date.today() - dt.timedelta(days=365 * DEFAULT_PERIOD_YEARS)
if "period_end" not in st.session_state:
    st.session_state.period_end = dt.date.today()


def _reset_row_widgets() -> None:
    for k in list(st.session_state.keys()):
        if k.startswith("t_") or k.startswith("w_") or k.startswith("rm_"):
            del st.session_state[k]


# ---------- URL portfolio load (runs once per session) ---------------------
if "url_loaded" not in st.session_state:
    raw_p = st.query_params.get("p", "")
    if raw_p:
        try:
            loaded = []
            for item in raw_p.split(","):
                if ":" in item:
                    t, w = item.rsplit(":", 1)
                    loaded.append({"ticker": t.strip().upper(), "weight": float(w)})
            if loaded:
                st.session_state.portfolio = loaded
                _reset_row_widgets()
                st.toast("공유 링크에서 포트폴리오를 불러왔습니다.")
        except Exception:
            pass
    st.session_state.url_loaded = True


# ---------- Theme + CSS (single light palette) -----------------------------
charts.set_theme(COLORS)
st.html(_build_css(COLORS))


# ---------- Compact layout helper ------------------------------------------
def _cols(*ratios: float) -> list:
    """Always stack vertically — unified compact layout per design spec."""
    return [st.container() for _ in ratios]


# ---------- Cached data functions (module-level for reliable caching) ------
@st.cache_data(show_spinner="가격 데이터를 불러오는 중…", ttl=60 * 30)
def load_prices(tickers_tuple: tuple, start: dt.date, end: dt.date, force_synth: bool):
    return data.fetch_prices(list(tickers_tuple), start, end, force_synthetic=force_synth)


@st.cache_data(show_spinner="벤치마크 데이터 로드 중…", ttl=60 * 30)
def load_benchmark(ticker: str, start: dt.date, end: dt.date, force_synth: bool) -> pd.DataFrame:
    if not ticker:
        return pd.DataFrame()
    df, _, _ = data.fetch_prices([ticker], start, end, force_synthetic=force_synth)
    return df


# Cache key derived from the data identity, not its CSV serialisation —
# avoids the round-trip cost and float-precision drift of to_csv/read_csv.
def _df_signature(df: pd.DataFrame) -> tuple:
    return (tuple(df.columns), df.index[0].isoformat(), df.index[-1].isoformat(), len(df))


@st.cache_data(show_spinner="EF 시뮬레이션 중…", ttl=60 * 30)
def _simulate_keyed(_prices: pd.DataFrame, _sig: tuple, n: int, rf: float) -> pd.DataFrame:
    return portfolio.simulate_frontier(_prices, n_sims=n, rf=rf)


def cached_simulate(prices: pd.DataFrame, n: int, rf: float) -> pd.DataFrame:
    return _simulate_keyed(prices, _df_signature(prices), n, round(rf, 6))


@st.cache_data(show_spinner="리밸런싱 시뮬레이션 중…", ttl=60 * 30)
def _rebalance_keyed(_prices: pd.DataFrame, _sig: tuple, weights_key: tuple, cost_bps: float) -> dict[str, pd.Series]:
    w = np.array(weights_key)
    return analysis.rebalance_backtest(_prices, w, cost_bps=cost_bps)


def cached_rebalance(prices: pd.DataFrame, weights: np.ndarray, cost_bps: float) -> dict[str, pd.Series]:
    return _rebalance_keyed(prices, _df_signature(prices), tuple(round(float(x), 6) for x in weights), float(cost_bps))


@st.cache_data(show_spinner="몬테카를로 시뮬레이션 중…", ttl=60 * 30)
def _forward_mc_keyed(_prices: pd.DataFrame, _sig: tuple, weights_key: tuple,
                      years: int, initial: float) -> pd.DataFrame:
    w = np.array(weights_key)
    return portfolio.forward_monte_carlo(_prices, w, years=years, n_sims=500, initial=initial)


def cached_forward_mc(prices: pd.DataFrame, weights: np.ndarray, years: int, initial: float) -> pd.DataFrame:
    return _forward_mc_keyed(prices, _df_signature(prices),
                             tuple(round(float(x), 6) for x in weights), years, initial)


# ---------- Sidebar -----------------------------------------------------------
with st.sidebar:
    st.markdown("<div class='section-eyebrow'>Portfolio</div>", unsafe_allow_html=True)
    st.markdown("### 보유 종목")
    st.caption("티커와 비중을 입력하세요 — 예: AAPL, BTC-USD, 005930.KS")

    # Preset selector — applies a named portfolio recipe in one click.
    preset_choice = st.selectbox(
        "프리셋",
        list(PRESETS.keys()),
        index=0,
        key="preset_sel",
        help="검증된 자산배분 모델을 한 번에 불러옵니다",
    )
    if preset_choice != "Custom" and st.session_state.get("_last_preset") != preset_choice:
        st.session_state.portfolio = [dict(a) for a in PRESETS[preset_choice]]
        st.session_state._last_preset = preset_choice
        _reset_row_widgets()
        st.rerun()
    elif preset_choice == "Custom":
        st.session_state._last_preset = "Custom"

    # Quick-add from curated ETF list — one tap to append.
    held = {a["ticker"] for a in st.session_state.portfolio}
    addable = [(t, label) for t, label in COMMON_TICKERS if t not in held]
    if addable:
        labels = [f"{t} — {label}" for t, label in addable]
        sel = st.selectbox(
            "+ 인기 ETF 빠른 추가",
            ["선택…"] + labels,
            key="quickadd_sel",
            help="대표 ETF·지수 30선",
        )
        if sel != "선택…":
            chosen = addable[labels.index(sel)][0]
            st.session_state.portfolio.append({"ticker": chosen, "weight": 0.0})
            _reset_row_widgets()
            st.rerun()

    rm_idx = None
    for i, asset in enumerate(st.session_state.portfolio):
        c1, c2, c3 = st.columns([3, 2, 1])
        with c1:
            new_ticker = st.text_input(
                "티커", value=asset["ticker"], key=f"t_{i}",
                label_visibility="collapsed", placeholder="티커",
            )
        with c2:
            new_weight = st.number_input(
                "비중", value=float(asset["weight"]), key=f"w_{i}",
                min_value=0.0, max_value=100.0, step=1.0,
                label_visibility="collapsed",
            )
        with c3:
            if st.button("×", key=f"rm_{i}", help="삭제", use_container_width=True):
                rm_idx = i
        color = color_for(i)
        st.markdown(
            f"<div style='height:3px;background:{color};border-radius:2px;"
            f"margin:-12px 0 6px 0'></div>",
            unsafe_allow_html=True,
        )
        asset["ticker"] = new_ticker.strip().upper()
        asset["weight"] = float(new_weight)

    if rm_idx is not None:
        st.session_state.portfolio.pop(rm_idx)
        _reset_row_widgets()
        st.rerun()

    bc1, bc2 = st.columns(2)
    if bc1.button("+ 종목 추가", use_container_width=True):
        st.session_state.portfolio.append({"ticker": "", "weight": 0.0})
        _reset_row_widgets()
        st.rerun()
    if bc2.button("균등 배분", use_container_width=True):
        valid = [a for a in st.session_state.portfolio if a["ticker"]]
        if valid:
            eq = round(100.0 / len(valid), 2)
            for a in st.session_state.portfolio:
                a["weight"] = eq if a["ticker"] else 0.0
            _reset_row_widgets()
            st.rerun()

    total_weight = sum(a["weight"] for a in st.session_state.portfolio if a["ticker"])
    if abs(total_weight - 100) < 0.5:
        st.caption(f"비중 합계 {total_weight:.1f}%")
    else:
        st.caption(f"비중 합계 {total_weight:.1f}% — 자동 정규화하여 계산")

    _share_p = ",".join(
        f"{a['ticker']}:{a['weight']:.1f}"
        for a in st.session_state.portfolio if a["ticker"]
    )
    if st.button("공유 링크 생성", use_container_width=True, help="이 포트폴리오를 URL로 공유"):
        st.session_state.show_share = not st.session_state.get("show_share", False)
    if st.session_state.get("show_share") and _share_p:
        st.code(f"?p={_share_p}", language=None)
        st.caption("URL 뒤에 붙여넣으면 동일 포트폴리오로 열립니다")

    st.divider()

    st.markdown("<div class='section-eyebrow'>Period</div>", unsafe_allow_html=True)
    st.markdown("### 분석 기간")
    today = dt.date.today()

    p1, p2, p3 = st.columns(3)
    p4, p5, p6 = st.columns(3)
    presets = [(p1, "1년", 1), (p2, "3년", 3), (p3, "5년", 5),
               (p4, "10년", 10), (p5, "20년", 20), (p6, "30년", 30)]
    for col, label, years in presets:
        if col.button(label, use_container_width=True, key=f"preset_{years}"):
            st.session_state.period_start = today - dt.timedelta(days=365 * years)
            st.session_state.period_end = today
            st.rerun()

    date_range = st.date_input(
        "직접 선택",
        value=(st.session_state.period_start, st.session_state.period_end),
        min_value=dt.date(1980, 1, 1),
        max_value=today,
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = st.session_state.period_start
        end_date = st.session_state.period_end
    st.session_state.period_start = start_date
    st.session_state.period_end = end_date

    st.divider()
    force_synth = st.toggle(
        "오프라인(샘플) 데이터 사용", value=False,
        help="네트워크 없이 합성 데이터로 동작 (실제 분석에는 권장 X)",
    )
    n_sims = st.slider(
        "EF 시뮬레이션 수", 1000, 20000, EF_SIMULATIONS, step=1000,
        help="Efficient Frontier 몬테카를로 시뮬레이션 횟수. 많을수록 정밀하지만 느립니다",
    )

    st.divider()
    st.markdown("<div class='section-eyebrow'>Risk-free</div>", unsafe_allow_html=True)
    use_live_rf = st.toggle(
        "실시간 무위험 수익률 사용 (^IRX)", value=not force_synth,
        help="Yahoo Finance에서 13주 미국 단기국채 수익률을 가져와 샤프 계산에 반영",
        key="use_live_rf",
    )
    if use_live_rf and not force_synth:
        rf_rate, rf_source = data.fetch_risk_free_rate()
    else:
        rf_rate, rf_source = 0.04, "default"
    rf_rate = st.slider(
        "무위험 수익률 (연, %)", 0.0, 10.0, float(round(rf_rate * 100, 2)), step=0.05,
        help="샤프·최대샤프·롤링 샤프·알파/베타 계산에 사용됩니다",
    ) / 100.0
    st.caption(
        f"출처: {'^IRX (Yahoo Finance)' if rf_source == 'yfinance' else '기본값(수동 조정 권장)'}"
    )

    st.divider()
    cost_bps = st.slider(
        "리밸런싱 거래비용 (bps)", 0, 50, 5, step=1,
        help="섹션 6 리밸런싱 시뮬레이션에 적용 — 1bp = 0.01%. 매도+매수 양방향에 적용",
    )

    st.divider()
    st.markdown("<div class='section-eyebrow'>Benchmark</div>", unsafe_allow_html=True)
    st.markdown("### 비교 지수")
    _BENCH_MAP = {
        "없음": "",
        "SPY (S&P 500)": "SPY",
        "QQQ (나스닥100)": "QQQ",
        "BND (미국 채권)": "BND",
        "GLD (금)": "GLD",
        "^KS11 (코스피)": "^KS11",
    }
    bench_label = st.selectbox(
        "기준 지수", list(_BENCH_MAP.keys()), key="bench_sel",
        help="가격 차트에 오버레이할 비교 기준 지수를 선택합니다",
    )
    bench_ticker = _BENCH_MAP[bench_label]

    st.divider()
    st.markdown("<div class='section-eyebrow'>Forecast</div>", unsafe_allow_html=True)
    st.markdown("### 미래 시뮬레이션")
    initial_inv = st.number_input(
        "초기 투자금 (원)", min_value=1_000_000, max_value=10_000_000_000,
        value=10_000_000, step=1_000_000, format="%d",
        help="섹션 7 GBM 시뮬레이션의 초기 투자 원금",
    )
    mc_years = st.slider(
        "시뮬레이션 기간 (년)", 1, 30, 10,
        help="미래 가치 시뮬레이션의 투자 기간",
    )


# ---------- Resolve portfolio & load data -----------------------------------
valid_assets = [a for a in st.session_state.portfolio if a["ticker"]]
tickers = [a["ticker"] for a in valid_assets]
raw_weights = {a["ticker"]: a["weight"] for a in valid_assets}

if not tickers:
    st.warning("사이드바에서 분석할 종목 티커를 1개 이상 입력하세요.")
    st.stop()

prices, source, missing = load_prices(tuple(tickers), start_date, end_date, force_synth)

available_tickers = list(prices.columns) if not prices.empty else []
tickers = [t for t in tickers if t in available_tickers]
if not tickers:
    st.error(
        f"입력하신 티커들의 데이터를 가져올 수 없습니다: {', '.join(missing) or '?'}. "
        f"티커를 확인해 주세요. (Yahoo Finance 형식 — 예: 한국 주식은 005930.KS)"
    )
    st.stop()

raw_weights = {t: raw_weights[t] for t in tickers}
total_w = sum(raw_weights.values())
if total_w == 0:
    norm_w = {t: 1 / len(tickers) for t in tickers}
    st.warning("모든 비중이 0 — 균등 비중으로 가정합니다.")
else:
    norm_w = {t: w / total_w for t, w in raw_weights.items()}

color_map = {t: color_for(i) for i, t in enumerate(tickers)}

# Sync portfolio to URL query param
_url_p = ",".join(
    f"{a['ticker']}:{a['weight']:.1f}"
    for a in st.session_state.portfolio if a["ticker"]
)
if _url_p:
    st.query_params["p"] = _url_p

# Benchmark
bench_prices_raw = load_benchmark(bench_ticker, start_date, end_date, force_synth)
if bench_ticker and not bench_prices_raw.empty and bench_ticker in bench_prices_raw.columns:
    bench_aligned = bench_prices_raw[[bench_ticker]].reindex(prices.index).ffill().dropna()
    # If benchmark is already a portfolio holding, use a disambiguated display name
    # so concat doesn't produce duplicate columns in charts.
    if bench_ticker in prices.columns:
        _bench_display = bench_ticker + " (지수)"
        bench_aligned = bench_aligned.rename(columns={bench_ticker: _bench_display})
        bench_tickers_set: set[str] = {_bench_display}
        bench_color_map = {_bench_display: COLORS["stone"]}
    else:
        bench_tickers_set = {bench_ticker}
        bench_color_map = {bench_ticker: COLORS["stone"]}
else:
    bench_aligned = pd.DataFrame()
    bench_color_map = {}
    bench_tickers_set = set()

returns = analysis.daily_returns(prices)
summary = analysis.asset_summary(prices, rf=rf_rate)
corr = analysis.correlation(prices)
w_array = np.array([norm_w[t] for t in tickers])
stats = portfolio.portfolio_stats(w_array, prices, rf=rf_rate)


# ---------- Header ----------------------------------------------------------
st.title("포트폴리오 분석 대시보드")
actual_start = prices.index.min().date()
actual_end = prices.index.max().date()
years_covered = (actual_end - actual_start).days / 365.25
st.caption(
    f"분석 기간 **{actual_start} → {actual_end}** ({years_covered:.1f}년) · "
    f"영업일 {len(prices):,}개 · 자산 {len(prices.columns)}개"
)
if missing:
    alert("warn",
        f"다음 티커는 데이터를 가져올 수 없어 제외되었습니다: **{', '.join(missing)}**. "
        f"오타이거나 상장폐지/거래정지된 종목일 수 있습니다."
    )
if (actual_start - start_date).days > 30:
    alert("info",
        f"일부 자산의 상장일이 늦어 실제 분석 시작일은 **{actual_start}** 입니다. "
        f"(여러 자산의 공통 데이터 구간 자동 적용)"
    )

# ---------- KPI strip — Linear/Vercel-style hero metrics -------------------
_total_ret = float((prices.iloc[-1] / prices.iloc[0] - 1) @ w_array) * 100
_p_mdd = float(analysis.max_drawdown(
    pd.Series(((prices / prices.iloc[0]) * w_array).sum(axis=1), index=prices.index).to_frame("p")
).iloc[0]) * 100
_kpi = [
    ("연 기대수익률", f"{stats.annual_return*100:+.2f}%",
     "pos" if stats.annual_return >= 0 else "neg"),
    ("연 변동성", f"{stats.annual_vol*100:.2f}%", "neu"),
    ("샤프 지수", f"{stats.sharpe:.2f}",
     "pos" if stats.sharpe >= 1 else "warn" if stats.sharpe >= 0.5 else "neg"),
    ("기간 누적 수익률", f"{_total_ret:+.2f}%",
     "pos" if _total_ret >= 0 else "neg"),
]
st.markdown(
    "<div class='kpi-strip'>"
    + "".join(
        f"<div class='kpi'><span class='kpi-label'>{label}</span>"
        f"<span class='kpi-value {cls}'>{value}</span></div>"
        for label, value, cls in _kpi
    )
    + "</div>",
    unsafe_allow_html=True,
)
st.divider()


# ---------- SECTION 1 + 2 ---------------------------------------------------
sec1, sec2 = _cols(1.1, 1)

with sec1:
    st.markdown("<div class='section-eyebrow'>01 · Assets</div>", unsafe_allow_html=True)
    st.subheader("자산 현황")
    n_card_cols = 2 if len(tickers) >= 2 else 1
    cards = st.columns(n_card_cols)
    for idx, ticker in enumerate(tickers):
        row = summary.loc[ticker]
        ret_pct = row["annual_return"] * 100
        vol_pct = row["annual_vol"] * 100
        sharpe = row["sharpe"]
        mdd_pct = row["mdd"] * 100
        ret_cls = "pos" if ret_pct >= 0 else "neg"
        if sharpe >= 1.0:
            badge, sharpe_cls = "<span class='badge badge-good'>우수</span>", "pos"
        elif sharpe >= 0.5:
            badge, sharpe_cls = "<span class='badge badge-mid'>보통</span>", "warn"
        else:
            badge, sharpe_cls = "<span class='badge badge-bad'>낮음</span>", "neg"
        with cards[idx % n_card_cols]:
            st.markdown(
                f"""<div class='metric-card'>
                  <h3 style='color:{color_map[ticker]}'>{ticker}</h3>
                  <div class='sub'>비중 {norm_w[ticker]*100:.1f}%</div>
                  <div class='metric-row'>
                    <span title="연환산 기대수익률 (과거 일간 수익률 × 252)">연 수익률</span>
                    <span class='{ret_cls}'>{ret_pct:+.2f}%</span></div>
                  <div class='metric-row'>
                    <span title="연환산 수익률 표준편차 (일간 변동성 × √252)">연 변동성</span>
                    <span class='neu'>{vol_pct:.2f}%</span></div>
                  <div class='metric-row'>
                    <span title="샤프 지수 = 연수익률 ÷ 연변동성 (무위험금리 0% 가정)">샤프 지수</span>
                    <span class='{sharpe_cls}'>{sharpe:.2f}</span></div>
                  <div class='metric-row'>
                    <span title="최대 낙폭: 고점 대비 최대 하락률">최대 낙폭(MDD)</span>
                    <span class='neg'>{mdd_pct:.2f}%</span></div>
                  {badge}
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("&nbsp;", unsafe_allow_html=True)
    if not bench_aligned.empty:
        disp_prices = pd.concat([prices, bench_aligned], axis=1).dropna()
        disp_norm = data.normalize(disp_prices)
        disp_returns = analysis.daily_returns(disp_prices)
        disp_color_map = {**color_map, **bench_color_map}
    else:
        disp_norm = data.normalize(prices)
        disp_returns = returns
        disp_color_map = color_map
    st.plotly_chart(
        charts.price_line_chart(disp_norm, disp_returns, disp_color_map, benchmark_tickers=bench_tickers_set),
        use_container_width=True,
    )

with sec2:
    st.markdown("<div class='section-eyebrow'>02 · Correlation</div>", unsafe_allow_html=True)
    st.subheader("상관관계 분석")
    if len(tickers) >= 2:
        st.plotly_chart(charts.correlation_heatmap(corr), use_container_width=True)
        n = len(corr)
        avg_off_diag = (corr.values.sum() - n) / (n * n - n)
        st.info(
            f"평균 비대각 상관계수 **{avg_off_diag:.3f}**. "
            + ("상관성이 낮아 분산 투자 효과가 큽니다." if avg_off_diag < 0.3
               else "상관성이 높아 분산 효과가 제한적일 수 있습니다.")
        )
    else:
        st.info("상관관계 분석은 자산 2개 이상에서 가능합니다.")

    with st.expander("용어 설명"):
        st.markdown(
            """
**비대각 상관계수 (Off-diagonal Correlation)**

상관행렬에서 대각선(자기 자신과의 상관 = 1.0)을 제외한 나머지 값들입니다.
- **+1에 가까울수록**: 두 자산이 거의 동일하게 움직여 분산 투자 효과가 작습니다.
- **0에 가까울수록**: 움직임이 독립적이어서 한쪽 하락 시 다른 쪽이 방어해 줍니다.
- **−1에 가까울수록**: 반대로 움직여 헤지(위험 상쇄) 효과가 극대화됩니다.

**샤프 지수 (Sharpe Ratio)**

> 샤프 지수 = (연 기대수익률 − 무위험금리) ÷ 연 변동성

- **1.0 이상**: 우수 · **0.5~1.0**: 보통 · **0.5 미만**: 낮음
            """,
        )

st.divider()


# ---------- SECTION 3: 포트폴리오 분석 -------------------------------------
st.markdown("<div class='section-eyebrow'>03 · Portfolio</div>", unsafe_allow_html=True)
st.subheader("포트폴리오 분석")

col_donut, col_metrics = _cols(1.1, 1)

with col_donut:
    st.plotly_chart(
        charts.weights_donut(norm_w, stats.annual_return, stats.annual_vol, color_map),
        use_container_width=True,
    )

with col_metrics:
    st.markdown("##### 포트폴리오 지표 (현재 비중 기준)")
    ret_pct = stats.annual_return * 100
    vol_pct = stats.annual_vol * 100
    cls = "pos" if ret_pct >= 0 else "neg"
    sharpe_cls = "pos" if stats.sharpe >= 1 else "warn" if stats.sharpe >= 0.5 else "neg"
    var95, cvar95 = analysis.var_cvar(prices, w_array)

    st.markdown(
        f"""<div class='metric-card'>
          <div class='metric-row'>
            <span title="연환산 기대수익률">연 기대수익률</span>
            <span class='{cls}'>{ret_pct:+.2f}%</span></div>
          <div class='metric-row'>
            <span title="연환산 변동성 (위험)">연 변동성</span>
            <span class='neu'>{vol_pct:.2f}%</span></div>
          <div class='metric-row'>
            <span title="샤프 지수 = 수익률 ÷ 변동성">샤프 지수</span>
            <span class='{sharpe_cls}'>{stats.sharpe:.3f}</span></div>
          <div class='metric-row'><span>샤프 평가</span>
            <span class='{sharpe_cls}'>{'우수' if stats.sharpe >= 1 else '보통' if stats.sharpe >= 0.5 else '낮음'}</span></div>
          <div class='metric-row'>
            <span title="Value at Risk: 95% 신뢰수준 기준 하루 최대 손실">VaR 95% (일)</span>
            <span class='neg'>-{var95*100:.2f}%</span></div>
          <div class='metric-row'>
            <span title="CVaR (Expected Shortfall): VaR 초과 손실의 평균">CVaR 95% (일)</span>
            <span class='neg'>-{cvar95*100:.2f}%</span></div>
        </div>""",
        unsafe_allow_html=True,
    )

    eq_w = np.full(len(tickers), 1 / len(tickers))
    eq_stats = portfolio.portfolio_stats(eq_w, prices, rf=rf_rate)
    delta_ret = (stats.annual_return - eq_stats.annual_return) * 100
    delta_vol = (stats.annual_vol - eq_stats.annual_vol) * 100
    st.caption(f"균등 비중 대비 수익률 {delta_ret:+.2f}%p · 변동성 {delta_vol:+.2f}%p")

    export_rows = []
    for t in tickers:
        r = summary.loc[t]
        export_rows.append({
            "자산": t, "비중(%)": round(norm_w[t] * 100, 2),
            "연수익률(%)": round(r["annual_return"] * 100, 2),
            "연변동성(%)": round(r["annual_vol"] * 100, 2),
            "샤프지수": round(r["sharpe"], 3),
            "MDD(%)": round(r["mdd"] * 100, 2),
        })
    export_rows.append({
        "자산": "【포트폴리오】", "비중(%)": 100.0,
        "연수익률(%)": round(ret_pct, 2),
        "연변동성(%)": round(vol_pct, 2),
        "샤프지수": round(stats.sharpe, 3),
        "MDD(%)": "",
    })
    csv_bytes = pd.DataFrame(export_rows).to_csv(index=False).encode("utf-8-sig")

    dl1, dl2 = st.columns(2)
    dl1.download_button(
        "CSV 다운로드", csv_bytes,
        file_name="portfolio_analysis.csv", mime="text/csv",
        use_container_width=True,
    )

    # Self-contained HTML report — bundles metrics table + key figures.
    summary_for_report = pd.DataFrame(export_rows).set_index("자산")
    if not bench_aligned.empty:
        disp_for_report = pd.concat([prices, bench_aligned], axis=1).dropna()
        norm_for_report = data.normalize(disp_for_report)
        rets_for_report = analysis.daily_returns(disp_for_report)
        cmap_for_report = {**color_map, **bench_color_map}
    else:
        norm_for_report = data.normalize(prices)
        rets_for_report = returns
        cmap_for_report = color_map

    report_metrics = {
        "연 기대수익률": f"{stats.annual_return*100:+.2f}%",
        "연 변동성": f"{stats.annual_vol*100:.2f}%",
        "샤프 지수": f"{stats.sharpe:.3f}",
        "기간 누적 수익률": f"{_total_ret:+.2f}%",
    }
    report_figs = {
        "자산 가격 추이": charts.price_line_chart(
            norm_for_report, rets_for_report, cmap_for_report,
            benchmark_tickers=bench_tickers_set,
        ),
        "포트폴리오 비중": charts.weights_donut(
            norm_w, stats.annual_return, stats.annual_vol, color_map,
        ),
    }
    if len(tickers) >= 2:
        report_figs["상관관계"] = charts.correlation_heatmap(corr)

    html_bytes = report.build_report(
        title="포트폴리오 분석 리포트",
        period=(actual_start, actual_end),
        summary_df=summary_for_report,
        portfolio_metrics=report_metrics,
        figures=report_figs,
    ).encode("utf-8")
    dl2.download_button(
        "HTML 리포트 다운로드", html_bytes,
        file_name=f"portfolio_report_{actual_end}.html",
        mime="text/html",
        use_container_width=True,
    )

st.divider()


# ---------- SECTION 4: 포트폴리오 구성 추천 --------------------------------
with st.expander("04 · 포트폴리오 구성 추천 (Efficient Frontier)", expanded=True):
    if len(tickers) >= 2:
        sims = cached_simulate(prices, n_sims, rf_rate)
        max_sharpe_opt = portfolio.optimize(prices, "max_sharpe", rf=rf_rate)
        min_vol_opt = portfolio.optimize(prices, "min_vol", rf=rf_rate)

        current_point = {"vol": stats.annual_vol, "ret": stats.annual_return, "sharpe": stats.sharpe}
        max_point = {"vol": max_sharpe_opt.annual_vol, "ret": max_sharpe_opt.annual_return, "sharpe": max_sharpe_opt.sharpe}
        min_point = {"vol": min_vol_opt.annual_vol, "ret": min_vol_opt.annual_return, "sharpe": min_vol_opt.sharpe}

        ef_left, ef_right = _cols(2, 1)
        with ef_left:
            st.plotly_chart(
                charts.efficient_frontier_scatter(sims, current=current_point, max_sharpe=max_point, min_vol=min_point),
                use_container_width=True,
            )
        with ef_right:
            st.markdown("##### 최적 포트폴리오 비중")
            rows = []
            for t, w_max, w_min in zip(tickers, max_sharpe_opt.weights, min_vol_opt.weights):
                rows.append({
                    "자산": t,
                    "최대 샤프 (%)": round(w_max * 100, 2),
                    "최소 변동성 (%)": round(w_min * 100, 2),
                    "현재 (%)": round(norm_w[t] * 100, 2),
                })
            st.table(pd.DataFrame(rows).set_index("자산"))
            st.markdown(
                f"- **최대 샤프** — 수익률 {max_sharpe_opt.annual_return*100:+.2f}% · "
                f"변동성 {max_sharpe_opt.annual_vol*100:.2f}% · 샤프 {max_sharpe_opt.sharpe:.3f}\n"
                f"- **최소 변동성** — 수익률 {min_vol_opt.annual_return*100:+.2f}% · "
                f"변동성 {min_vol_opt.annual_vol*100:.2f}% · 샤프 {min_vol_opt.sharpe:.3f}\n"
                f"- **현재** — 수익률 {stats.annual_return*100:+.2f}% · "
                f"변동성 {stats.annual_vol*100:.2f}% · 샤프 {stats.sharpe:.3f}"
            )
            if st.button("최대 샤프 비중 적용", use_container_width=True, key="apply_max"):
                for i, t in enumerate(tickers):
                    for a in st.session_state.portfolio:
                        if a["ticker"] == t:
                            a["weight"] = float(round(max_sharpe_opt.weights[i] * 100, 1))
                _reset_row_widgets()
                st.rerun()
            if st.button("최소 변동성 비중 적용", use_container_width=True, key="apply_min"):
                for i, t in enumerate(tickers):
                    for a in st.session_state.portfolio:
                        if a["ticker"] == t:
                            a["weight"] = float(round(min_vol_opt.weights[i] * 100, 1))
                _reset_row_widgets()
                st.rerun()
    else:
        st.info("Efficient Frontier 분석은 자산 2개 이상에서 가능합니다.")


# ---------- SECTION 5: 롤링 지표 -------------------------------------------
with st.expander("05 · 롤링 지표", expanded=False):
    rolling_df = analysis.rolling_metrics(prices, w_array, rf=rf_rate)
    st.plotly_chart(charts.rolling_metrics_chart(rolling_df), use_container_width=True)
    st.caption(
        "롤링 변동성: 63영업일(약 3개월) 기준 연환산 · "
        "롤링 샤프: 252영업일(1년) 기준 · 점선 = 0 및 샤프 1.0 기준선"
    )


# ---------- SECTION 5b: 벤치마크 회귀 (Alpha / Beta / IR) -------------------
if not bench_aligned.empty:
    with st.expander(f"05b · 벤치마크 회귀 ({bench_ticker})", expanded=False):
        reg = analysis.regression_stats(prices, w_array, bench_aligned.iloc[:, 0], rf=rf_rate)
        if np.isnan(reg["beta"]):
            st.info("회귀 통계 계산에 필요한 데이터가 부족합니다.")
        else:
            alpha_cls = "pos" if reg["alpha"] >= 0 else "neg"
            ir_cls = "pos" if reg["info_ratio"] >= 0.5 else "warn" if reg["info_ratio"] >= 0 else "neg"
            st.markdown(
                f"""<div class='metric-card'>
                  <div class='metric-row'>
                    <span title="CAPM 알파 (연환산) — 시장 대비 초과 수익">알파 (연 %)</span>
                    <span class='{alpha_cls}'>{reg["alpha"]*100:+.2f}%</span></div>
                  <div class='metric-row'>
                    <span title="시장 민감도 — 1.0이면 시장과 동일, &gt;1이면 변동성 큼">베타</span>
                    <span class='neu'>{reg["beta"]:.3f}</span></div>
                  <div class='metric-row'>
                    <span title="Information Ratio — 추적오차 단위당 초과 수익">정보 비율</span>
                    <span class='{ir_cls}'>{reg["info_ratio"]:.3f}</span></div>
                  <div class='metric-row'>
                    <span title="결정계수 — 시장으로 설명되는 수익 변동의 비율">R²</span>
                    <span class='neu'>{reg["r2"]:.3f}</span></div>
                </div>""",
                unsafe_allow_html=True,
            )
            st.caption(
                f"기준 지수: **{bench_ticker}** · 무위험금리 {rf_rate*100:.2f}% · "
                f"표본 {len(bench_aligned):,}일"
            )


# ---------- SECTION 6: 리밸런싱 시뮬레이션 ----------------------------------
with st.expander("06 · 리밸런싱 시뮬레이션", expanded=False):
    rb_strategies = cached_rebalance(prices, w_array, cost_bps)
    rb_left, rb_right = _cols(2, 1)
    with rb_left:
        st.plotly_chart(charts.rebalancing_chart(rb_strategies), use_container_width=True)
    with rb_right:
        st.markdown("##### 전략별 결과 요약")
        rb_rows = []
        for name, series in rb_strategies.items():
            total_ret = (series.iloc[-1] - 1) * 100
            d_rets = series.pct_change().dropna()
            ann_vol_rb = d_rets.std() * np.sqrt(TRADING_DAYS) * 100
            ann_ret_rb = d_rets.mean() * TRADING_DAYS * 100
            sharpe_rb = ann_ret_rb / ann_vol_rb if ann_vol_rb > 0 else 0
            rb_rows.append({
                "전략": name,
                "누적 수익률 (%)": round(total_ret, 2),
                "연 변동성 (%)": round(ann_vol_rb, 2),
                "샤프": round(sharpe_rb, 3),
            })
        st.table(pd.DataFrame(rb_rows).set_index("전략"))
        st.caption(
            f"동일 자산·기간·비중, 리밸런싱 주기만 다르게 비교합니다 · "
            f"거래비용 {cost_bps}bps 적용"
        )


# ---------- SECTION 7: 미래 가치 시뮬레이션 ---------------------------------
with st.expander("07 · 미래 가치 시뮬레이션", expanded=False):
    mc_df = cached_forward_mc(prices, w_array, mc_years, float(initial_inv))
    mc_left, mc_right = _cols(2, 1)
    with mc_left:
        st.plotly_chart(charts.forward_mc_chart(mc_df, float(initial_inv)), use_container_width=True)
    with mc_right:
        final = mc_df.iloc[-1]
        st.markdown("##### 시뮬레이션 결과 요약")
        ret_med = (final["p50"] / initial_inv - 1) * 100
        ret_cls = "pos" if ret_med >= 0 else "neg"
        st.markdown(
            f"""<div class='metric-card'>
              <div class='metric-row'><span>초기 투자금</span>
                <span class='neu'>{initial_inv:,.0f}원</span></div>
              <div class='metric-row'>
                <span title="시뮬레이션 하위 5% 결과">최악 시나리오 (5%)</span>
                <span class='neg'>{final["p5"]:,.0f}원</span></div>
              <div class='metric-row'>
                <span title="시뮬레이션 하위 25% 결과">하위 25%</span>
                <span class='warn'>{final["p25"]:,.0f}원</span></div>
              <div class='metric-row'>
                <span title="시뮬레이션 중앙값 (50%)">중앙값 (50%)</span>
                <span class='{ret_cls}'>{final["p50"]:,.0f}원</span></div>
              <div class='metric-row'>
                <span title="시뮬레이션 상위 25% 결과">상위 25%</span>
                <span class='pos'>{final["p75"]:,.0f}원</span></div>
              <div class='metric-row'>
                <span title="시뮬레이션 상위 5% 결과">최선 시나리오 (95%)</span>
                <span class='pos'>{final["p95"]:,.0f}원</span></div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.caption(
            f"{mc_years}년 후 기대 수익률 (중앙값): **{ret_med:+.1f}%**  \n"
            "과거 수익률·변동성 기반 GBM · 미래 보장 아님"
        )


st.divider()
st.caption(
    "© Mean-Variance Portfolio Dashboard · "
    f"Modern Portfolio Theory (Markowitz, 1952) · 무위험금리 {rf_rate*100:.2f}% · "
    f"연 환산 {TRADING_DAYS}영업일 기준"
)
