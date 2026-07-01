from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.deps import DbSession, get_current_user
from app.domain.models import User
from app.domain.schemas import HistoryResponse, ImageAssetRead, UploadResponse
from app.repositories.images import ImageRepository
from app.services.imagery import ImageryService

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("", response_model=UploadResponse)
def upload_image(
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
    file: Annotated[UploadFile, File(...)],
    capture_date: Annotated[datetime | None, Form()] = None,
) -> UploadResponse:
    asset = ImageryService(ImageRepository(db)).save_upload(current_user.id, file, capture_date=capture_date)
    return UploadResponse(asset=ImageAssetRead.model_validate(asset))


@router.get("", response_model=list[ImageAssetRead])
def list_uploads(db: DbSession, current_user: Annotated[User, Depends(get_current_user)]) -> list[ImageAssetRead]:
    assets = ImageRepository(db).list_for_user(current_user.id)
    return [ImageAssetRead.model_validate(asset) for asset in assets]
