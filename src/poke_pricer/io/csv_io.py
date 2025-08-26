from __future__ import annotations

import csv
from pathlib import Path

from sqlmodel import Session, select

from ..db import get_engine
from ..models import Card, PricePoint


def export_prices_csv(out_path: Path) -> int:
    """Export joined (price + card) rows to CSV. Returns number of rows written."""
    engine = get_engine()
    with Session(engine) as session:
        stmt = select(PricePoint, Card).join(
            Card,
            onclause=(PricePoint.card_id == Card.id),  # type: ignore[arg-type]
        )
        rows = session.exec(stmt).all()

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["card_id", "name", "set_code", "number", "date", "source", "price"])
            for p, c in rows:
                w.writerow(
                    [
                        p.card_id,
                        c.name,
                        c.set_code,
                        c.number,
                        p.date.isoformat(),
                        p.source,
                        f"{p.price:.2f}",
                    ]
                )
    return len(rows)
