"""평균-분산 기반 투자 포트폴리오 분석 대시보드.

사용자가 직접 티커와 비중을 입력하여 자신의 포트폴리오를 분석할 수 있습니다.
Run: streamlit run app.py
"""
from __future__ import annotations

import datetime as dt
import io
import textwrap

import numpy as np
import pandas as pd
import streamlit as st

from portfolio_dashboard import analysis, charts, data, portfolio
from portfolio_dashboard.config import (
    COLORS_DARK,
    COLORS_LIGHT,
    DEFAULT_PERIOD_YEARS,
    DEFAULT_PORTFOLIO,
    EF_SIMULATIONS,
    TRADING_DAYS,
    color_for,
)

st.set_page_config(
    page_title="포트폴리오 분석 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------- Theme-aware CSS builder ----------------------------------------
def _build_css(C: dict) -> str:
    return textwrap.dedent(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@500;600;700&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"], .stApp, .stMarkdown, p, span, div, li, label {{
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  letter-spacing: 0.16px;
}}
.stApp {{ background-color: {C['bg']}; color: {C['text']}; }}
h1, h2, h3, h4, .display {{
  font-family: 'Manrope', 'Inter', sans-serif !important;
  font-weight: 500 !important;
  color: {C['text']};
}}
h1 {{ font-size: 56px !important; line-height: 1.0 !important; letter-spacing: -0.04em !important; font-weight: 500 !important; margin-bottom: 12px !important; }}
h2 {{ font-size: 32px !important; line-height: 1.19 !important; letter-spacing: -0.01em !important; font-weight: 500 !important; }}
h3 {{ font-size: 22px !important; line-height: 1.33 !important; font-weight: 500 !important; }}
h4, h5, h6 {{ font-size: 18px !important; line-height: 1.4 !important; font-weight: 500 !important; }}

.metric-card {{
  background: {C['card']};
  border: 1px solid {C['divider']};
  border-radius: 20px;
  padding: 24px 26px;
  height: 100%;
}}
.metric-card h3 {{ margin: 0 0 4px 0; font-size: 24px !important; font-weight: 500 !important; letter-spacing: -0.01em; }}
.metric-card .sub {{ color: {C['muted']}; font-size: 13px; margin-bottom: 14px; letter-spacing: 0; }}
.metric-row {{
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-top: 1px solid {C['divider_soft']};
  font-size: 14px;
  letter-spacing: 0.16px;
}}
.metric-row span:first-child {{ color: {C['muted']}; cursor: default; }}
.metric-row span[title]:first-child {{ border-bottom: 1px dotted {C['stone']}; }}
.pos {{ color: {C['positive']}; font-weight: 600; }}
.neg {{ color: {C['negative']}; font-weight: 600; }}
.neu {{ color: {C['text']}; font-weight: 600; }}
.warn {{ color: {C['warning']}; font-weight: 600; }}

.badge {{
  display: inline-block;
  padding: 4px 12px;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.16px;
  margin-top: 10px;
}}
.badge-good {{ background: rgba(0,168,126,0.18); color: {C['positive']}; }}
.badge-mid  {{ background: rgba(236,126,0,0.18);  color: {C['warning']}; }}
.badge-bad  {{ background: rgba(226,59,74,0.20);   color: {C['negative']}; }}

.stButton > button, .stDownloadButton > button {{
  background-color: {C['text']} !important;
  color: {C['bg']} !important;
  border: none !important;
  border-radius: 9999px !important;
  font-family: 'Inter', sans-serif !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  letter-spacing: 0.16px !important;
  height: 44px !important;
  padding: 10px 20px !important;
  transition: background 120ms ease;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
  background-color: {C['faint']} !important;
  color: {C['bg']} !important;
}}

[data-baseweb="slider"] [role="slider"] {{
  background-color: {C['primary']} !important;
  border-color: {C['primary']} !important;
}}
[data-baseweb="slider"] > div > div > div {{ background-color: {C['primary']} !important; }}

section[data-testid="stSidebar"] {{
  background-color: {C['card_deep']};
  border-right: 1px solid {C['divider']};
}}
section[data-testid="stSidebar"] .stButton > button {{
  height: 36px !important;
  padding: 6px 14px !important;
  font-size: 13px !important;
}}

.stDateInput input, .stTextInput input, .stNumberInput input {{
  background-color: {C['card']} !important;
  color: {C['text']} !important;
  border: 1px solid {C['divider']} !important;
  border-radius: 12px !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 16px !important;
  letter-spacing: 0.24px !important;
}}

hr {{ border-color: {C['divider']} !important; margin: 32px 0 !important; }}

