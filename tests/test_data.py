"""Tests for the price-fetch layer (synthetic fallback)."""
from __future__ import annotations

import datetime as dt

from portfolio_dashboard import data


def test_synthetic_fallback_returns_data():
    df, source, missing = data.fetch_prices(
        ["AAA", "BBB"],
        dt.date(2023, 1, 1),
        dt.date(2023, 6, 30),
        force_synthetic=True,
    )
    assert source == "synthetic"
    assert missing == []
    assert list(df.columns) == ["AAA", "BBB"]
    assert (df > 0).all().all()


def test_synthetic_is_deterministic():
    a, _, _ = data.fetch_prices(["XYZ"], dt.date(2023, 1, 1), dt.date(2023, 3, 1), force_synthetic=True)
    b, _, _ = data.fetch_prices(["XYZ"], dt.date(2023, 1, 1), dt.date(2023, 3, 1), force_synthetic=True)
    assert a.equals(b)


def test_empty_ticker_list_returns_empty():
    df, _, missing = data.fetch_prices([], dt.date(2023, 1, 1), dt.date(2023, 6, 30))
    assert df.empty
    assert missing == []


def test_normalize_first_row_is_100():
    df, _, _ = data.fetch_prices(["AAA"], dt.date(2023, 1, 1), dt.date(2023, 3, 1), force_synthetic=True)
    norm = data.normalize(df)
    assert abs(norm.iloc[0, 0] - 100.0) < 1e-9


def test_risk_free_rate_returns_plausible():
    rate, source = data.fetch_risk_free_rate(default=0.04)
    assert source in {"yfinance", "default"}
    assert 0.0 <= rate <= 0.25
