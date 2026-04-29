from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from video_crawler.api.deps import get_db
from video_crawler.db.repository import VideoRepository

router = APIRouter(prefix="/api/rankings", tags=["rankings"])


@router.get("/{platform}")
def get_latest_ranking(
    platform: str,
    category: str = "all",
    session: Session = Depends(get_db),
):
    repo = VideoRepository(session)
    snapshot = repo.get_latest_ranking(platform, category)
    if snapshot is None:
        return {"snapshot_time": None, "category": category, "entries": []}

    entries = repo.get_ranking_entries(snapshot.id)
    return {
        "snapshot_time": snapshot.snapshot_time.isoformat() if snapshot.snapshot_time else None,
        "category": snapshot.category,
        "entries": [
            {
                "rank": entry.rank,
                "score": entry.score,
                "video": {
                    "platform": video.platform,
                    "video_id": video.video_id,
                    "title": video.title,
                    "author_name": video.author_name,
                    "cover_url": video.cover_url,
                    "url": video.url,
                    "category": video.category,
                },
            }
            for entry, video in entries
        ],
    }


@router.get("/{platform}/history")
def get_ranking_history(
    platform: str,
    category: str = "all",
    days: int = Query(7, ge=1, le=90),
    session: Session = Depends(get_db),
):
    repo = VideoRepository(session)
    snapshots = repo.get_ranking_history(platform, category, days)
    result = []
    for snap in snapshots:
        entries = repo.get_ranking_entries(snap.id)
        result.append(
            {
                "snapshot_time": snap.snapshot_time.isoformat() if snap.snapshot_time else None,
                "category": snap.category,
                "entry_count": len(entries),
                "top_10": [
                    {
                        "rank": entry.rank,
                        "score": entry.score,
                        "video_id": video.video_id,
                        "title": video.title,
                    }
                    for entry, video in entries[:10]
                ],
            }
        )
    return {"platform": platform, "category": category, "days": days, "snapshots": result}
