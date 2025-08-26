from __future__ import annotations

from datetime import date

from sqlmodel import Field, SQLModel


class Card(SQLModel, table=True):  # type: ignore[call-arg,misc]
    id: int | None = Field(default=None, primary_key=True)
    name: str
    set_code: str
    number: str
    rarity: str | None = None


class PricePoint(SQLModel, table=True):  # type: ignore[call-arg,misc]
    id: int | None = Field(default=None, primary_key=True)
    card_id: int = Field(foreign_key="card.id")
    date: date
    source: str
    price: float
