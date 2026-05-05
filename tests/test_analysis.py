"""Unit tests for analysis primitives."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from portfolio_dashboard import analysis


def test_daily_returns_drops_first_row(sample_prices):
    rets = analysis.daily_returns(sample_prices)
    assert len(rets) == len(sample_prices) - 1
    assert rets.notna().all().all()


def test_annualized_return_scales_by_252():
    s = pd.Series([0.001] * 100)
    assert analysis.annualized_return(s) == pytest.approx(0.001 * 252)


def test_max_drawdown_is_non_positive(sample_prices):
    mdd = analysis.max_drawdown(sample_prices)
    assert (mdd <= 0).all()


def test_correlation_diagonal_is_one(sample_prices):
    corr = analysis.correlation(sample_prices)
    np.testing.assert_allclose(np.diag(corr.values), 1.0)
    assert corr.shape == (3, 3)


def test_var_cvar_ordering(sample_prices, equal_weights):
    var, cvar = analysis.var_cvar(sample_prices, equal_weights, confidence=0.95)
    # CVaR (tail mean loss) is at least as bad as VaR.
    assert cvar >= var
    assert var > 0  # returned as positive loss fraction


def test_portfolio_daily_returns_matches_weighted_sum(sample_prices, equal_weights):
    rets = analysis.daily_returns(sample_prices)
    expected = (rets * equal_weights).sum(axis=1)
    actual = analysis.portfolio_daily_returns(sample_prices, equal_weights)
    pd.testing.assert_series_equal(actual, expected)


def test_rolling_metrics_columns(sample_prices, equal_weights):
    df = analysis.rolling_metrics(sample_prices, equal_weights)
    assert set(df.columns) == {"rolling_vol", "rolling_sharpe"}
    # First (window-1) values are NaN; later values must be finite where defined.
    assert df["rolling_vol"].dropna().gt(0).all()


def test_rebalance_backtest_starts_at_one(sample_prices, equal_weights):
    out = analysis.rebalance_backtest(sample_prices, equal_weights)
    assert set(out.keys()) == {"매수 후 보유", "월간 리밸런싱", "분기 리밸런싱", "연간 리밸런싱"}
    for series in out.values():
        assert abs(series.iloc[0] - 1.0) < 1e-9
        assert series.notna().all()
