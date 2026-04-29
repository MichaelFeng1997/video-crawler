from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from video_crawler.api.deps import get_db
from video_crawler.db.repository import VideoRepository

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health_check(session: Session = Depends(get_db)):
    repo = VideoRepository(session)
    last_crawl = repo.get_latest_crawl_log()
    return {
        "status": "ok",
        "video_count": repo.get_video_count(),
        "stat_count": repo.get_stat_count(),
        "ranking_snapshots": repo.get_ranking_snapshot_count(),
        "last_crawl": {
            "time": last_crawl.finished_at.isoformat() if last_crawl else None,
            "status": last_crawl.status if last_crawl else None,
            "platform": last_crawl.platform if last_crawl else None,
        },
    }
