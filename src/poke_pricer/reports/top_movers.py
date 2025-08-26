from __future__ import annotations

from typing import Final

import pandas as pd

_COLUMNS: Final[list[str]] = [
    "window_days",
    "rank",
    "card_id",
    "name",
    "set_code",
    "number",
    "last_date",
    "last_price",
    "ret_window",
]


def compute_top_movers(
    df: pd.DataFrame,
    window_days: int = 14,
    top_k: int = 10,
) -> pd.DataFrame:
    """
    Given a DataFrame with columns:
      card_id,name,set_code,number,date,source,price
    compute per-card returns over `window_days`, pick the latest row per card,
    and return the top `top_k` by return.

    Returns a DataFrame with columns in _COLUMNS.
    """
    if df.empty:
        return pd.DataFrame(columns=_COLUMNS)

    # Ensure datetime
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df = df.assign(date=pd.to_datetime(df["date"]))

    # Stable sort then rolling % change
    df = df.sort_values(["card_id", "date"], kind="stable").copy()
    df["ret_window"] = df.groupby("card_id")["price"].pct_change(periods=window_days)

    # Latest row per card, drop cards without the lookback
    last_idx = df.groupby("card_id")["date"].idxmax()
    latest = (
        df.loc[last_idx]
        .dropna(subset=["ret_window"])
        .sort_values("ret_window", ascending=False, kind="stable")
    )

    if top_k > 0:
        latest = latest.head(top_k)

    out = latest[["card_id", "name", "set_code", "number", "date", "price", "ret_window"]].rename(
        columns={"date": "last_date", "price": "last_price"}
    )

    out = out.reset_index(drop=True)
    out.insert(0, "rank", range(1, len(out) + 1))
    out.insert(0, "window_days", window_days)

    # Standardize column order
    return out[_COLUMNS].copy()
