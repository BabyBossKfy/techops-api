"""Fixtures partagées par les tests.

Les variables d'environnement sont fixées AVANT d'importer l'application : les tests
tournent sur une base dédiée (SQLite en mémoire par défaut, ou TEST_DATABASE_URL en CI)
et ne touchent jamais à la base configurée dans DATABASE_URL.
"""

import os

os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", "sqlite://")
os.environ["JWT_SECRET"] = "test-secret-key-long-enough-for-hs256-signing"
os.environ["ASSISTANT_USE_LLM"] = "false"
os.environ.pop("ADMIN_USERNAME", None)
os.environ.pop("ADMIN_PASSWORD", None)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Role, User  # noqa: E402
from app.security import hash_password  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client


def _create_user(username: str, password: str, role: Role) -> None:
    with SessionLocal() as db:
        db.add(User(username=username, hashed_password=hash_password(password), role=role))
        db.commit()


def _login(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post("/auth/login", data={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture()
def agent_headers(client):
    _create_user("agent1", "MotDePasseAgent1", Role.AGENT)
    return _login(client, "agent1", "MotDePasseAgent1")


@pytest.fixture()
def supervisor_headers(client):
    _create_user("superviseur1", "MotDePasseSup1", Role.SUPERVISEUR)
    return _login(client, "superviseur1", "MotDePasseSup1")


@pytest.fixture()
def admin_headers(client):
    _create_user("admin1", "MotDePasseAdmin1", Role.ADMIN)
    return _login(client, "admin1", "MotDePasseAdmin1")
