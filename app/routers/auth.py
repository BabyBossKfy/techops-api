"""Routes d'authentification : inscription, connexion, profil et gestion des rôles."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Role, User
from app.schemas import RoleUpdate, Token, UserCreate, UserOut
from app.security import (
    create_access_token,
    get_current_user,
    hash_password,
    require_roles,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)) -> User:
    if db.scalar(select(User).where(User.username == data.username)) is not None:
        raise HTTPException(status_code=409, detail="Nom d'utilisateur déjà utilisé")
    # Toute inscription crée un simple agent : seul un admin peut élever les droits.
    user = User(
        username=data.username, hashed_password=hash_password(data.password), role=Role.AGENT
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> Token:
    user = db.scalar(select(User).where(User.username == form.username))
    # Même message que l'utilisateur existe ou non, pour ne rien révéler.
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Identifiants invalides",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.patch("/users/{user_id}/role", response_model=UserOut)
def change_role(
    user_id: int,
    data: RoleUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles(Role.ADMIN)),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user.role = data.role
    db.commit()
    db.refresh(user)
    return user
