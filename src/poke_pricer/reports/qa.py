from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..analytics.data_access import load_prices_df
from ..catalog.stats import catalog_summary_df


def _duplicates_df(df: pd.DataFrame) -> pd.DataFrame:
    """Duplicate price points on (card_id, date, source)."""
    if df.empty or not {"card_id", "date", "source"}.issubset(df.columns):
        cols = ["card_id", "name", "set_code", "number", "source", "date", "count"]
        return pd.DataFrame(columns=cols)

    key = ["card_id", "date", "source"]
    dup = df[df.duplicated(subset=key, keep=False)].copy()
    if dup.empty:
        cols = ["card_id", "name", "set_code", "number", "source", "date", "count"]
        return pd.DataFrame(columns=cols)

    counts = dup.groupby(key).size().reset_index(name="count")
    meta_cols = ["card_id", "name", "set_code", "number", "source", "date"]
    meta = dup.loc[:, meta_cols].drop_duplicates(subset=key).copy()
    merged = counts.merge(meta, on=key, how="left")
    out_cols = ["card_id", "name", "set_code", "number", "source", "date", "count"]
    return merged.loc[:, out_cols]


def _stale_cards_df(df: pd.DataFrame, days: int) -> pd.DataFrame:
    """Cards with no prices within the last N days of the dataset."""
    if df.empty or not {"card_id", "date"}.issubset(df.columns):
        cols = ["card_id", "name", "set_code", "number", "last_date", "age_days"]
        return pd.DataFrame(columns=cols)

    max_dt = df["date"].max()
    last_dt = (
        df.groupby("card_id", as_index=False)["date"].max().rename(columns={"date": "last_date"})
    )
    meta = df.loc[:, ["card_id", "name", "set_code", "number"]].drop_duplicates("card_id")
    merged = last_dt.merge(meta, on="card_id", how="left")
    merged["age_days"] = (max_dt - merged["last_date"]).dt.days
    out = merged[merged["age_days"] > days].copy()
    cols = ["card_id", "name", "set_code", "number", "last_date", "age_days"]
    return out.loc[:, cols].sort_values("age_days", ascending=False, kind="stable")


def write_qa_bundle(out_dir: Path, stale_days: int = 30) -> list[Path]:
    """
    Write QA CSVs:
      - qa_summary.csv
      - qa_duplicates.csv
      - qa_stale_cards.csv
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    prices = load_prices_df()
    summary = catalog_summary_df()
    dups = _duplicates_df(prices)
    stale = _stale_cards_df(prices, days=stale_days)

    p_summary = out / "qa_summary.csv"
    p_dups = out / "qa_duplicates.csv"
    p_stale = out / "qa_stale_cards.csv"

    summary.to_csv(p_summary, index=False)
    dups.to_csv(p_dups, index=False)
    stale.to_csv(p_stale, index=False)

    return [p_summary, p_dups, p_stale]


__all__ = ["write_qa_bundle"]
