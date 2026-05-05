"""Portfolio metrics + Efficient Frontier (Monte Carlo + analytical optima)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from .analysis import daily_returns
from .config import EF_SIMULATIONS, RISK_FREE_RATE, TRADING_DAYS


@dataclass
class PortfolioStats:
    weights: np.ndarray
    annual_return: float
    annual_vol: float
    sharpe: float


def _stats(weights: np.ndarray, mu: np.ndarray, cov: np.ndarray, rf: float = RISK_FREE_RATE) -> PortfolioStats:
    ret = float(weights @ mu)
    vol = float(np.sqrt(weights @ cov @ weights))
    sharpe = (ret - rf) / vol if vol > 0 else 0.0
    return PortfolioStats(weights=weights, annual_return=ret, annual_vol=vol, sharpe=sharpe)


def portfolio_stats(weights: np.ndarray, prices: pd.DataFrame, rf: float = RISK_FREE_RATE) -> PortfolioStats:
    rets = daily_returns(prices)
    mu = rets.mean().values * TRADING_DAYS
    cov = rets.cov().values * TRADING_DAYS
    return _stats(np.asarray(weights, dtype=float), mu, cov, rf=rf)


def simulate_frontier(
    prices: pd.DataFrame, n_sims: int = EF_SIMULATIONS, seed: int = 7, rf: float = RISK_FREE_RATE,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rets = daily_returns(prices)
    mu = rets.mean().values * TRADING_DAYS
    cov = rets.cov().values * TRADING_DAYS
    n_assets = len(mu)

    weights = rng.dirichlet(np.ones(n_assets), size=n_sims)
    port_ret = weights @ mu
    port_vol = np.sqrt(np.einsum("ij,jk,ik->i", weights, cov, weights))
    sharpe = np.where(port_vol > 0, (port_ret - rf) / port_vol, 0.0)

    df = pd.DataFrame(weights, columns=prices.columns)
    df["ret"] = port_ret
    df["vol"] = port_vol
    df["sharpe"] = sharpe
    return df


def optimize(prices: pd.DataFrame, objective: str, rf: float = RISK_FREE_RATE) -> PortfolioStats:
    """objective ∈ {'max_sharpe', 'min_vol'}."""
    rets = daily_returns(prices)
    mu = rets.mean().values * TRADING_DAYS
    cov = rets.cov().values * TRADING_DAYS
    n = len(mu)

    bounds = [(0.0, 1.0)] * n
    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    x0 = np.full(n, 1.0 / n)

    if objective == "max_sharpe":
        def neg(w):
            r = w @ mu
            v = np.sqrt(w @ cov @ w)
            return -(r - rf) / v if v > 0 else 1e6
        fn = neg
    elif objective == "min_vol":
        fn = lambda w: float(w @ cov @ w)
    else:
        raise ValueError(objective)

    res = minimize(fn, x0, method="SLSQP", bounds=bounds, constraints=constraints)
    return _stats(res.x, mu, cov, rf=rf)


def forward_monte_carlo(
    prices: pd.DataFrame,
    weights: np.ndarray,
    years: int = 10,
    n_sims: int = 500,
    initial: float = 10_000_000,
    seed: int = 42,
) -> pd.DataFrame:
    """GBM forward simulation using historical portfolio drift/vol.

    Returns a DataFrame (index = future business dates, columns = p5/p25/p50/p75/p95)
    so callers can draw a fan chart without storing all n_sims paths.
    """
    from .analysis import portfolio_daily_returns

    port_ret = portfolio_daily_returns(prices, weights)
    mu = float(port_ret.mean())
    sigma = float(port_ret.std())
    n_days = int(years * TRADING_DAYS)

    rng = np.random.default_rng(seed)
    rand_rets = rng.normal(mu, sigma, (n_sims, n_days))
    # Cumulative product → each row is one simulated path
    cum = np.cumprod(1 + rand_rets, axis=1) * initial
    cum = np.hstack([np.full((n_sims, 1), initial), cum])  # prepend t=0

    pcts = [5, 25, 50, 75, 95]
    pct_data = np.percentile(cum, pcts, axis=0).T  # shape (n_days+1, 5)

    future_idx = pd.bdate_range(start=prices.index[-1], periods=n_days + 1)
    return pd.DataFrame(pct_data, index=future_idx, columns=[f"p{p}" for p in pcts])
