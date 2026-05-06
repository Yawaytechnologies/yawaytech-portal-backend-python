from __future__ import annotations

from io import BytesIO
from typing import Iterable

from PIL import Image, ImageOps


ALLOWED_IMAGE_MIME = {"image/jpeg", "image/jpg", "image/png", "image/webp"}


def validate_image_upload(
    data: bytes,
    content_type: str,
    *,
    allowed_mime: Iterable[str] = ALLOWED_IMAGE_MIME,
    max_bytes: int,
) -> str:
    mime = (content_type or "").lower()
    if mime not in set(allowed_mime):
        raise ValueError("Only JPG/PNG/WEBP images are allowed")
    if not data:
        raise ValueError("Empty image file")
    if len(data) > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        raise ValueError(f"Image too large (max {max_mb:g}MB)")
    return "image/jpeg" if mime == "image/jpg" else mime


def optimize_image_for_storage(
    data: bytes,
    *,
    max_dimension: int = 768,
    quality: int = 75,
) -> bytes:
    """Normalize uploaded images to bounded JPEG bytes before storage."""
    with Image.open(BytesIO(data)) as image:
        image = ImageOps.exif_transpose(image)
        image.thumbnail((max_dimension, max_dimension))

        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        out = BytesIO()
        image.save(out, format="JPEG", quality=quality, optimize=True, progressive=True)
        return out.getvalue()
