from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import DbSession, get_current_user
from app.domain.models import User
from app.domain.schemas import GoogleLoginResponse, TokenResponse, UserCreate, UserRead
from app.repositories.users import UserRepository
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(payload: UserCreate, db: DbSession) -> TokenResponse:
    return AuthService(UserRepository(db)).register(payload)


@router.post("/token", response_model=TokenResponse)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession) -> TokenResponse:
    return AuthService(UserRepository(db)).authenticate(form_data.username, form_data.password)


@router.get("/google/login", response_model=GoogleLoginResponse)
def google_login(db: DbSession, state: str = Query(default="gencloudnet")) -> GoogleLoginResponse:
    service = AuthService(UserRepository(db))
    return GoogleLoginResponse(authorization_url=service.google_login_url(state=state))


@router.get("/google/callback", response_model=TokenResponse)
async def google_callback(code: str, db: DbSession) -> TokenResponse:
    return await AuthService(UserRepository(db)).handle_google_callback(code)


@router.get("/me", response_model=UserRead)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserRead:
    return UserRead.model_validate(current_user)
