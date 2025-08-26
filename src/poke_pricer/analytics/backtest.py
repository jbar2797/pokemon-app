from __future__ import annotations

from typing import Any

import pandas as pd
from pandas import DataFrame


def backtest_momentum_topk(
    df: DataFrame,
    *,
    lookback: int = 14,
    top_k: int = 1,
    price_col: str = "price",
    id_col: str = "card_id",
    date_col: str = "date",
) -> DataFrame:
    """
    Simple cross-sectional momentum backtest:
      - For each date, pick top_k cards by momentum over `lookback` days.
      - Portfolio return for that date = average next-day return of picks.
      - Equity = cumulative product of (1 + portfolio_return).

    Robust to tiny datasets: if no valid picks exist (e.g., too short history),
    returns an empty DataFrame with columns ["date", "portfolio_return", "equity"].
    """
    data = df.sort_values([id_col, date_col], kind="stable").reset_index(drop=True).copy()

    # Ensure needed columns exist; compute them if absent.
    if "ret" not in data:
        data["ret"] = data.groupby(id_col)[price_col].pct_change()

    if "mom" not in data:
        # momentum over `lookback` days
        data["mom"] = data.groupby(id_col)[price_col].transform(
            lambda s: s / s.shift(lookback) - 1.0
        )

    if "fwd_ret" not in data:
        data["fwd_ret"] = data.groupby(id_col)[price_col].shift(-1) / data[price_col] - 1.0

    results: list[dict[str, Any]] = []
    for d, g in data.groupby(date_col, sort=True):
        picks = g[["mom", "fwd_ret"]].dropna()
        if picks.empty:
            continue
        picks = picks.sort_values("mom", ascending=False).head(top_k)
        port_ret = float(picks["fwd_ret"].mean())
        results.append({"date": d, "portfolio_return": port_ret})

    bt = pd.DataFrame(results)
    if bt.empty:
        # Return a schema-stable empty frame (so callers can write it safely).
        return pd.DataFrame(columns=["date", "portfolio_return", "equity"])

    bt = bt.sort_values("date", kind="stable").reset_index(drop=True)
    bt["equity"] = (1.0 + bt["portfolio_return"]).cumprod()
    return bt