.stCaption, [data-testid="stCaptionContainer"], small {{
  color: {C['muted']} !important;
  font-size: 13px !important;
}}

.stAlert {{ border-radius: 12px !important; border: 1px solid {C['divider']} !important; }}

[data-testid="stDataFrame"] {{
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid {C['divider']};
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
if "theme" not in st.session_state:
    st.session_state.theme = "dark"


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
                st.toast("🔗 공유 링크에서 포트폴리오를 불러왔습니다.", icon="✅")
        except Exception:
            pass
    st.session_state.url_loaded = True


# ---------- Active theme & CSS injection -----------------------------------
C = COLORS_DARK if st.session_state.theme == "dark" else COLORS_LIGHT
charts.set_theme(C)
st.html(_build_css(C))


# ---------- Mobile layout helper -------------------------------------------
def _cols(*ratios: float) -> list:
    """Return st.columns in desktop mode, or stacked containers in mobile mode."""
    if st.session_state.get("mobile_mode", False):
        return [st.container() for _ in ratios]
    return st.columns(list(ratios))


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


@st.cache_data(show_spinner="EF 시뮬레이션 중…", ttl=60 * 30)
def cached_simulate(prices_csv: str, n: int) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(prices_csv), index_col=0, parse_dates=True)
    return portfolio.simulate_frontier(df, n_sims=n)


@st.cache_data(show_spinner="리밸런싱 시뮬레이션 중…", ttl=60 * 30)
def cached_rebalance(prices_csv: str, weights_str: str) -> dict[str, list]:
    df = pd.read_csv(io.StringIO(prices_csv), index_col=0, parse_dates=True)
    w = np.array([float(x) for x in weights_str.split(",")])
    raw = analysis.rebalance_backtest(df, w)
    return {k: (list(v.index.astype(str)), list(v.values)) for k, v in raw.items()}


@st.cache_data(show_spinner="몬테카를로 시뮬레이션 중…", ttl=60 * 30)
def cached_forward_mc(prices_csv: str, weights_str: str, years: int, initial: float) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(prices_csv), index_col=0, parse_dates=True)
    w = np.array([float(x) for x in weights_str.split(",")])
    return portfolio.forward_monte_carlo(df, w, years=years, n_sims=500, initial=initial)


# ---------- Sidebar -----------------------------------------------------------
with st.sidebar:
    # ── 화면 설정 ──────────────────────────────────────────────────────────
    _is_dark = st.session_state.theme == "dark"
    _new_dark = st.toggle(
        "🌙 다크 모드",
        value=_is_dark,
        key="theme_toggle",
        help="다크/라이트 테마를 전환합니다",
    )
    if _new_dark != _is_dark:
        st.session_state.theme = "dark" if _new_dark else "light"
        st.rerun()

    mobile_mode = st.toggle(
        "📱 모바일 모드",
        value=st.session_state.get("mobile_mode", False),
        key="mobile_toggle",
        help="좁은 화면에서 섹션을 세로로 쌓습니다",
    )
    st.session_state.mobile_mode = mobile_mode

    st.divider()

    # ── 포트폴리오 편집 ───────────────────────────────────────────────────
    st.markdown("### 💼 내 포트폴리오")
    st.caption("티커와 비중을 입력하세요 (예: AAPL, BTC-USD, 005930.KS)")

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
            if st.button("✕", key=f"rm_{i}", help="삭제", use_container_width=True):
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
    if bc1.button("＋ 종목 추가", use_container_width=True):
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
        st.caption(f"✅ 비중 합계 {total_weight:.1f}%")
    else:
        st.caption(f"⚠️ 비중 합계 {total_weight:.1f}% — 자동 정규화하여 계산")

    # 공유 링크
    _share_p = ",".join(
        f"{a['ticker']}:{a['weight']:.1f}"
        for a in st.session_state.portfolio if a["ticker"]
    )
    if st.button("🔗 공유 링크", use_container_width=True, help="이 포트폴리오를 URL로 공유"):
        st.session_state.show_share = not st.session_state.get("show_share", False)
    if st.session_state.get("show_share") and _share_p:
        st.code(f"?p={_share_p}", language=None)
        st.caption("URL 뒤에 붙여넣으면 동일 포트폴리오로 열립니다")

    st.divider()

    # ── 분석 기간 ─────────────────────────────────────────────────────────
    st.markdown("### 📅 분석 기간")
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
    st.markdown("### 📊 벤치마크 비교")
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
    st.markdown("### 🔮 미래 시뮬레이션")
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
    st.warning("👈 사이드바에서 분석할 종목 티커를 1개 이상 입력하세요.")
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
    bench_color_map = {bench_ticker: C["stone"]}
    bench_tickers_set: set[str] = {bench_ticker}
