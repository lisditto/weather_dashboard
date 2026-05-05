"""Price data fetching with yfinance, with deterministic synthetic fallback.

Now generic over an arbitrary list of tickers supplied at call time.
"""
from __future__ import annotations

import datetime as dt
import hashlib

import numpy as np
import pandas as pd


def _ticker_seed(ticker: str) -> int:
    """Stable seed per ticker so synthetic series stay consistent across reruns."""
    return int(hashlib.md5(ticker.encode()).hexdigest()[:8], 16)


def _synthetic_prices(
    tickers: list[str], start: dt.date, end: dt.date
) -> pd.DataFrame:
    """Generate plausible price series via GBM with per-ticker deterministic params."""
    dates = pd.bdate_range(start=start, end=end)
    n = len(dates)
    out = {}
    for t in tickers:
        seed = _ticker_seed(t)
        rng = np.random.default_rng(seed)
        # Plausible ranges: drift 2-15%, vol 12-35%, starting price 50-300.
        mu = 0.02 + (seed % 130) / 1000          # 0.02 ~ 0.15
        sigma = 0.12 + (seed % 230) / 1000       # 0.12 ~ 0.35
        p0 = 50 + (seed % 250)                    # 50 ~ 300
        dt_step = 1 / 252
        shocks = rng.normal((mu - 0.5 * sigma**2) * dt_step,
                            sigma * np.sqrt(dt_step), size=n)
        log_prices = np.log(p0) + np.cumsum(shocks)
        out[t] = np.exp(log_prices)
    return pd.DataFrame(out, index=dates)


def fetch_prices(
    tickers: list[str],
    start: dt.date,
    end: dt.date,
    *,
    force_synthetic: bool = False,
) -> tuple[pd.DataFrame, str, list[str]]:
    """Fetch adjusted close for the given tickers.

    Returns
    -------
    prices : DataFrame (ascending Date index, columns = valid tickers)
    source : "yfinance" | "synthetic"
    missing : tickers that returned no data (excluded from result)
    """
    tickers = [t.strip().upper() for t in tickers if t and t.strip()]
    if not tickers:
        return pd.DataFrame(), "synthetic", []

    if force_synthetic:
        return _synthetic_prices(tickers, start, end), "synthetic", []

    try:
        import yfinance as yf

        df = yf.download(
            tickers,
            start=start.isoformat(),
            end=(end + dt.timedelta(days=1)).isoformat(),
            auto_adjust=True,
            progress=False,
            threads=True,
            group_by="column",
        )
        if df is None or df.empty:
            raise RuntimeError("empty yfinance response")

        # Normalize: yfinance returns MultiIndex when multiple tickers, single when one
        if isinstance(df.columns, pd.MultiIndex):
            close = df["Close"] if "Close" in df.columns.get_level_values(0) else df["Adj Close"]
        else:
            close = df[["Close"]] if "Close" in df.columns else df
            if isinstance(close, pd.Series):
                close = close.to_frame(name=tickers[0])
            elif close.shape[1] == 1 and len(tickers) == 1:
                close.columns = [tickers[0]]

        # Align column set to requested tickers; drop those with no usable data
        missing = [t for t in tickers if t not in close.columns]
        present = [t for t in tickers if t in close.columns]
        close = close[present].ffill().dropna(how="all")

        # Drop tickers that ended up entirely NaN
        all_nan = [t for t in close.columns if close[t].isna().all()]
        for t in all_nan:
            missing.append(t)
        close = close.drop(columns=all_nan, errors="ignore")
        # Final intersection — only keep rows where ALL remaining tickers are present
        close = close.dropna()

        if close.empty or close.shape[1] == 0:
            raise RuntimeError("no overlapping data after cleaning")
        return close, "yfinance", sorted(set(missing))
    except Exception:
        return _synthetic_prices(tickers, start, end), "synthetic", []


def normalize(prices: pd.DataFrame) -> pd.DataFrame:
    """Rebase each column so first row = 100."""
    return prices.divide(prices.iloc[0]).multiply(100)
