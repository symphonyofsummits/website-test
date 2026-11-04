"""
Pull latest Instagram posts via Basic Display API and cache them in DB.
Run on cron every hour.
"""
import asyncio
from datetime import datetime

import httpx
from sqlalchemy import select

from app.config import settings
from app.database import session_scope
from app.models import InstagramPost


async def main():
    if not settings.IG_ACCESS_TOKEN:
        print("IG_ACCESS_TOKEN not configured — skipping")
        return

    url = f"https://graph.instagram.com/{settings.IG_USER_ID}/media"
    params = {
        "fields": "id,media_type,media_url,thumbnail_url,permalink,caption,timestamp",
        "access_token": settings.IG_ACCESS_TOKEN,
        "limit": 12,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json().get("data", [])

    async with session_scope() as db:
        for post in data:
            existing = (await db.execute(
                select(InstagramPost).where(InstagramPost.ig_media_id == post["id"])
            )).scalar_one_or_none()
            if existing:
                continue
            db.add(InstagramPost(
                ig_media_id=post["id"],
                media_type=post.get("media_type"),
                media_url=post["media_url"],
                thumbnail_url=post.get("thumbnail_url"),
                permalink=post.get("permalink"),
                caption=post.get("caption"),
                posted_at=datetime.fromisoformat(post["timestamp"].replace("Z", "+00:00")),
            ))
    print(f"Synced {len(data)} Instagram posts")


if __name__ == "__main__":
    asyncio.run(main())
