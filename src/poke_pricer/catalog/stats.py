from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import func
from sqlmodel import Session, select

from ..db import get_engine
from ..models import PricePoint


def _normalize_sources(values: Sequence[Any]) -> list[str]:
    """
    mypy- and runtime-safe normalization for distinct() results which may be
    typed as list[str] or list[tuple[str]]. We only keep non-empty strings.
    """
    out: list[str] = []
    for v in values:
        if isinstance(v, tuple):
            if v and isinstance(v[0], str) and v[0]:
                out.append(v[0])
        elif isinstance(v, str) and v:
            out.append(v)
    return out


def catalog_summary_df() -> pd.DataFrame:
    """Return a one-row DataFrame with dataset summary."""
    engine = get_engine()
    with Session(engine) as session:
        total_prices = session.exec(select(func.count()).select_from(PricePoint)).one()

        total_cards = session.exec(select(func.count(func.distinct(PricePoint.card_id)))).one()

        min_date = session.exec(select(func.min(PricePoint.date))).one_or_none()

        max_date = session.exec(select(func.max(PricePoint.date))).one_or_none()

        sources_raw = session.exec(select(PricePoint.source).distinct()).all()
        sources_list = _normalize_sources(sources_raw)

    df = pd.DataFrame(
        [
            {
                "total_cards": int(total_cards or 0),
                "total_prices": int(total_prices or 0),
                "min_date": str(min_date) if min_date else "",
                "max_date": str(max_date) if max_date else "",
                "sources": ",".join(sorted(sources_list)),
            }
        ]
    )
    return df


def export_catalog_csv(out_path: Path) -> None:
    """Export catalog summary to CSV at the given path."""
    df = catalog_summary_df()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
