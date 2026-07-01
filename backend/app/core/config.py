from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    project_name: str = "GenCloudNet API"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60 * 24
    algorithm: str = "HS256"

    database_url: str = "sqlite:///./gencloudnet.db"
    redis_url: str = "redis://localhost:6379/0"
    mlflow_tracking_uri: str = "http://localhost:5000"
    wandb_project: str = "gencloudnet"

    backend_base_url: str = "http://localhost:8000"
    frontend_base_url: str = "http://localhost:3000"
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_path: str = "/api/v1/auth/google/callback"
    allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    storage_root: Path = Path("backend/storage")
    raw_upload_dir: Path = Path("backend/storage/raw")
    processed_dir: Path = Path("backend/storage/processed")
    preview_dir: Path = Path("backend/storage/previews")
    report_dir: Path = Path("backend/storage/reports")
    checkpoint_dir: Path = Path("artifacts/checkpoints")

    max_upload_mb: int = 512

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def google_redirect_uri(self) -> str:
        return f"{self.backend_base_url.rstrip('/')}{self.google_redirect_path}"

    def ensure_directories(self) -> None:
        for directory in (
            self.storage_root,
            self.raw_upload_dir,
            self.processed_dir,
            self.preview_dir,
            self.report_dir,
            self.checkpoint_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings


settings = get_settings()
