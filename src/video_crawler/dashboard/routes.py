from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from video_crawler.api.deps import get_db
from video_crawler.db.repository import VideoRepository

router = APIRouter(tags=["dashboard"])

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))

CATEGORY_LABELS = {
    "all": "全站",
    "animation": "动画",
    "music": "音乐",
    "dance": "舞蹈",
    "game": "游戏",
    "knowledge": "知识",
    "tech": "科技",
    "sports": "运动",
    "car": "汽车",
    "life": "生活",
    "food": "美食",
    "animal": "动物圈",
    "fashion": "时尚",
    "entertainment": "娱乐",
    "movie": "电影",
    "tv": "电视剧",
    "documentary": "纪录片",
}


@router.get("/")
def dashboard_home(request: Request, session: Session = Depends(get_db)):
    repo = VideoRepository(session)
    stats = {
        "video_count": repo.get_video_count(),
        "stat_count": repo.get_stat_count(),
        "ranking_snapshots": repo.get_ranking_snapshot_count(),
    }
    last_crawl = repo.get_latest_crawl_log()
    crawl_logs = repo.get_crawl_logs(limit=10)
    top_videos = repo.get_top_videos_by_views(limit=5)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "stats": stats,
            "last_crawl": last_crawl,
            "crawl_logs": crawl_logs,
            "top_videos": top_videos,
        },
    )


@router.get("/videos")
def videos_page(request: Request):
    return templates.TemplateResponse(
        request,
        "videos.html",
        {"categories": CATEGORY_LABELS},
    )


@router.get("/videos/{platform}/{video_id}")
def video_detail_page(
    request: Request,
    platform: str,
    video_id: str,
    session: Session = Depends(get_db),
):
    repo = VideoRepository(session)
    video = repo.get_video(platform, video_id)
    return templates.TemplateResponse(
        request,
        "video_detail.html",
        {
            "video": video,
            "platform": platform,
            "video_id": video_id,
        },
    )


@router.get("/rankings")
def rankings_page(request: Request):
    return templates.TemplateResponse(
        request,
        "rankings.html",
        {"categories": CATEGORY_LABELS},
    )
