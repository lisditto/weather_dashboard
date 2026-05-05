"""Static configuration: assets, colors, defaults."""
from __future__ import annotations

ASSETS: dict[str, dict[str, str]] = {
    "SPY": {"name": "S&P 500 ETF", "category": "주식", "icon": "📈", "color": "#1565C0", "inception": "1993-01-22"},
    "TLT": {"name": "20+ Year Treasury Bond ETF", "category": "채권", "icon": "🏦", "color": "#2E7D32", "inception": "2002-07-22"},
    "GLD": {"name": "Gold ETF", "category": "금", "icon": "🥇", "color": "#F9A825", "inception": "2004-11-18"},
    "VNQ": {"name": "US REIT ETF", "category": "부동산", "icon": "🏢", "color": "#6A1B9A", "inception": "2004-09-29"},
}

EARLIEST_COMMON_DATE = "2004-11-18"
EARLIEST_PICKABLE = "1993-01-01"

TICKERS: list[str] = list(ASSETS.keys())

COLORS = {
    "bg": "#0F1117",
    "card": "#1E2130",
    "divider": "#2D3250",
    "text": "#FAFAFA",
    "muted": "#9E9E9E",
    "positive": "#2E7D32",
    "negative": "#C62828",
    "warning": "#F57C00",
    "neutral": "#455A64",
    "optimal": "#FFD600",
}

TRADING_DAYS = 252
RISK_FREE_RATE = 0.0
DEFAULT_PERIOD_YEARS = 5
EF_SIMULATIONS = 5000
