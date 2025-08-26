from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import NotRequired, TypedDict

from ..db import get_engine, get_session, init_db, insert_price_if_absent, upsert_card


class CsvRow(TypedDict):
    name: str
    set_code: str
    number: str
    date: str
    price: str
    source: NotRequired[str]
    rarity: NotRequired[str]


REQUIRED_COLS = {"name", "set_code", "number", "date", "price"}


def _parse_date(text: str) -> date:
    # Expect ISO-8601 (YYYY-MM-DD)
    return date.fromisoformat(text.strip())


def ingest_csv(path: Path, default_source: str = "csv") -> tuple[int, int, int]:
    """Ingest a CSV file into SQLite.
    Returns: (cards_created, prices_inserted, prices_skipped_duplicate)
    """
    engine = get_engine()
    init_db(engine)

    created_cards = 0
    inserted = 0
    skipped = 0

    # local cache to avoid re-querying for the same card triple

    card_cache: dict[tuple[str, str, str], int] = {}

    with get_session(engine) as session:
        with path.open("r", newline="") as f:
            reader = csv.DictReader(f)
            cols = set(reader.fieldnames or [])
            missing = REQUIRED_COLS - cols
            if missing:
                raise ValueError(
                    f"CSV missing required columns: {sorted(missing)} (have: {sorted(cols)})"
                )

            for row in reader:
                r = row  # type: ignore[assignment]
                name = str(r["name"]).strip()
                set_code = str(r["set_code"]).strip()
                number = str(r["number"]).strip()
                src = str(r.get("source") or default_source).strip() or default_source
                rarity = (str(r.get("rarity")).strip() or None) if r.get("rarity") else None

                try:
                    dt = _parse_date(str(r["date"]))
                    price = float(str(r["price"]))
                except Exception:
                    # Skip malformed rows
                    skipped += 1
                    session.rollback()
                    continue

                key = (name, set_code, number)
                if key in card_cache:
                    card_id = card_cache[key]
                else:
                    c = upsert_card(
                        session,
                        name=name,
                        set_code=set_code,
                        number=number,
                        rarity=rarity,
                    )
                    assert c.id is not None
                    card_id = c.id
                    card_cache[key] = card_id
                    # Note: we return created_cards=0 (approx) for simplicity in Sprint 3.

                if insert_price_if_absent(session, card_id=card_id, dt=dt, source=src, price=price):
                    inserted += 1
                else:
                    skipped += 1

    return (created_cards, inserted, skipped)
