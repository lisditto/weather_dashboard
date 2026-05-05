"""Shared pytest fixtures."""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_prices() -> pd.DataFrame:
    """Deterministic 3-asset price panel — 252 business days, GBM-ish."""
    rng = np.random.default_rng(42)
    dates = pd.bdate_range(start=dt.date(2023, 1, 2), periods=252)
    returns = rng.normal(0.0004, 0.012, size=(252, 3))
    prices = 100 * np.exp(np.cumsum(returns, axis=0))
    return pd.DataFrame(prices, index=dates, columns=["A", "B", "C"])


@pytest.fixture
def equal_weights() -> np.ndarray:
    return np.array([1 / 3, 1 / 3, 1 / 3])
