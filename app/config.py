"""Configuration de l'application, lue depuis les variables d'environnement."""

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_JWT_SECRET = "dev-only-secret-change-me-before-deploying-32b"


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "oui"}


@dataclass(frozen=True)
class Settings:
    environment: str
    database_url: str
    jwt_secret: str
    jwt_algorithm: str
    access_token_minutes: int
    admin_username: str | None
    admin_password: str | None
    assistant_use_llm: bool
    anthropic_model: str
    knowledge_dir: Path


def load_settings() -> Settings:
    settings = Settings(
        environment=os.getenv("ENVIRONMENT", "development"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./techops.db"),
        jwt_secret=os.getenv("JWT_SECRET", DEFAULT_JWT_SECRET),
        jwt_algorithm="HS256",
        access_token_minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "30")),
        admin_username=os.getenv("ADMIN_USERNAME") or None,
        admin_password=os.getenv("ADMIN_PASSWORD") or None,
        assistant_use_llm=_bool("ASSISTANT_USE_LLM"),
        anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5"),
        knowledge_dir=Path(os.getenv("KNOWLEDGE_DIR", str(PROJECT_ROOT / "knowledge"))),
    )
    # Garde-fou : on refuse de démarrer en production avec le secret de développement.
    if settings.environment == "production" and settings.jwt_secret == DEFAULT_JWT_SECRET:
        raise RuntimeError("JWT_SECRET doit être défini en production.")
    return settings


settings = load_settings()
