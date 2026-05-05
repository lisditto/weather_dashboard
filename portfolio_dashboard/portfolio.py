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


def _stats(weights: np.ndarray, mu: np.ndarray, cov: np.ndarray) -> PortfolioStats:
    ret = float(weights @ mu)
    vol = float(np.sqrt(weights @ cov @ weights))
    sharpe = (ret - RISK_FREE_RATE) / vol if vol > 0 else 0.0
    return PortfolioStats(weights=weights, annual_return=ret, annual_vol=vol, sharpe=sharpe)


def portfolio_stats(weights: np.ndarray, prices: pd.DataFrame) -> PortfolioStats:
    rets = daily_returns(prices)
    mu = rets.mean().values * TRADING_DAYS
    cov = rets.cov().values * TRADING_DAYS
    return _stats(np.asarray(weights, dtype=float), mu, cov)


def simulate_frontier(
    prices: pd.DataFrame, n_sims: int = EF_SIMULATIONS, seed: int = 7
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rets = daily_returns(prices)
    mu = rets.mean().values * TRADING_DAYS
    cov = rets.cov().values * TRADING_DAYS
    n_assets = len(mu)

    weights = rng.dirichlet(np.ones(n_assets), size=n_sims)
    port_ret = weights @ mu
    port_vol = np.sqrt(np.einsum("ij,jk,ik->i", weights, cov, weights))
    sharpe = np.where(port_vol > 0, (port_ret - RISK_FREE_RATE) / port_vol, 0.0)

    df = pd.DataFrame(weights, columns=prices.columns)
    df["ret"] = port_ret
    df["vol"] = port_vol
    df["sharpe"] = sharpe
    return df


def optimize(prices: pd.DataFrame, objective: str) -> PortfolioStats:
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
            return -(r - RISK_FREE_RATE) / v if v > 0 else 1e6
        fn = neg
    elif objective == "min_vol":
        fn = lambda w: float(w @ cov @ w)
    else:
        raise ValueError(objective)

    res = minimize(fn, x0, method="SLSQP", bounds=bounds, constraints=constraints)
    return _stats(res.x, mu, cov)
