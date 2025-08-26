from __future__ import annotations

from collections.abc import Iterable
from datetime import date as _date

import pandas as pd


def _to_ts(d: _date | str | None) -> pd.Timestamp | None:
    if d is None:
        return None
    return pd.to_datetime(d)  # accepts date or string


def compute_top_movers(
    df: pd.DataFrame,
    *,
    k: int = 5,
    on_date: _date | str | None = None,
    id_col: str = "card_id",
    price_col: str = "price",
    date_col: str = "date",
    group_cols: Iterable[str] = ("card_id", "name", "set_code", "number"),
) -> pd.DataFrame:
    """
    Return top/bottom k movers for a given day (simple 1D pct-change).
    Expects columns: id_col, 'name','set_code','number', date_col, price_col, 'source'.
    """
    if df.empty:
        return pd.DataFrame(
            columns=[*group_cols, "source", price_col, "return_1d", "bucket", date_col]
        )

    work = df.copy()
    work[date_col] = pd.to_datetime(work[date_col])

    # Sort and compute 1D return per card_id
    work = work.sort_values([id_col, date_col], kind="stable")
    work["return_1d"] = work.groupby(id_col)[price_col].pct_change()

    # Select the day of interest (default = latest available)
    day_ts = _to_ts(on_date) or work[date_col].max()

    today = work[work[date_col] == day_ts].copy()
    # Keep only rows where return is defined (needs prior day)
    today = today.dropna(subset=["return_1d"])

    if today.empty:
        return pd.DataFrame(
            columns=[*group_cols, "source", price_col, "return_1d", "bucket", date_col]
        )

    cols = [*group_cols, "source", price_col, "return_1d", date_col]
    today = today.loc[:, cols]

    winners = today.sort_values("return_1d", ascending=False, kind="stable").head(k).copy()
    losers = today.sort_values("return_1d", ascending=True, kind="stable").head(k).copy()
    winners["bucket"] = "winner"
    losers["bucket"] = "loser"

    out = pd.concat([winners, losers], ignore_index=True)
    out = out.sort_values(["bucket", "return_1d"], ascending=[True, False], kind="stable")
    return out.reset_index(drop=True)
