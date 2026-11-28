"""
Local file storage helper for pet photo uploads.
Stores images under `backend/uploads/` and serves them via StaticFiles in dev.
Designed as a small interface that can be swapped for S3 or Cloudinary later.
"""

import os
import uuid
from pathlib import Path
from typing import Tuple

from fastapi import HTTPException, UploadFile, status

# backend/ directory (two levels up from app/services/storage.py)
BACKEND_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BACKEND_ROOT / "uploads"

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB


def ensure_upload_dir() -> Path:
    """Ensure the local uploads directory exists and return its Path."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR


async def save_pet_photo(pet_id: str, file: UploadFile) -> str:
    """
    Validate and save an uploaded pet photo.
    Returns the public relative URL path `/uploads/<filename>`.
    """
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image type '{content_type}'. Allowed: JPEG, PNG, WebP.",
        )

    data = await file.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds maximum allowed size of {MAX_IMAGE_BYTES // (1024 * 1024)} MB.",
        )

    ext = ALLOWED_IMAGE_TYPES[content_type]
    safe_pet_id = "".join(c for c in pet_id if c.isalnum() or c in ("_", "-"))
    filename = f"{safe_pet_id}_{uuid.uuid4().hex[:10]}{ext}"

    upload_dir = ensure_upload_dir()
    dest = upload_dir / filename
    dest.write_bytes(data)

    return f"/uploads/{filename}"
