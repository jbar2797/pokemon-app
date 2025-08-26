from __future__ import annotations

import csv
from pathlib import Path

from pydantic import ValidationError

from ..db import (
    find_card,
    get_session,
    init_db,
    insert_price_if_absent,
    upsert_card,
)
from .schema import PriceRow

REQUIRED_COLS: set[str] = {"name", "set_code", "number", "date", "price"}


def _has_required_header(path: Path) -> bool:
    try:
        with path.open("r", newline="") as f:
            reader = csv.DictReader(f)
            cols = set(reader.fieldnames or [])
            return REQUIRED_COLS.issubset(cols)
    except Exception:
        return False


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
    """Return (valid_count, invalid_count) for a CSV file against PriceRow schema."""
    valid = 0
    invalid = 0
    with path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                PriceRow.model_validate(dict(row))
                valid += 1
            except ValidationError:
                invalid += 1
    return (valid, invalid)


def ingest_csv(path: Path, default_source: str = "csv") -> tuple[int, int, int]:
    """
    Ingest one CSV file (idempotent on (card_id, date, source)).
    Returns (cards_created, prices_inserted, prices_skipped).
    """
    # Ensure tables exist before writing.
    init_db()

    created_cards = 0
    inserted = 0
    skipped = 0
    card_cache: dict[tuple[str, str, str], int] = {}

    with get_session() as session:
        rows = _read_rows(path)
        for raw in rows:
            try:
                pr = PriceRow.model_validate(raw)
            except ValidationError:
                skipped += 1
                session.rollback()
                continue

            name = pr.name.strip()
            set_code = pr.set_code.strip()
            number = pr.number.strip()
            source = (pr.source or default_source).strip() or default_source

            key = (name, set_code, number)
            if key in card_cache:
                card_id = card_cache[key]
            else:
                # Track card creations precisely.
                existing = find_card(session, name=name, set_code=set_code, number=number)
                if existing is None:
                    created = upsert_card(
                        session,
                        name=name,
                        set_code=set_code,
                        number=number,
                        rarity=pr.rarity,
                    )
                    assert created.id is not None
                    card_id = created.id
                    created_cards += 1
                else:
                    assert existing.id is not None
                    card_id = existing.id
                card_cache[key] = card_id

            if insert_price_if_absent(
                session,
                card_id=card_id,
                dt=pr.date,
                source=source,
                price=float(pr.price),
            ):
                inserted += 1
            else:
                skipped += 1

    return (created_cards, inserted, skipped)


def ingest_dir(dir_path: Path, default_source: str = "csv") -> tuple[int, int, int]:
    """
    Ingest all *.csv files under dir_path (non-recursive) that have the required header.
    Skips CSVs that don't match the ingestion schema (e.g., equity/signals exports).
    Returns accumulated (cards_created, prices_inserted, prices_skipped).
    """
    total_c = 0
    total_i = 0
    total_s = 0

    for csv_file in sorted(dir_path.glob("*.csv")):
        if not _has_required_header(csv_file):
            # Silently skip non-price CSVs; they are not ingestion inputs.
            continue
        c, i, s = ingest_csv(csv_file, default_source=default_source)
        total_c += c
        total_i += i
        total_s += s

    return (total_c, total_i, total_s)


__all__ = ["validate_csv", "ingest_csv", "ingest_dir"]
