from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from video_crawler.api.deps import get_db
from video_crawler.db.repository import VideoRepository

router = APIRouter(prefix="/api/videos", tags=["videos"])


def _video_to_dict(row) -> dict:
    return {
        "platform": row.platform,
        "video_id": row.video_id,
        "title": row.title,
        "author_id": row.author_id,
        "author_name": row.author_name,
        "description": row.description,
        "cover_url": row.cover_url,
        "duration": row.duration,
        "category": row.category,
        "tags": row.tags or [],
        "url": row.url,
        "publish_time": row.publish_time.isoformat() if row.publish_time else None,
        "first_seen_at": row.first_seen_at.isoformat() if row.first_seen_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _stat_to_dict(row) -> dict:
    return {
        "view_count": row.view_count,
        "like_count": row.like_count,
        "coin_count": row.coin_count,
        "favorite_count": row.favorite_count,
        "reply_count": row.reply_count,
        "share_count": row.share_count,
        "danmaku_count": row.danmaku_count,
        "crawled_at": row.crawled_at.isoformat() if row.crawled_at else None,
    }


@router.get("")
def list_videos(
    platform: str | None = None,
    category: str | None = None,
    keyword: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_db),
):
    repo = VideoRepository(session)
    rows, total = repo.list_videos(
        platform=platform, category=category, keyword=keyword, limit=limit, offset=offset
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [_video_to_dict(r) for r in rows],
    }


@router.get("/{platform}/{video_id}")
def get_video_detail(
    platform: str,
    video_id: str,
    session: Session = Depends(get_db),
):
    repo = VideoRepository(session)
    row = repo.get_video(platform, video_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Video not found")

    stats = repo.get_video_stats_history(row.id)
    latest_stat = stats[-1] if stats else None

    result = _video_to_dict(row)
    if latest_stat:
        result["latest_stats"] = _stat_to_dict(latest_stat)
    result["stats_history"] = [_stat_to_dict(s) for s in stats]

    return result
