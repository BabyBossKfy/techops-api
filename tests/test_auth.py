from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings


def test_register_then_login_returns_token(client):
    response = client.post("/auth/register", json={"username": "franck", "password": "Secret123!"})
    assert response.status_code == 201
    assert response.json()["role"] == "agent"

    response = client.post("/auth/login", data={"username": "franck", "password": "Secret123!"})
    assert response.status_code == 200
    token = response.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "franck"


def test_register_duplicate_username_is_rejected(client):
    payload = {"username": "doublon", "password": "Secret123!"}
    assert client.post("/auth/register", json=payload).status_code == 201
    assert client.post("/auth/register", json=payload).status_code == 409


def test_register_rejects_short_password(client):
    response = client.post("/auth/register", json={"username": "court", "password": "abc"})
    assert response.status_code == 422


def test_login_with_wrong_password_fails(client, agent_headers):
    response = client.post("/auth/login", data={"username": "agent1", "password": "mauvais"})
    assert response.status_code == 401


def test_protected_route_requires_token(client):
    assert client.get("/auth/me").status_code == 401


def test_token_signed_with_another_secret_is_rejected(client, agent_headers):
    forged = jwt.encode({"sub": "1", "role": "admin"}, "un-autre-secret-de-plus-de-32-octets", "HS256")
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


def test_expired_token_is_rejected(client, agent_headers):
    past = datetime.now(timezone.utc) - timedelta(minutes=5)
    expired = jwt.encode(
        {"sub": "1", "role": "agent", "iat": past - timedelta(minutes=30), "exp": past},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


def test_only_admin_can_change_roles(client, agent_headers, admin_headers):
    created = client.post("/auth/register", json={"username": "promu", "password": "Secret123!"})
    user_id = created.json()["id"]

    response = client.patch(
        f"/auth/users/{user_id}/role", json={"role": "superviseur"}, headers=agent_headers
    )
    assert response.status_code == 403

    response = client.patch(
        f"/auth/users/{user_id}/role", json={"role": "superviseur"}, headers=admin_headers
    )
    assert response.status_code == 200
    assert response.json()["role"] == "superviseur"
