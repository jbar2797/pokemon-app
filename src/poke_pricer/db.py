from __future__ import annotations

from pathlib import Path

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from .config import Settings


def _sqlite_url(path: Path) -> str:
    return f"sqlite:///{path}"


def get_engine(settings: Settings | None = None) -> Engine:
    s = settings or Settings()
    path = Path(s.sqlite_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(_sqlite_url(path), echo=False)
    return engine


def init_db(engine: Engine | None = None) -> None:
    engine = engine or get_engine()
    SQLModel.metadata.create_all(engine)


def get_session(engine: Engine | None = None) -> Session:
    engine = engine or get_engine()
    return Session(engine)
