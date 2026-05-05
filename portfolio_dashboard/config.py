"""Static configuration: palette (shadcn/ui · zinc), defaults, constants.

Uses shadcn/ui design tokens (zinc neutral) for both light and dark themes —
borders define surfaces, no shadows, monochrome primary, semantic colors
for positive/negative/warning. Chart palette is theme-agnostic and uses
distinct hue ramps for legibility against either canvas.
"""
from __future__ import annotations

# Default starter portfolio shown on first load. Users can edit/add/remove.
DEFAULT_PORTFOLIO: list[dict] = [
    {"ticker": "SPY", "weight": 25.0},
    {"ticker": "TLT", "weight": 25.0},
    {"ticker": "GLD", "weight": 25.0},
    {"ticker": "VNQ", "weight": 25.0},
]

# Per-asset chart palette — Tailwind 600-tier hues. Identical in both themes
# (sufficient contrast against #fff and #09090b alike).
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


# shadcn/ui zinc — dark theme
COLORS_DARK: dict = {
    "bg": "#09090b",          # zinc-950
    "card": "#09090b",
    "card_deep": "#0a0a0a",   # sidebar surface (very subtle offset)
    "divider": "#27272a",     # zinc-800
    "divider_soft": "#18181b",  # zinc-900
    "text": "#fafafa",        # zinc-50
    "muted": "#a1a1aa",       # zinc-400
    "stone": "#71717a",       # zinc-500
    "faint": "#52525b",       # zinc-600
    "primary": "#fafafa",     # inverted: white button on dark
    "primary_bright": "#ffffff",
    "primary_deep": "#e4e4e7",
    "positive": "#22c55e",    # green-500
    "negative": "#ef4444",    # red-500
    "warning": "#f59e0b",     # amber-500
    "neutral": "#71717a",
    "optimal": "#fafafa",
    "min_vol_marker": "#a1a1aa",
    "current_marker": "#ef4444",
}

# shadcn/ui zinc — light theme
COLORS_LIGHT: dict = {
    "bg": "#ffffff",
    "card": "#ffffff",
    "card_deep": "#fafafa",   # sidebar
    "divider": "#e4e4e7",     # zinc-200
    "divider_soft": "#f4f4f5",  # zinc-100
    "text": "#09090b",        # zinc-950
    "muted": "#52525b",       # zinc-600 — passes WCAG AA on white
    "stone": "#71717a",       # zinc-500
    "faint": "#3f3f46",       # zinc-700
    "primary": "#18181b",     # zinc-900 — black button
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

# Default theme reference (legacy alias used by charts module init)
COLORS = COLORS_DARK

TRADING_DAYS = 252
RISK_FREE_RATE = 0.0
DEFAULT_PERIOD_YEARS = 5
EF_SIMULATIONS = 5000

TRADING_DAYS = 252
RISK_FREE_RATE = 0.0
DEFAULT_PERIOD_YEARS = 5
EF_SIMULATIONS = 5000
