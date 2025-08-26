from __future__ import annotations

from datetime import date, timedelta
from random import Random

from sqlmodel import Session, select

from ..db import get_engine, init_db
from ..models import Card, PricePoint


def seed_demo(seed: int = 42) -> tuple[int, int]:
    """Seed a few demo cards and ~30 days of price points per card.

    Returns:
        tuple: (num_cards, num_prices)
    """
    engine = get_engine()
    init_db(engine)

    with Session(engine) as session:
        # If already seeded, return counts
        existing_card = session.exec(select(Card)).first()
        if existing_card:
            existing_cards = session.exec(select(Card)).all()
            existing_prices = session.exec(select(PricePoint)).all()
            return (len(existing_cards), len(existing_prices))

        rng = Random(seed)
        raw_cards = [
            ("Pikachu", "BASE", "58/102", "Common"),
            ("Charizard", "BASE", "4/102", "Holo Rare"),
            ("Blastoise", "BASE", "2/102", "Holo Rare"),
        ]

        seeded_cards: list[Card] = []
        for name, set_code, number, rarity in raw_cards:
            c = Card(name=name, set_code=set_code, number=number, rarity=rarity)
            session.add(c)
            session.flush()  # assigns id
            # type-narrow: after flush, id should be set; assert for mypy/runtime safety
            assert c.id is not None
            seeded_cards.append(c)

        start = date.today() - timedelta(days=29)
        price_count = 0
        for c in seeded_cards:
            assert c.id is not None  # reassure type checker in this scope
            base = rng.uniform(20.0, 300.0)
            for i in range(30):
                # Slight noise around base to look realistic
                factor = 0.95 + 0.1 * rng.random()
                p = PricePoint(
                    card_id=c.id,
                    date=start + timedelta(days=i),
                    source="demo",
                    price=round(base * factor, 2),
                )
                session.add(p)
                price_count += 1

        session.commit()
        return (len(seeded_cards), price_count)
