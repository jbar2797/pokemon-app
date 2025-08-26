from __future__ import annotations

from typing import Any

import pandas as pd
from sqlmodel import Session, select

from ..db import get_engine
from ..models import Card, PricePoint


def load_prices_df() -> pd.DataFrame:
    """Return dataframe with columns:
    card_id, name, set_code, number, date (datetime64), source, price (float)."""
    engine = get_engine()
    with Session(engine) as session:
        stmt = select(PricePoint, Card).join(Card, onclause=(PricePoint.card_id == Card.id))  # type: ignore[arg-type]
        rows = session.exec(stmt).all()

    if not rows:
        return pd.DataFrame(
            columns=["card_id", "name", "set_code", "number", "date", "source", "price"]
        )

    records: list[dict[str, Any]] = []
    for p, c in rows:
        records.append(
            {
                "card_id": p.card_id,
                "name": c.name,
                "set_code": c.set_code,
                "number": c.number,
                "date": pd.to_datetime(p.date),
                "source": p.source,
                "price": float(p.price),
            }
        )

    df = pd.DataFrame.from_records(records)
    df = df.sort_values(["card_id", "date"], kind="stable").reset_index(drop=True)
    return df
