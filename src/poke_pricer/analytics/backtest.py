from __future__ import annotations

import pandas as pd


def backtest_momentum_topk(
    df: pd.DataFrame,
    price_col: str = "price",
    id_col: str = "card_id",
    date_col: str = "date",
    lookback: int = 14,
    top_k: int = 1,
) -> pd.DataFrame:
    """Each day, long the top_k cards by lookback-momentum; hold 1 day; equal-weight."""
    data = df.copy()
    data = data.sort_values([date_col, id_col], kind="stable").reset_index(drop=True)

    # Daily returns and forward return for next-day P&L attribution
    data["ret"] = data.groupby(id_col)[price_col].pct_change()
    data["mom"] = data.groupby(id_col)[price_col].transform(lambda s: s / s.shift(lookback) - 1.0)
    data["fwd_ret"] = data.groupby(id_col)["ret"].shift(-1)

    results: list[dict[str, float]] = []
    for d, g in data.groupby(date_col):
        g = g.dropna(subset=["mom", "fwd_ret"])
        if g.empty:
            continue
        picks = g.sort_values("mom", ascending=False).head(top_k)
        port_ret = float(picks["fwd_ret"].mean())
        results.append({"date": d, "portfolio_return": port_ret})

    bt = pd.DataFrame(results).sort_values("date", kind="stable").reset_index(drop=True)
    if bt.empty:
        bt = pd.DataFrame(columns=["date", "portfolio_return", "equity"])
        return bt
    bt["equity"] = (1.0 + bt["portfolio_return"]).cumprod()
    return bt
