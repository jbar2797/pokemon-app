from __future__ import annotations

import pandas as pd


def compute_signals(
    df: pd.DataFrame,
    price_col: str = "price",
    id_col: str = "card_id",
    date_col: str = "date",
    windows: list[int] | None = None,
) -> pd.DataFrame:
    """Compute simple signals: pct return, rolling SMAs, and momentum over windows."""
    if windows is None:
        windows = [7, 14, 30]

    out = df.copy()
    out = out.sort_values([id_col, date_col], kind="stable").reset_index(drop=True)

    out["ret"] = out.groupby(id_col)[price_col].pct_change()

    for w in windows:
        _w = int(w)
        out[f"sma_{_w}"] = out.groupby(id_col)[price_col].transform(
            lambda s, _w=_w: s.rolling(_w, min_periods=_w).mean()
        )
        out[f"mom_{_w}"] = out.groupby(id_col)[price_col].transform(
            lambda s, _w=_w: s / s.shift(_w) - 1.0
        )

    return out
