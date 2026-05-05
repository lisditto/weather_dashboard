"""Per-asset statistics and correlation."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import RISK_FREE_RATE, TRADING_DAYS


def daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pct_change().dropna(how="all")


def annualized_return(returns: pd.Series | pd.DataFrame) -> pd.Series | float:
    return returns.mean() * TRADING_DAYS


def annualized_vol(returns: pd.Series | pd.DataFrame) -> pd.Series | float:
    return returns.std() * np.sqrt(TRADING_DAYS)


def sharpe_ratio(returns: pd.DataFrame, rf: float = RISK_FREE_RATE) -> pd.Series:
    return (annualized_return(returns) - rf) / annualized_vol(returns)


def max_drawdown(prices: pd.DataFrame) -> pd.Series:
    """MDD as a negative number (worst peak-to-trough)."""
    running_max = prices.cummax()
    drawdown = prices / running_max - 1.0
    return drawdown.min()


def drawdown_series(prices: pd.Series) -> pd.Series:
    return prices / prices.cummax() - 1.0


def asset_summary(prices: pd.DataFrame) -> pd.DataFrame:
    rets = daily_returns(prices)
    return pd.DataFrame(
        {
            "annual_return": annualized_return(rets),
            "annual_vol": annualized_vol(rets),
            "sharpe": sharpe_ratio(rets),
            "mdd": max_drawdown(prices),
        }
    )


def correlation(prices: pd.DataFrame) -> pd.DataFrame:
    return daily_returns(prices).corr()


# ── New analytics ─────────────────────────────────────────────────────────────

def portfolio_daily_returns(prices: pd.DataFrame, weights: np.ndarray) -> pd.Series:
    """Daily P&L of the portfolio given fixed weights."""
    return (daily_returns(prices) * weights).sum(axis=1)


def rolling_metrics(
    prices: pd.DataFrame,
    weights: np.ndarray,
    vol_window: int = 63,
    sharpe_window: int = 252,
) -> pd.DataFrame:
    """Rolling annualised volatility (63d) and Sharpe ratio (252d)."""
    port_ret = portfolio_daily_returns(prices, weights)
    roll_vol = port_ret.rolling(vol_window).std() * np.sqrt(TRADING_DAYS)
    ann_ret = port_ret.rolling(sharpe_window).mean() * TRADING_DAYS
    ann_vol_r = port_ret.rolling(sharpe_window).std() * np.sqrt(TRADING_DAYS)
    with np.errstate(invalid="ignore", divide="ignore"):
        roll_sharpe = np.where(ann_vol_r > 0, (ann_ret - RISK_FREE_RATE) / ann_vol_r, np.nan)
    return pd.DataFrame(
        {"rolling_vol": roll_vol, "rolling_sharpe": roll_sharpe},
        index=port_ret.index,
    )


def var_cvar(
    prices: pd.DataFrame,
    weights: np.ndarray,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Historical VaR and CVaR returned as positive loss fractions."""
    port_ret = portfolio_daily_returns(prices, weights)
    threshold = float(np.percentile(port_ret, (1 - confidence) * 100))
    var = -threshold
    tail = port_ret[port_ret <= threshold]
    cvar = float(-tail.mean()) if len(tail) > 0 else var
    return var, cvar


def rebalance_backtest(
    prices: pd.DataFrame,
    weights: np.ndarray,
) -> dict[str, pd.Series]:
    """Normalised cumulative value for buy-and-hold vs three rebalancing freqs."""
    results: dict[str, pd.Series] = {}

    # Buy & Hold — never trade after day 0
    shares = weights / prices.iloc[0].values
    bah = pd.Series((prices.values * shares).sum(axis=1), index=prices.index)
    results["매수 후 보유"] = bah / bah.iloc[0]

    for freq, label in [("ME", "월간 리밸런싱"), ("QE", "분기 리밸런싱"), ("YE", "연간 리밸런싱")]:
        s = _sim_rebalance(prices, weights, freq)
        results[label] = s / s.iloc[0]

    return results


def _sim_rebalance(prices: pd.DataFrame, weights: np.ndarray, freq: str) -> pd.Series:
    rebal_set = set(prices.resample(freq).last().index)
    shares = weights / prices.iloc[0].values
    out = np.empty(len(prices))
    for i in range(len(prices)):
        row = prices.iloc[i].values
        pv = float((shares * row).sum())
        out[i] = pv
        if prices.index[i] in rebal_set and i > 0:
            shares = (weights * pv) / row
    return pd.Series(out, index=prices.index)
