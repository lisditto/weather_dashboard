"""Named portfolio presets and curated ETF list for quick-add."""
from __future__ import annotations

# Well-known portfolio recipes. Weights sum to 100.
PRESETS: dict[str, list[dict]] = {
    "Custom": [],  # placeholder — keeps current portfolio
    "60/40 (주식·채권)": [
        {"ticker": "SPY", "weight": 60.0},
        {"ticker": "AGG", "weight": 40.0},
    ],
    "All-Weather (Ray Dalio)": [
        {"ticker": "SPY", "weight": 30.0},
        {"ticker": "TLT", "weight": 40.0},
        {"ticker": "IEF", "weight": 15.0},
        {"ticker": "GLD", "weight": 7.5},
        {"ticker": "DBC", "weight": 7.5},
    ],
    "Permanent Portfolio": [
        {"ticker": "SPY", "weight": 25.0},
        {"ticker": "TLT", "weight": 25.0},
        {"ticker": "GLD", "weight": 25.0},
        {"ticker": "BIL", "weight": 25.0},
    ],
    "Three-Fund (Bogleheads)": [
        {"ticker": "VTI", "weight": 60.0},
        {"ticker": "VXUS", "weight": 30.0},
        {"ticker": "BND", "weight": 10.0},
    ],
    "Golden Butterfly": [
        {"ticker": "VTI", "weight": 20.0},
        {"ticker": "IJS", "weight": 20.0},
        {"ticker": "TLT", "weight": 20.0},
        {"ticker": "SHY", "weight": 20.0},
        {"ticker": "GLD", "weight": 20.0},
    ],
    "한국 KOSPI 대형주": [
        {"ticker": "005930.KS", "weight": 30.0},  # 삼성전자
        {"ticker": "000660.KS", "weight": 20.0},  # SK하이닉스
        {"ticker": "005380.KS", "weight": 15.0},  # 현대차
        {"ticker": "035420.KS", "weight": 20.0},  # NAVER
        {"ticker": "000270.KS", "weight": 15.0},  # 기아
    ],
    "한국·미국 혼합": [
        {"ticker": "SPY", "weight": 40.0},
        {"ticker": "005930.KS", "weight": 20.0},  # 삼성전자
        {"ticker": "035420.KS", "weight": 15.0},  # NAVER
        {"ticker": "035720.KS", "weight": 15.0},  # 카카오
        {"ticker": "GLD", "weight": 10.0},
    ],
}

# Curated quick-add list — common, liquid US-listed ETFs across asset classes.
COMMON_TICKERS: list[tuple[str, str]] = [
    ("SPY", "S&P 500"),
    ("QQQ", "나스닥 100"),
    ("VTI", "미국 전체 주식"),
    ("VXUS", "미국 외 전세계 주식"),
    ("VEA", "선진국 (미국 외)"),
    ("VWO", "신흥국"),
    ("IWM", "Russell 2000 소형주"),
    ("DIA", "다우 30"),
    ("AGG", "미국 종합 채권"),
    ("BND", "미국 종합 채권 (Vanguard)"),
    ("TLT", "장기 미국채 (20+년)"),
    ("IEF", "중기 미국채 (7-10년)"),
    ("SHY", "단기 미국채 (1-3년)"),
    ("BIL", "초단기 T-Bill"),
    ("TIP", "물가연동채"),
    ("HYG", "하이일드 회사채"),
    ("LQD", "투자등급 회사채"),
    ("GLD", "금"),
    ("SLV", "은"),
    ("DBC", "원자재 종합"),
    ("USO", "원유"),
    ("VNQ", "미국 리츠"),
    ("VNQI", "글로벌 리츠"),
    ("BTC-USD", "비트코인"),
    ("ETH-USD", "이더리움"),
    ("^KS11", "코스피 지수"),
    ("^KQ11", "코스닥 지수"),
    ("EWJ", "일본"),
    ("MCHI", "중국"),
    ("INDA", "인도"),
    # ── 한국 KOSPI 대형주 ─────────────────────────────────────────
    ("005930.KS", "삼성전자"),
    ("000660.KS", "SK하이닉스"),
    ("005380.KS", "현대차"),
    ("035420.KS", "NAVER"),
    ("035720.KS", "카카오"),
    ("000270.KS", "기아"),
    ("051910.KS", "LG화학"),
    ("006400.KS", "삼성SDI"),
    ("207940.KS", "삼성바이오로직스"),
    ("105560.KS", "KB금융"),
    ("055550.KS", "신한지주"),
    ("003550.KS", "LG"),
    # ── 한국 KOSDAQ ───────────────────────────────────────────────
    ("247540.KQ", "에코프로비엠"),
    ("086520.KQ", "에코프로"),
    ("196170.KQ", "알테오젠"),
]