else:
    bench_aligned = pd.DataFrame()
    bench_color_map = {}
    bench_tickers_set = set()

returns = analysis.daily_returns(prices)
summary = analysis.asset_summary(prices)
corr = analysis.correlation(prices)
w_array = np.array([norm_w[t] for t in tickers])
stats = portfolio.portfolio_stats(w_array, prices)


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
    st.warning(
        f"⚠️ 다음 티커는 데이터를 가져올 수 없어 제외되었습니다: **{', '.join(missing)}**. "
        f"오타이거나 상장폐지/거래정지된 종목일 수 있습니다."
    )
if (actual_start - start_date).days > 30:
    st.info(
        f"ℹ️ 일부 자산의 상장일이 늦어 실제 분석 시작일은 **{actual_start}** 입니다. "
        f"(여러 자산의 공통 데이터 구간 자동 적용)"
    )
st.divider()


# ---------- SECTION 1 + 2 ---------------------------------------------------
sec1, sec2 = _cols(1.1, 1)

with sec1:
    st.subheader("1️⃣ 자산 현황")
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
    st.subheader("2️⃣ 상관관계 분석")
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

    with st.expander("📖 용어 설명"):
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
st.subheader("3️⃣ 포트폴리오 분석")

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
            <span>{'🟢 우수' if stats.sharpe >= 1 else '🟠 보통' if stats.sharpe >= 0.5 else '🔴 낮음'}</span></div>
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
    eq_stats = portfolio.portfolio_stats(eq_w, prices)
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
    st.download_button(
        "📥 분석 결과 CSV 다운로드", csv_bytes,
        file_name="portfolio_analysis.csv", mime="text/csv",
        use_container_width=True,
    )

st.divider()


# ---------- SECTION 4: 포트폴리오 구성 추천 --------------------------------
with st.expander("4️⃣ 포트폴리오 구성 추천 (Efficient Frontier)", expanded=True):
    if len(tickers) >= 2:
        sims = cached_simulate(prices.to_csv(), n_sims)
        max_sharpe_opt = portfolio.optimize(prices, "max_sharpe")
        min_vol_opt = portfolio.optimize(prices, "min_vol")

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
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.markdown(
                f"- 🟡 **최대 샤프**: 수익률 {max_sharpe_opt.annual_return*100:+.2f}% / "
                f"변동성 {max_sharpe_opt.annual_vol*100:.2f}% / 샤프 {max_sharpe_opt.sharpe:.3f}\n"
                f"- 💎 **최소 변동성**: 수익률 {min_vol_opt.annual_return*100:+.2f}% / "
                f"변동성 {min_vol_opt.annual_vol*100:.2f}% / 샤프 {min_vol_opt.sharpe:.3f}\n"
                f"- 🟠 **현재**: 수익률 {stats.annual_return*100:+.2f}% / "
                f"변동성 {stats.annual_vol*100:.2f}% / 샤프 {stats.sharpe:.3f}"
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
with st.expander("5️⃣ 롤링 지표", expanded=False):
    rolling_df = analysis.rolling_metrics(prices, w_array)
    st.plotly_chart(charts.rolling_metrics_chart(rolling_df), use_container_width=True)
    st.caption(
        "롤링 변동성: 63영업일(약 3개월) 기준 연환산 · "
        "롤링 샤프: 252영업일(1년) 기준 · 점선 = 0 및 샤프 1.0 기준선"
    )


# ---------- SECTION 6: 리밸런싱 시뮬레이션 ----------------------------------
with st.expander("6️⃣ 리밸런싱 시뮬레이션", expanded=False):
    rb_raw = cached_rebalance(prices.to_csv(), ",".join(str(x) for x in w_array))
    rb_strategies = {
        k: pd.Series(vals, index=pd.to_datetime(dates))
        for k, (dates, vals) in rb_raw.items()
    }
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
        st.dataframe(pd.DataFrame(rb_rows), hide_index=True, use_container_width=True)
        st.caption("동일 자산·기간·비중, 리밸런싱 주기만 다르게 비교합니다.")


# ---------- SECTION 7: 미래 가치 시뮬레이션 ---------------------------------
with st.expander("7️⃣ 미래 가치 시뮬레이션", expanded=False):
    mc_df = cached_forward_mc(
        prices.to_csv(), ",".join(str(x) for x in w_array),
        mc_years, float(initial_inv),
    )
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
    f"Modern Portfolio Theory (Markowitz, 1952) · 무위험금리 0% 가정 · "
    f"연 환산 {TRADING_DAYS}영업일 기준"
)
