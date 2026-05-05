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
    COLORS,
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


# ---------- Custom CSS — Revolut design language ----------------------------
_CSS = textwrap.dedent(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@500;600;700&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"], .stApp, .stMarkdown, p, span, div, li, label {{
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  letter-spacing: 0.16px;
}}
.stApp {{ background-color: {COLORS['bg']}; color: {COLORS['text']}; }}
h1, h2, h3, h4, .display {{
  font-family: 'Manrope', 'Inter', sans-serif !important;
  font-weight: 500 !important;
  color: {COLORS['text']};
}}
h1 {{ font-size: 56px !important; line-height: 1.0 !important; letter-spacing: -0.04em !important; font-weight: 500 !important; margin-bottom: 12px !important; }}
h2 {{ font-size: 32px !important; line-height: 1.19 !important; letter-spacing: -0.01em !important; font-weight: 500 !important; }}
h3 {{ font-size: 22px !important; line-height: 1.33 !important; font-weight: 500 !important; }}
h4, h5, h6 {{ font-size: 18px !important; line-height: 1.4 !important; font-weight: 500 !important; }}

.metric-card {{
  background: {COLORS['card']};
  border: 1px solid {COLORS['divider']};
  border-radius: 20px;
  padding: 24px 26px;
  height: 100%;
}}
.metric-card h3 {{ margin: 0 0 4px 0; font-size: 24px !important; font-weight: 500 !important; letter-spacing: -0.01em; }}
.metric-card .sub {{ color: {COLORS['muted']}; font-size: 13px; margin-bottom: 14px; letter-spacing: 0; }}
.metric-row {{
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-top: 1px solid {COLORS['divider_soft']};
  font-size: 14px;
  letter-spacing: 0.16px;
}}
.metric-row span:first-child {{ color: {COLORS['muted']}; }}
.pos {{ color: {COLORS['positive']}; font-weight: 600; }}
.neg {{ color: {COLORS['negative']}; font-weight: 600; }}
.neu {{ color: {COLORS['text']}; font-weight: 600; }}
.warn {{ color: {COLORS['warning']}; font-weight: 600; }}

.badge {{
  display: inline-block;
  padding: 4px 12px;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.16px;
  margin-top: 10px;
}}
.badge-good {{ background: rgba(0,168,126,0.18); color: {COLORS['positive']}; }}
.badge-mid  {{ background: rgba(236,126,0,0.18); color: {COLORS['warning']}; }}
.badge-bad  {{ background: rgba(226,59,74,0.20); color: {COLORS['negative']}; }}

.source-pill {{
  background: {COLORS['card']};
  color: {COLORS['muted']};
  padding: 6px 14px;
  border-radius: 9999px;
  font-size: 13px;
  font-weight: 500;
  border: 1px solid {COLORS['divider']};
}}

.stButton > button, .stDownloadButton > button {{
  background-color: {COLORS['text']} !important;
  color: {COLORS['bg']} !important;
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
  background-color: {COLORS['faint']} !important;
  color: {COLORS['bg']} !important;
}}

[data-baseweb="slider"] [role="slider"] {{
  background-color: {COLORS['primary']} !important;
  border-color: {COLORS['primary']} !important;
}}
[data-baseweb="slider"] > div > div > div {{ background-color: {COLORS['primary']} !important; }}

section[data-testid="stSidebar"] {{
  background-color: {COLORS['card_deep']};
  border-right: 1px solid {COLORS['divider']};
}}
section[data-testid="stSidebar"] .stButton > button {{
  height: 36px !important;
  padding: 6px 14px !important;
  font-size: 13px !important;
}}

.stDateInput input, .stTextInput input, .stNumberInput input {{
  background-color: {COLORS['card']} !important;
  color: {COLORS['text']} !important;
  border: 1px solid {COLORS['divider']} !important;
  border-radius: 12px !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 16px !important;
  letter-spacing: 0.24px !important;
}}

hr {{ border-color: {COLORS['divider']} !important; margin: 32px 0 !important; }}

.stCaption, [data-testid="stCaptionContainer"], small {{
  color: {COLORS['muted']} !important;
  font-size: 13px !important;
}}

.stAlert {{ border-radius: 12px !important; border: 1px solid {COLORS['divider']} !important; }}

[data-testid="stDataFrame"] {{
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid {COLORS['divider']};
}}

