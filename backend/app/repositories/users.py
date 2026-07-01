from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def get_by_id(self, user_id: str) -> User | None:
        return self.db.get(User, user_id)

    def get_by_google_sub(self, google_sub: str) -> User | None:
        return self.db.scalar(select(User).where(User.google_sub == google_sub))

    def create(self, *, email: str, full_name: str, hashed_password: str | None, role: str, google_sub: str | None = None) -> User:
        user = User(email=email, full_name=full_name, hashed_password=hashed_password, role=role, google_sub=google_sub)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
