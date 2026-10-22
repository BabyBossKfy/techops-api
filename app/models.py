"""Modèles de données : utilisateurs et incidents techniques."""

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Role(str, enum.Enum):
    AGENT = "agent"
    SUPERVISEUR = "superviseur"
    ADMIN = "admin"


class Severity(str, enum.Enum):
    FAIBLE = "faible"
    MOYENNE = "moyenne"
    CRITIQUE = "critique"


class Status(str, enum.Enum):
    OUVERT = "ouvert"
    EN_COURS = "en_cours"
    RESOLU = "resolu"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.AGENT)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    equipment: Mapped[str] = mapped_column(String(100), index=True)
    severity: Mapped[Severity] = mapped_column(Enum(Severity))
    status: Mapped[Status] = mapped_column(Enum(Status), default=Status.OUVERT, index=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, onupdate=utcnow
    )

    reporter: Mapped[User] = relationship()
