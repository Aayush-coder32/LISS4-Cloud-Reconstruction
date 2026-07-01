from __future__ import annotations

from datetime import timedelta
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.domain.models import UserRole
from app.domain.schemas import TokenResponse, UserCreate, UserRead
from app.repositories.users import UserRepository


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    def register(self, payload: UserCreate) -> TokenResponse:
        if self.user_repository.get_by_email(payload.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

        user = self.user_repository.create(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=get_password_hash(payload.password),
            role=payload.role,
        )
        token = create_access_token(user.id, expires_delta=timedelta(minutes=settings.access_token_expire_minutes))
        return TokenResponse(access_token=token, user=UserRead.model_validate(user))

    def authenticate(self, email: str, password: str) -> TokenResponse:
        user = self.user_repository.get_by_email(email)
        if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        token = create_access_token(user.id, expires_delta=timedelta(minutes=settings.access_token_expire_minutes))
        return TokenResponse(access_token=token, user=UserRead.model_validate(user))

    def google_login_url(self, state: str = "gencloudnet") -> str:
        if not settings.google_client_id:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google OAuth is not configured")

        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)

    async def handle_google_callback(self, code: str) -> TokenResponse:
        if not settings.google_client_id or not settings.google_client_secret:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google OAuth is not configured")

        async with httpx.AsyncClient(timeout=30.0) as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.google_redirect_uri,
                },
            )
            token_response.raise_for_status()
            access_token = token_response.json()["access_token"]
            user_info_response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_info_response.raise_for_status()
            profile = user_info_response.json()

        google_sub = profile["sub"]
        user = self.user_repository.get_by_google_sub(google_sub) or self.user_repository.get_by_email(profile["email"])
        if not user:
            user = self.user_repository.create(
                email=profile["email"],
                full_name=profile.get("name", profile["email"]),
                hashed_password=None,
                role=UserRole.operator,
                google_sub=google_sub,
            )
        elif not user.google_sub:
            user.google_sub = google_sub
            self.user_repository.db.add(user)
            self.user_repository.db.commit()
            self.user_repository.db.refresh(user)

        token = create_access_token(user.id)
        return TokenResponse(access_token=token, user=UserRead.model_validate(user))
