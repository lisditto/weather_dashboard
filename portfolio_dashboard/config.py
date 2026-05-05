"""Static configuration: assets, colors, defaults.

Color system follows the Revolut design language:
- True-black canvas (#000000) with surface-elevated dark cards (#16181a).
- Cobalt-violet (#494fdf) reserved for primary brand stamps.
- Asset colors mapped to the Revolut accent palette.
"""
from __future__ import annotations

ASSETS: dict[str, dict[str, str]] = {
    "SPY": {"name": "S&P 500 ETF", "category": "주식", "icon": "📈",
            "color": "#007bc2", "inception": "1993-01-22"},      # accent-light-blue
    "TLT": {"name": "20+ Year Treasury Bond ETF", "category": "채권", "icon": "🏦",
            "color": "#00a87e", "inception": "2002-07-22"},      # accent-teal
    "GLD": {"name": "Gold ETF", "category": "금", "icon": "🥇",
            "color": "#b09000", "inception": "2004-11-18"},      # accent-yellow
    "VNQ": {"name": "US REIT ETF", "category": "부동산", "icon": "🏢",
            "color": "#e61e49", "inception": "2004-09-29"},      # accent-pink
}

EARLIEST_COMMON_DATE = "2004-11-18"
EARLIEST_PICKABLE = "1993-01-01"

TICKERS: list[str] = list(ASSETS.keys())

# Revolut palette — true-black canvas + cobalt-violet accent
COLORS = {
    # Canvas / surface
    "bg": "#000000",                       # canvas-dark
    "card": "#16181a",                     # surface-elevated
    "card_deep": "#0a0a0a",                # surface-deep
    "divider": "rgba(255,255,255,0.12)",   # hairline-dark
    "divider_soft": "rgba(255,255,255,0.06)",
    # Text
    "text": "#ffffff",                     # on-dark
    "muted": "rgba(255,255,255,0.72)",     # on-dark-mute
    "stone": "#8d969e",
    "faint": "#c9c9cd",
    # Brand
    "primary": "#494fdf",                  # cobalt violet
    "primary_bright": "#4f55f1",
    "primary_deep": "#3a40c4",
    # Semantic (Revolut accent palette)
    "positive": "#00a87e",                 # accent-teal
    "negative": "#e23b4a",                 # accent-danger
    "warning": "#ec7e00",                  # accent-warning
    "neutral": "#8d969e",
    "optimal": "#494fdf",                  # primary cobalt for optimal portfolio
    "min_vol_marker": "#ffffff",           # white pill on dark for contrast
    "current_marker": "#e61e49",           # accent-pink for "you are here"
}

TRADING_DAYS = 252
RISK_FREE_RATE = 0.0
DEFAULT_PERIOD_YEARS = 5
EF_SIMULATIONS = 5000
