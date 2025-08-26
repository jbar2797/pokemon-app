from __future__ import annotations

from datetime import date
from typing import Any, ClassVar

from sqlalchemy import Index, UniqueConstraint
from sqlmodel import Field, SQLModel


class Card(SQLModel, table=True):  # type: ignore[call-arg,misc]
    id: int | None = Field(default=None, primary_key=True)
    name: str
    set_code: str
    number: str
    rarity: str | None = None

    __table_args__: ClassVar[tuple[Any, ...]] = (
        UniqueConstraint("set_code", "number", name="uq_card_set_number"),
        Index("ix_card_name", "name"),
    )


class PricePoint(SQLModel, table=True):  # type: ignore[call-arg,misc]
    id: int | None = Field(default=None, primary_key=True)
    card_id: int = Field(foreign_key="card.id")
    date: date
    source: str
    price: float

    __table_args__: ClassVar[tuple[Any, ...]] = (
        UniqueConstraint("card_id", "date", "source", name="uq_price_card_date_source"),
        Index("ix_price_date", "date"),
    )
