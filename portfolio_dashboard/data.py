"""Price data fetching with yfinance, with deterministic synthetic fallback."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

from .config import TICKERS

CACHE_DIR = Path(__file__).resolve().parent.parent / "data_cache"


def _synthetic_prices(start: dt.date, end: dt.date) -> pd.DataFrame:
    """Generate plausible price series when network is unavailable.

    Uses GBM with asset-specific drift/vol so charts look realistic offline.
    """
    rng = np.random.default_rng(42)
    dates = pd.bdate_range(start=start, end=end)
    n = len(dates)

    params = {
        "SPY": (0.10, 0.18, 400.0),
        "TLT": (0.02, 0.15, 95.0),
        "GLD": (0.06, 0.16, 180.0),
        "VNQ": (0.07, 0.20, 85.0),
    }
    out = {}
    for ticker, (mu, sigma, p0) in params.items():
        dt_step = 1 / 252
        shocks = rng.normal((mu - 0.5 * sigma**2) * dt_step, sigma * np.sqrt(dt_step), size=n)
        log_prices = np.log(p0) + np.cumsum(shocks)
        out[ticker] = np.exp(log_prices)
    return pd.DataFrame(out, index=dates)


def fetch_prices(start: dt.date, end: dt.date, *, force_synthetic: bool = False) -> tuple[pd.DataFrame, str]:
    """Fetch adjusted close prices for ALL configured tickers.

    Returns (prices_df, source_label) where source_label ∈ {"yfinance", "synthetic"}.
    """
    if force_synthetic:
        return _synthetic_prices(start, end), "synthetic"

    try:
        import yfinance as yf

        df = yf.download(
            TICKERS,
            start=start.isoformat(),
            end=(end + dt.timedelta(days=1)).isoformat(),
            auto_adjust=True,
            progress=False,
            threads=True,
        )
        if df is None or df.empty:
            raise RuntimeError("empty yfinance response")

        if isinstance(df.columns, pd.MultiIndex):
            close = df["Close"] if "Close" in df.columns.get_level_values(0) else df["Adj Close"]
        else:
            close = df

        close = close[TICKERS].dropna(how="all").ffill().dropna()
        if close.empty:
            raise RuntimeError("no overlapping data after cleaning")
        return close, "yfinance"
    except Exception:
        return _synthetic_prices(start, end), "synthetic"


def normalize(prices: pd.DataFrame) -> pd.DataFrame:
    """Rebase each column so first row = 100."""
    return prices.divide(prices.iloc[0]).multiply(100)
