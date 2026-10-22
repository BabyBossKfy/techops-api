"""Point d'entrée de l'API TechOps."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import select

from app.ai.assistant import ProcedureAssistant
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import Role, User
from app.routers import assistant, auth, incidents
from app.security import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("techops")


def bootstrap_admin() -> None:
    """Crée le premier administrateur à partir de ADMIN_USERNAME / ADMIN_PASSWORD."""
    if not (settings.admin_username and settings.admin_password):
        return
    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.username == settings.admin_username))
        if existing is None:
            db.add(
                User(
                    username=settings.admin_username,
                    hashed_password=hash_password(settings.admin_password),
                    role=Role.ADMIN,
                )
            )
            db.commit()
            logger.info("Compte administrateur initial créé : %s", settings.admin_username)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    bootstrap_admin()
    app.state.assistant = ProcedureAssistant.from_directory(
        settings.knowledge_dir,
        use_llm=settings.assistant_use_llm,
        model=settings.anthropic_model,
    )
    yield


app = FastAPI(
    title="TechOps API",
    description=(
        "Gestion des incidents techniques avec authentification JWT, contrôle des rôles "
        "et assistant IA (RAG) sur les procédures de maintenance."
    ),
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(auth.router)
app.include_router(incidents.router)
app.include_router(assistant.router)


@app.get("/health", tags=["Supervision"])
def health() -> dict[str, str]:
    return {"status": "ok"}
