"""Static configuration: palette, defaults, constants.

The dashboard now accepts arbitrary tickers from the user; per-asset
metadata (color, label) is built at runtime in app.py from session state.
"""
from __future__ import annotations

# Default starter portfolio shown on first load. Users can edit/add/remove.
DEFAULT_PORTFOLIO: list[dict] = [
    {"ticker": "SPY", "weight": 25.0},
    {"ticker": "TLT", "weight": 25.0},
    {"ticker": "GLD", "weight": 25.0},
    {"ticker": "VNQ", "weight": 25.0},
]

# Revolut accent palette — assigned to assets in order. Cycles if > 8 assets.
PALETTE: list[str] = [
    "#007bc2",  # accent-light-blue
    "#00a87e",  # accent-teal
    "#b09000",  # accent-yellow
    "#e61e49",  # accent-pink
    "#936d62",  # accent-brown
    "#428619",  # accent-light-green
    "#ec7e00",  # accent-warning
    "#4f55f1",  # cobalt-bright (still distinguishable from primary brand stamp)
]


def color_for(index: int) -> str:
    return PALETTE[index % len(PALETTE)]


# Revolut palette — true-black canvas + cobalt-violet accent
COLORS = {
    # Canvas / surface
    "bg": "#000000",
    "card": "#16181a",
    "card_deep": "#0a0a0a",
    "divider": "rgba(255,255,255,0.12)",
    "divider_soft": "rgba(255,255,255,0.06)",
    # Text
    "text": "#ffffff",
    "muted": "rgba(255,255,255,0.72)",
    "stone": "#8d969e",
    "faint": "#c9c9cd",
    # Brand
    "primary": "#494fdf",
    "primary_bright": "#4f55f1",
    "primary_deep": "#3a40c4",
    # Semantic
    "positive": "#00a87e",
    "negative": "#e23b4a",
    "warning": "#ec7e00",
    "neutral": "#8d969e",
    "optimal": "#494fdf",
    "min_vol_marker": "#ffffff",
    "current_marker": "#e61e49",
}

TRADING_DAYS = 252
RISK_FREE_RATE = 0.0
DEFAULT_PERIOD_YEARS = 5
EF_SIMULATIONS = 5000
