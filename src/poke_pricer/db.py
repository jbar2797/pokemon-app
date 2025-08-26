from __future__ import annotations

from datetime import date
from pathlib import Path

from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine, select

from .config import Settings
from .models import Card, PricePoint


def _sqlite_url(path: Path) -> str:
    return f"sqlite:///{path}"


def get_engine(settings: Settings | None = None) -> Engine:
    s = settings or Settings()
    path = Path(s.sqlite_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(_sqlite_url(path), echo=False)


def init_db(engine: Engine | None = None) -> None:
    engine = engine or get_engine()
    SQLModel.metadata.create_all(engine)


def get_session(engine: Engine | None = None) -> Session:
    engine = engine or get_engine()
    return Session(engine)


def find_card(session: Session, name: str, set_code: str, number: str) -> Card | None:
    return session.exec(
        select(Card).where(Card.name == name, Card.set_code == set_code, Card.number == number)
    ).first()


def upsert_card(
    session: Session, name: str, set_code: str, number: str, rarity: str | None = None
) -> Card:
    c = find_card(session, name=name, set_code=set_code, number=number)
    if c:
        return c
    c = Card(name=name, set_code=set_code, number=number, rarity=rarity)
    session.add(c)
    session.commit()
    session.refresh(c)
    return c


def insert_price_if_absent(
    session: Session, card_id: int, dt: date, source: str, price: float
) -> bool:
    p = PricePoint(card_id=card_id, date=dt, source=source, price=price)
    try:
        session.add(p)
        session.commit()
        return True
    except IntegrityError:
        session.rollback()
        return False
