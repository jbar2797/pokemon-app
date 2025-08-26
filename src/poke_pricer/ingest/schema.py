from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class PriceRow(BaseModel):
    """Validated CSV row for price ingestion."""

    name: str = Field(min_length=1)
    set_code: str = Field(min_length=1)
    number: str = Field(min_length=1)
    date: date
    price: float
    source: str | None = None
    rarity: str | None = None