.hero-strip {{
  font-family: 'Manrope', sans-serif;
  font-weight: 500;
  font-size: 13px;
  letter-spacing: 0.24px;
  color: {COLORS['muted']};
  text-transform: uppercase;
  margin-bottom: 8px;
}}
</style>
""").strip()
st.html(_CSS)


# ---------- Session state init ---------------------------------------------
if "portfolio" not in st.session_state:
    st.session_state.portfolio = [dict(a) for a in DEFAULT_PORTFOLIO]
if "period_start" not in st.session_state:
    st.session_state.period_start = dt.date.today() - dt.timedelta(days=365 * DEFAULT_PERIOD_YEARS)
if "period_end" not in st.session_state:
    st.session_state.period_end = dt.date.today()


def _reset_row_widgets() -> None:
    """Clear all per-row widget keys so they reinitialize from portfolio dict.

    Streamlit forbids writing to a widget's session_state key after the
    widget has been instantiated. To programmatically change a value
    (e.g. after "균등 배분" or "최대 샤프 적용"), we delete the keys and
    rerun — the widgets repopulate from the underlying portfolio list.
    """
    for k in list(st.session_state.keys()):
        if k.startswith("t_") or k.startswith("w_") or k.startswith("rm_"):
            del st.session_state[k]


# ---------- Sidebar: portfolio editor + period --------------------------
with st.sidebar:
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
        # Color preview bar
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

    st.divider()
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
    n_sims = st.slider("EF 시뮬레이션 수", 1000, 20000, EF_SIMULATIONS, step=1000)


# ---------- Resolve user portfolio ------------------------------------------
valid_assets = [a for a in st.session_state.portfolio if a["ticker"]]
tickers = [a["ticker"] for a in valid_assets]
raw_weights = {a["ticker"]: a["weight"] for a in valid_assets}

if not tickers:
    st.warning("👈 사이드바에서 분석할 종목 티커를 1개 이상 입력하세요.")
    st.stop()


# ---------- Data load (cached) ---------------------------------------------
@st.cache_data(show_spinner="가격 데이터를 불러오는 중…", ttl=60 * 30)
def load_prices(tickers_tuple: tuple, start: dt.date, end: dt.date, force_synth: bool):
    return data.fetch_prices(list(tickers_tuple), start, end, force_synthetic=force_synth)


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

# Color map by user's input order
color_map = {t: color_for(i) for i, t in enumerate(tickers)}

returns = analysis.daily_returns(prices)
summary = analysis.asset_summary(prices)
corr = analysis.correlation(prices)


# ---------- Header ----------------------------------------------------------
hdr_left, hdr_right = st.columns([3, 1])
with hdr_left:
    st.markdown("<div class='hero-strip'>Mean-Variance · Modern Portfolio Theory</div>",
                unsafe_allow_html=True)
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
with hdr_right:
    label = "Yahoo Finance 실데이터" if source == "yfinance" else "합성 샘플 데이터"
    st.markdown(
        f"<div style='text-align:right;margin-top:14px'>"
        f"<span class='source-pill'>📡 {label}</span></div>",
        unsafe_allow_html=True,
    )

st.divider()


# ---------- SECTION 1 + 2 ---------------------------------------------------
sec1, sec2 = st.columns([1.1, 1])

with sec1:
    st.subheader("1️⃣ 자산 현황")
    n_cols = 2 if len(tickers) >= 2 else 1
    cards = st.columns(n_cols)
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

        with cards[idx % n_cols]:
            st.markdown(
                f"""
                <div class='metric-card'>
                  <h3 style='color:{color_map[ticker]}'>{ticker}</h3>
                  <div class='sub'>비중 {norm_w[ticker]*100:.1f}%</div>
                  <div class='metric-row'><span>연 수익률</span><span class='{ret_cls}'>{ret_pct:+.2f}%</span></div>
                  <div class='metric-row'><span>연 변동성</span><span class='neu'>{vol_pct:.2f}%</span></div>
                  <div class='metric-row'><span>샤프 지수</span><span class='{sharpe_cls}'>{sharpe:.2f}</span></div>
                  <div class='metric-row'><span>최대 낙폭(MDD)</span><span class='neg'>{mdd_pct:.2f}%</span></div>
                  {badge}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("&nbsp;", unsafe_allow_html=True)
    st.plotly_chart(
        charts.price_line_chart(data.normalize(prices), returns, color_map),
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

st.divider()


# ---------- SECTION 3: 포트폴리오 비중 분석 ---------------------------------
st.subheader("3️⃣ 포트폴리오 분석")

col_donut, col_metrics = st.columns([1.1, 1])

w_array = np.array([norm_w[t] for t in tickers])
stats = portfolio.portfolio_stats(w_array, prices)

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
    st.markdown(
        f"""
        <div class='metric-card'>
          <div class='metric-row'><span>연 기대수익률</span><span class='{cls}'>{ret_pct:+.2f}%</span></div>
          <div class='metric-row'><span>연 변동성</span><span class='neu'>{vol_pct:.2f}%</span></div>
          <div class='metric-row'><span>샤프 지수</span><span class='{sharpe_cls}'>{stats.sharpe:.3f}</span></div>
          <div class='metric-row'><span>샤프 평가</span>
            <span>{ '🟢 우수' if stats.sharpe >= 1 else '🟠 보통' if stats.sharpe >= 0.5 else '🔴 낮음' }</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    eq_w = np.full(len(tickers), 1 / len(tickers))
    eq_stats = portfolio.portfolio_stats(eq_w, prices)
    delta_ret = (stats.annual_return - eq_stats.annual_return) * 100
    delta_vol = (stats.annual_vol - eq_stats.annual_vol) * 100
    st.caption(f"균등 비중 대비 수익률 {delta_ret:+.2f}%p · 변동성 {delta_vol:+.2f}%p")

st.divider()


# ---------- SECTION 4: Efficient Frontier ----------------------------------
st.subheader("4️⃣ Efficient Frontier")

if len(tickers) >= 2:
    @st.cache_data(show_spinner="EF 시뮬레이션 중…", ttl=60 * 30)
    def cached_simulate(prices_csv: str, n: int) -> pd.DataFrame:
        df = pd.read_csv(io.StringIO(prices_csv), index_col=0, parse_dates=True)
        return portfolio.simulate_frontier(df, n_sims=n)

    sims = cached_simulate(prices.to_csv(), n_sims)
    max_sharpe_opt = portfolio.optimize(prices, "max_sharpe")
    min_vol_opt = portfolio.optimize(prices, "min_vol")

    current_point = {"vol": stats.annual_vol, "ret": stats.annual_return, "sharpe": stats.sharpe}
    max_point = {"vol": max_sharpe_opt.annual_vol, "ret": max_sharpe_opt.annual_return, "sharpe": max_sharpe_opt.sharpe}
    min_point = {"vol": min_vol_opt.annual_vol, "ret": min_vol_opt.annual_return, "sharpe": min_vol_opt.sharpe}

    ef_left, ef_right = st.columns([2, 1])
    with ef_left:
        st.plotly_chart(
            charts.efficient_frontier_scatter(
                sims, current=current_point, max_sharpe=max_point, min_vol=min_point
            ),
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

        st.markdown("##### 요약")
        st.markdown(
            f"""
            - 🟡 **최대 샤프**: 수익률 {max_sharpe_opt.annual_return*100:+.2f}% / 변동성 {max_sharpe_opt.annual_vol*100:.2f}% / 샤프 {max_sharpe_opt.sharpe:.3f}
            - 💎 **최소 변동성**: 수익률 {min_vol_opt.annual_return*100:+.2f}% / 변동성 {min_vol_opt.annual_vol*100:.2f}% / 샤프 {min_vol_opt.sharpe:.3f}
            - 🟠 **현재**: 수익률 {stats.annual_return*100:+.2f}% / 변동성 {stats.annual_vol*100:.2f}% / 샤프 {stats.sharpe:.3f}
            """
        )

        if st.button("최대 샤프 비중 적용", use_container_width=True, key="apply_max"):
            for i, t in enumerate(tickers):
                for j, a in enumerate(st.session_state.portfolio):
                    if a["ticker"] == t:
                        a["weight"] = float(round(max_sharpe_opt.weights[i] * 100, 1))
            _reset_row_widgets()
            st.rerun()
        if st.button("최소 변동성 비중 적용", use_container_width=True, key="apply_min"):
            for i, t in enumerate(tickers):
                for j, a in enumerate(st.session_state.portfolio):
                    if a["ticker"] == t:
                        a["weight"] = float(round(min_vol_opt.weights[i] * 100, 1))
            _reset_row_widgets()
            st.rerun()
else:
    st.info("Efficient Frontier 분석은 자산 2개 이상에서 가능합니다.")

st.divider()
st.caption(
    "© Mean-Variance Portfolio Dashboard · "
    f"Modern Portfolio Theory (Markowitz, 1952) · 무위험금리 0% 가정 · "
    f"연 환산 {TRADING_DAYS}영업일 기준"
)
