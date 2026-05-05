"""Static configuration: shadcn/ui zinc · light theme · defaults · constants."""
from __future__ import annotations

# Default starter portfolio shown on first load. Users can edit/add/remove.
DEFAULT_PORTFOLIO: list[dict] = [
    {"ticker": "SPY", "weight": 25.0},
    {"ticker": "TLT", "weight": 25.0},
    {"ticker": "GLD", "weight": 25.0},
    {"ticker": "VNQ", "weight": 25.0},
]

# Per-asset chart palette — Tailwind 600-tier hues with strong contrast on white.
PALETTE: list[str] = [
    "#2563eb",  # blue-600
    "#16a34a",  # green-600
    "#d97706",  # amber-600
    "#db2777",  # pink-600
    "#7c3aed",  # violet-600
    "#0891b2",  # cyan-600
    "#65a30d",  # lime-600
    "#dc2626",  # red-600
]


def color_for(index: int) -> str:
    return PALETTE[index % len(PALETTE)]


# shadcn/ui zinc — light theme (the only theme).
COLORS: dict = {
    "bg": "#ffffff",
    "card": "#ffffff",
    "card_deep": "#fafafa",   # zinc-50  (sidebar surface)
    "divider": "#e4e4e7",     # zinc-200
    "divider_soft": "#f4f4f5",  # zinc-100
    "text": "#09090b",        # zinc-950
    "muted": "#52525b",       # zinc-600 — passes WCAG AA on white
    "stone": "#71717a",       # zinc-500
    "faint": "#3f3f46",       # zinc-700
    "primary": "#18181b",     # zinc-900 — solid black button
    "primary_bright": "#27272a",
    "primary_deep": "#000000",
    "positive": "#16a34a",    # green-600
    "negative": "#dc2626",    # red-600
    "warning": "#d97706",     # amber-600
    "neutral": "#52525b",
    "optimal": "#18181b",
    "min_vol_marker": "#000000",
    "current_marker": "#dc2626",
}

# Backward-compat aliases — both light/dark resolve to the single light palette.
COLORS_LIGHT = COLORS
COLORS_DARK = COLORS

TRADING_DAYS = 252
RISK_FREE_RATE = 0.0
DEFAULT_PERIOD_YEARS = 5
EF_SIMULATIONS = 5000
