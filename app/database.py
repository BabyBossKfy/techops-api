"""Connexion à la base de données (PostgreSQL en production, SQLite en local et en test)."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings


def _engine_options(url: str) -> dict:
    if url.startswith("sqlite"):
        options: dict = {"connect_args": {"check_same_thread": False}}
        # Base en mémoire : une seule connexion partagée, sinon chaque connexion
        # verrait une base vide.
        if url in ("sqlite://", "sqlite:///:memory:"):
            options["poolclass"] = StaticPool
        return options
    return {"pool_pre_ping": True}


engine = create_engine(settings.database_url, **_engine_options(settings.database_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
