from __future__ import annotations

from typing import Final

import pandas as pd

C_ID: Final[str] = "card_id"
DATE: Final[str] = "date"
PRICE: Final[str] = "price"
RET: Final[str] = "return_1d"


def _to_ts(s: str | None) -> pd.Timestamp | None:
    if not s:
        return None
    return pd.to_datetime(s)


def scan_anomalies_df(
    df: pd.DataFrame,
    *,
    ret_threshold: float = 0.10,
    lookback: int = 30,
    on_date: str | None = None,
) -> pd.DataFrame:
    """
    Detects anomalies for the selected day:
      - |1d return| >= ret_threshold
      - new high / new low versus prior `lookback` days
    Returns columns: card_id, name, set_code, number, source, price, return_1d, flag, date
    """
    required = {C_ID, "name", "set_code", "number", "source", PRICE, DATE}
    if df.empty or not required.issubset(df.columns):
        return pd.DataFrame(
            columns=[
                "card_id",
                "name",
                "set_code",
                "number",
                "source",
                "price",
                "return_1d",
                "flag",
                "date",
            ]
        )

    work = df.copy()
    work[DATE] = pd.to_datetime(work[DATE])
    work = work.sort_values([C_ID, DATE], kind="stable")

    # 1‑day return
    work[RET] = work.groupby(C_ID)[PRICE].pct_change()

    # rolling extremes (shift(1) so "today" doesn’t compare to itself)
    roll_max = (
        work.groupby(C_ID)[PRICE]
        .transform(lambda s: s.rolling(lookback, min_periods=1).max())
        .shift(1)
    )
    roll_min = (
        work.groupby(C_ID)[PRICE]
        .transform(lambda s: s.rolling(lookback, min_periods=1).min())
        .shift(1)
    )
    work["new_high"] = work[PRICE] > roll_max
    work["new_low"] = work[PRICE] < roll_min

    # pick the day (default latest)
    day = _to_ts(on_date) or work[DATE].max()
    today = work[work[DATE] == day].copy()
    today = today.dropna(subset=[RET])  # need prior day to compute return

    if today.empty:
        return pd.DataFrame(
            columns=[
                "card_id",
                "name",
                "set_code",
                "number",
                "source",
                "price",
                "return_1d",
                "flag",
                "date",
            ]
        )

    spike = today[RET].abs() >= ret_threshold
    flags = []
    for is_spike, is_hi, is_lo in zip(
        spike.tolist(),
        today["new_high"].tolist(),
        today["new_low"].tolist(),
        strict=False,
    ):
        f: list[str] = []
        if is_spike:
            f.append("spike")
        if is_hi:
            f.append("new_high")
        if is_lo:
            f.append("new_low")
        flags.append(",".join(f))

    today["flag"] = flags
    out = today[(spike) | (today["new_high"]) | (today["new_low"])].copy()
    out[DATE] = out[DATE].dt.date.astype(str)

    cols = [
        "card_id",
        "name",
        "set_code",
        "number",
        "source",
        PRICE,
        RET,
        "flag",
        DATE,
    ]
    return out.loc[:, cols].reset_index(drop=True)


__all__ = ["scan_anomalies_df"]
