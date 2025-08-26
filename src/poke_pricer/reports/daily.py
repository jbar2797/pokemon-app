from __future__ import annotations

from pathlib import Path

from ..analytics.data_access import load_prices_df
from ..analytics.movers import compute_top_movers
from ..catalog.stats import catalog_summary_df


def write_daily_reports(out_dir: Path, k: int = 5, on_date: str | None = None) -> list[Path]:
    """
    Produce a small daily bundle of CSV files into out_dir:
      - catalog_summary.csv
      - top_movers.csv
      - latest_prices.csv (if data available)
    Returns the list of written paths.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Catalog summary
    summary_df = catalog_summary_df()
    summary_path = out_dir / "catalog_summary.csv"
    summary_df.to_csv(summary_path, index=False)

    # 2) Top movers
    prices_df = load_prices_df()
    movers_df = compute_top_movers(prices_df, k=k, on_date=on_date)
    movers_path = out_dir / "top_movers.csv"
    movers_df.to_csv(movers_path, index=False)

    written: list[Path] = [summary_path, movers_path]

    # 3) Latest prices snapshot
    if not prices_df.empty and "date" in prices_df.columns:
        latest_date = prices_df["date"].max()
        latest = prices_df.loc[
            prices_df["date"] == latest_date,
            [
                "card_id",
                "name",
                "set_code",
                "number",
                "source",
                "price",
                "date",
            ],
        ].copy()
        latest_path = out_dir / "latest_prices.csv"
        latest.to_csv(latest_path, index=False)
        written.append(latest_path)

    return written


__all__ = ["write_daily_reports"]
