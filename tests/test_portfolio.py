"""Unit tests for portfolio optimization + Monte Carlo."""
from __future__ import annotations

import numpy as np

from portfolio_dashboard import portfolio


def test_portfolio_stats_equal_weights(sample_prices, equal_weights):
    stats = portfolio.portfolio_stats(equal_weights, sample_prices)
    assert stats.annual_vol > 0
    assert isinstance(stats.sharpe, float)
    np.testing.assert_allclose(stats.weights.sum(), 1.0)


def test_simulate_frontier_shape(sample_prices):
    sims = portfolio.simulate_frontier(sample_prices, n_sims=200, seed=1)
    assert len(sims) == 200
    assert {"ret", "vol", "sharpe"}.issubset(sims.columns)
    # Asset weight columns sum to 1 per row.
    asset_cols = [c for c in sims.columns if c not in {"ret", "vol", "sharpe"}]
    np.testing.assert_allclose(sims[asset_cols].sum(axis=1), 1.0, atol=1e-9)


def test_optimize_max_sharpe_beats_random(sample_prices):
    sims = portfolio.simulate_frontier(sample_prices, n_sims=500, seed=2)
    opt = portfolio.optimize(sample_prices, "max_sharpe")
    # Optimised Sharpe should be at least as high as the best random draw
    # (within a small numerical tolerance).
    assert opt.sharpe + 0.05 >= sims["sharpe"].max()


def test_optimize_min_vol_is_lowest(sample_prices):
    opt = portfolio.optimize(sample_prices, "min_vol")
    sims = portfolio.simulate_frontier(sample_prices, n_sims=500, seed=3)
    assert opt.annual_vol <= sims["vol"].min() + 1e-3


def test_forward_monte_carlo_percentile_ordering(sample_prices, equal_weights):
    df = portfolio.forward_monte_carlo(
        sample_prices, equal_weights, years=2, n_sims=200, initial=1_000_000, seed=7,
    )
    # Percentile columns must be monotonically increasing at every horizon.
    cols = ["p5", "p25", "p50", "p75", "p95"]
    vals = df[cols].values
    assert (np.diff(vals, axis=1) >= 0).all()
    # First row should equal initial capital (within float tolerance).
    np.testing.assert_allclose(df.iloc[0].values, 1_000_000, rtol=1e-6)
