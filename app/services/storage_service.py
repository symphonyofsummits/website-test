"""Thin wrapper over Supabase Storage (works with S3-compatible like R2 too)."""
import logging
import mimetypes
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def upload_to_supabase(
    file_bytes: bytes,
    filename: str,
    folder: str = "uploads",
    content_type: Optional[str] = None,
) -> str:
    """Upload bytes to Supabase Storage and return the public URL."""
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "bin"
    key = f"{folder}/{datetime.now(timezone.utc).strftime('%Y/%m')}/{uuid4().hex}.{ext}"
    content_type = content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"

    url = f"{settings.SUPABASE_URL}/storage/v1/object/{settings.SUPABASE_STORAGE_BUCKET}/{key}"
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": content_type,
        "x-upsert": "true",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(url, headers=headers, content=file_bytes)
        if r.status_code >= 400:
            logger.error("Supabase upload failed %s: %s", r.status_code, r.text)
            r.raise_for_status()
    public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_STORAGE_BUCKET}/{key}"
    return public_url
