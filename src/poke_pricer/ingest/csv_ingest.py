from __future__ import annotations

import csv
from pathlib import Path

from ..db import (
    find_card,
    get_engine,
    get_session,
    init_db,
    insert_price_if_absent,
    upsert_card,
)
from .schema import PriceRow

REQUIRED_COLS = {"name", "set_code", "number", "date", "price"}


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        cols = set(reader.fieldnames or [])
        missing = REQUIRED_COLS - cols
        if missing:
            raise ValueError(
                f"CSV missing required columns: {sorted(missing)} (have: {sorted(cols)})"
            )
        return [dict(row) for row in reader]


def validate_csv(path: Path) -> tuple[int, int]:
    """Return (valid_rows, invalid_rows) for a CSV file."""
    valid = 0
    invalid = 0
    for row in _read_rows(path):
        try:
            PriceRow.model_validate(row)
            valid += 1
        except Exception:
            invalid += 1
    return (valid, invalid)


def ingest_csv(path: Path, default_source: str = "csv") -> tuple[int, int, int]:
    """
    Ingest a single CSV file into SQLite.
    Returns: (cards_created, prices_inserted, prices_skipped_duplicate)
    """
    engine = get_engine()
    init_db(engine)

    created_cards = 0
    inserted = 0
    skipped = 0

    # cache to avoid re-querying same triplet
    card_cache: dict[tuple[str, str, str], int] = {}

    with get_session(engine) as session:
        rows = _read_rows(path)
        for raw in rows:
            try:
                pr = PriceRow.model_validate(raw)
            except Exception:
                session.rollback()
                skipped += 1
                continue

            name = pr.name.strip()
            set_code = pr.set_code.strip()
            number = pr.number.strip()
            rarity = pr.rarity.strip() if pr.rarity else None
            source = (pr.source.strip() if pr.source else "") or default_source

            key = (name, set_code, number)
            if key in card_cache:
                card_id = card_cache[key]
            else:
                # Detect existence so we can count creations
                existing = find_card(session, name=name, set_code=set_code, number=number)
                if existing is None:
                    created = upsert_card(
                        session, name=name, set_code=set_code, number=number, rarity=rarity
                    )
                    assert created.id is not None
                    card_id = created.id
                    created_cards += 1
                else:
                    assert existing.id is not None
                    card_id = existing.id
                card_cache[key] = card_id

            if insert_price_if_absent(
                session, card_id=card_id, dt=pr.date, source=source, price=float(pr.price)
            ):
                inserted += 1
            else:
                skipped += 1

    return (created_cards, inserted, skipped)


def ingest_dir(dir_path: Path, default_source: str = "csv") -> tuple[int, int, int]:
    """
    Ingest all *.csv files under dir_path (non-recursive).
    Returns accumulated (cards_created, prices_inserted, prices_skipped).
    """
    total_c = 0
    total_i = 0
    total_s = 0

    for csv_file in sorted(dir_path.glob("*.csv")):
        c, i, s = ingest_csv(csv_file, default_source=default_source)
        total_c += c
        total_i += i
        total_s += s

    return (total_c, total_i, total_s)
