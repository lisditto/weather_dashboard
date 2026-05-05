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


def asset_summary(prices: pd.DataFrame, rf: float = RISK_FREE_RATE) -> pd.DataFrame:
    rets = daily_returns(prices)
    return pd.DataFrame(
        {
            "annual_return": annualized_return(rets),
            "annual_vol": annualized_vol(rets),
            "sharpe": sharpe_ratio(rets, rf=rf),
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
    rf: float = RISK_FREE_RATE,
) -> pd.DataFrame:
    """Rolling annualised volatility (63d) and Sharpe ratio (252d)."""
    port_ret = portfolio_daily_returns(prices, weights)
    roll_vol = port_ret.rolling(vol_window).std() * np.sqrt(TRADING_DAYS)
    ann_ret = port_ret.rolling(sharpe_window).mean() * TRADING_DAYS
    ann_vol_r = port_ret.rolling(sharpe_window).std() * np.sqrt(TRADING_DAYS)
    with np.errstate(invalid="ignore", divide="ignore"):
        roll_sharpe = np.where(ann_vol_r > 0, (ann_ret - rf) / ann_vol_r, np.nan)
    return pd.DataFrame(
        {"rolling_vol": roll_vol, "rolling_sharpe": roll_sharpe},
        index=port_ret.index,
    )


def regression_stats(
    prices: pd.DataFrame,
    weights: np.ndarray,
    benchmark: pd.Series,
    rf: float = RISK_FREE_RATE,
) -> dict[str, float]:
    """CAPM-style regression of portfolio excess returns on benchmark excess returns.

    Returns alpha (annualised), beta, information ratio (annualised), and R².
    The portfolio and benchmark are aligned on overlapping dates.
    """
    port_ret = portfolio_daily_returns(prices, weights)
    bench_ret = benchmark.pct_change().dropna()
    df = pd.concat([port_ret, bench_ret], axis=1, keys=["p", "b"]).dropna()
    if len(df) < 2:
        return {"alpha": float("nan"), "beta": float("nan"),
                "info_ratio": float("nan"), "r2": float("nan")}

    rf_daily = rf / TRADING_DAYS
    p = df["p"].values - rf_daily
    b = df["b"].values - rf_daily
    var_b = float(np.var(b, ddof=1))
    if var_b <= 0:
        return {"alpha": float("nan"), "beta": float("nan"),
                "info_ratio": float("nan"), "r2": float("nan")}
    cov = float(np.cov(p, b, ddof=1)[0, 1])
    beta = cov / var_b
    alpha_daily = float(np.mean(p) - beta * np.mean(b))
    alpha = alpha_daily * TRADING_DAYS

    active = df["p"].values - df["b"].values
    te = float(np.std(active, ddof=1))
    info_ratio = (float(np.mean(active)) * TRADING_DAYS) / (te * np.sqrt(TRADING_DAYS)) if te > 0 else float("nan")

    corr = float(np.corrcoef(p, b)[0, 1])
    r2 = corr * corr
    return {"alpha": alpha, "beta": beta, "info_ratio": info_ratio, "r2": r2}


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
    cost_bps: float = 0.0,
) -> dict[str, pd.Series]:
    """Normalised cumulative value for buy-and-hold vs three rebalancing freqs.

    cost_bps applies a one-way transaction cost (in basis points of turnover)
    each time the portfolio rebalances. 10 bps = 0.10%.
    """
    results: dict[str, pd.Series] = {}

    # Buy & Hold — never trade after day 0
    shares = weights / prices.iloc[0].values
    bah = pd.Series((prices.values * shares).sum(axis=1), index=prices.index)
    results["매수 후 보유"] = bah / bah.iloc[0]

    for freq, label in [("ME", "월간 리밸런싱"), ("QE", "분기 리밸런싱"), ("YE", "연간 리밸런싱")]:
        s = _sim_rebalance(prices, weights, freq, cost_bps=cost_bps)
        results[label] = s / s.iloc[0]

    return results


def _sim_rebalance(
    prices: pd.DataFrame, weights: np.ndarray, freq: str, cost_bps: float = 0.0,
) -> pd.Series:
    rebal_set = set(prices.resample(freq).last().index)
    shares = weights / prices.iloc[0].values
    cost_frac = cost_bps / 10_000.0
    out = np.empty(len(prices))
    for i in range(len(prices)):
        row = prices.iloc[i].values
        pv = float((shares * row).sum())
        if prices.index[i] in rebal_set and i > 0 and pv > 0:
            current_w = (shares * row) / pv
            turnover = float(np.abs(weights - current_w).sum()) / 2.0
            pv *= (1.0 - cost_frac * 2.0 * turnover)
            shares = (weights * pv) / row
        out[i] = pv
    return pd.Series(out, index=prices.index)
