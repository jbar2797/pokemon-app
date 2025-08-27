from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..analytics.data_access import load_prices_df

KEYS = ["name", "set_code", "number"]


def _latest_by_keys(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Return the latest row per key-group based on the 'date' column."""
    if df.empty:
        return df.copy()
    work = df.sort_values("date").drop_duplicates(keys, keep="last")
    return work.reset_index(drop=True)


def watchlist_latest_prices(watchlist_csv: Path) -> pd.DataFrame:
    """
    Input CSV schema:
      name,set_code,number
    Output columns:
      card_id,name,set_code,number,source,price,date
    """
    wl = pd.read_csv(watchlist_csv, dtype=str).fillna("")
    for col in KEYS:
        if col not in wl.columns:
            raise ValueError(f"watchlist missing column: {col}")

    prices = load_prices_df()
    if prices.empty:
        return pd.DataFrame(columns=["card_id", *KEYS, "source", "price", "date"])

    latest = _latest_by_keys(prices, KEYS)
    out = wl.merge(latest, on=KEYS, how="left")
    cols = ["card_id", *KEYS, "source", "price", "date"]
    for c in cols:
        if c not in out.columns:
            out[c] = ""  # ensure stable header even if merge misses
    return out.loc[:, cols].reset_index(drop=True)


def portfolio_valuation(holdings_csv: Path) -> pd.DataFrame:
    """
    Input CSV schema:
      name,set_code,number,qty,cost_per_unit
    Output columns:
      name,set_code,number,qty,price,date,market_value,cost_per_unit,pnl,pct_return
    """
    dtypes = {"name": str, "set_code": str, "number": str}
    hold = pd.read_csv(holdings_csv, dtype=dtypes)
    for col in (*KEYS, "qty", "cost_per_unit"):
        if col not in hold.columns:
            raise ValueError(f"holdings missing column: {col}")

    # Coerce numeric
    hold["qty"] = pd.to_numeric(hold["qty"], errors="coerce").fillna(0.0)
    hold["cost_per_unit"] = pd.to_numeric(hold["cost_per_unit"], errors="coerce").fillna(0.0)

    prices = load_prices_df()
    if prices.empty:
        return pd.DataFrame(
            columns=[
                *KEYS,
                "qty",
                "price",
                "date",
                "market_value",
                "cost_per_unit",
                "pnl",
                "pct_return",
            ]
        )

    latest = _latest_by_keys(prices, KEYS)
    joined = hold.merge(latest, on=KEYS, how="left")

    joined["price"] = pd.to_numeric(joined.get("price"), errors="coerce")
    joined["market_value"] = (joined["price"].fillna(0.0)) * joined["qty"]

    cb = joined["cost_per_unit"]
    px = joined["price"]
    joined["pnl"] = (px.fillna(0.0) - cb) * joined["qty"]
    joined["pct_return"] = (px - cb) / cb.replace(0.0, pd.NA)

    cols = [
        *KEYS,
        "qty",
        "price",
        "date",
        "market_value",
        "cost_per_unit",
        "pnl",
        "pct_return",
    ]
    for c in cols:
        if c not in joined.columns:
            joined[c] = pd.NA
    return joined.loc[:, cols].reset_index(drop=True)


__all__ = ["watchlist_latest_prices", "portfolio_valuation"]
