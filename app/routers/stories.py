"""Public stories/blog + Instagram sidebar."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import InstagramPost, Story
from app.models.enums import StoryStatus
from app.schemas.schemas import InstagramPostOut, StoryDetailOut, StoryListOut

router = APIRouter(tags=["stories"])


@router.get("/stories", response_model=List[StoryListOut])
async def list_stories(
    db: AsyncSession = Depends(get_db),
    category: str = Query(None),
    limit: int = Query(20, ge=1, le=50),
):
    stmt = select(Story).where(Story.status == StoryStatus.PUBLISHED.value)
    if category:
        stmt = stmt.where(Story.category == category)
    stmt = stmt.order_by(Story.published_at.desc()).limit(limit)
    return (await db.execute(stmt)).scalars().all()


@router.get("/stories/{slug}", response_model=StoryDetailOut)
async def story_detail(slug: str, db: AsyncSession = Depends(get_db)):
    story = (
        await db.execute(select(Story).where(
            Story.slug == slug, Story.status == StoryStatus.PUBLISHED.value,
        ))
    ).scalar_one_or_none()
    if not story:
        raise HTTPException(404, "Story not found")
    story.view_count += 1
    return story


@router.get("/instagram", response_model=List[InstagramPostOut])
async def instagram_feed(db: AsyncSession = Depends(get_db), limit: int = Query(6, ge=1, le=20)):
    """For the right-sidebar Instagram rail — reads cached posts (refreshed by cron)."""
    stmt = select(InstagramPost).order_by(InstagramPost.posted_at.desc()).limit(limit)
    return (await db.execute(stmt)).scalars().all()
