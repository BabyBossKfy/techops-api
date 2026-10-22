"""Schémas Pydantic : validation des entrées et format des réponses de l'API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import Role, Severity, Status


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        # bcrypt ne prend en compte que les 72 premiers octets du mot de passe.
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Le mot de passe ne doit pas dépasser 72 octets.")
        return value


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: Role


class RoleUpdate(BaseModel):
    role: Role


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class IncidentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=5000)
    equipment: str = Field(min_length=2, max_length=100)
    severity: Severity


class IncidentStatusUpdate(BaseModel):
    status: Status


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    equipment: str
    severity: Severity
    status: Status
    reporter_id: int
    created_at: datetime
    updated_at: datetime | None


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class Source(BaseModel):
    document: str
    extrait: str
    score: float


class AskResponse(BaseModel):
    answer: str
    mode: str = Field(description="generatif, extractif ou aucun_resultat")
    sources: list[Source]
