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
