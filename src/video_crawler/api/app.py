from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from video_crawler.api.routes import health, rankings, videos
from video_crawler.dashboard.routes import router as dashboard_router
from video_crawler.db.engine import init_db
from video_crawler.scheduler.jobs import create_scheduler

logger = logging.getLogger(__name__)

_DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "dashboard"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialized")

    scheduler = create_scheduler()
    scheduler.start()
    logger.info("Scheduler started with %d jobs", len(scheduler.get_jobs()))

    yield

    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")


def create_app() -> FastAPI:
    import video_crawler.platforms  # noqa: F401 — register adapters

    app = FastAPI(
        title="Video Crawler",
        description="多平台视频数据采集与分析工具",
        version="0.3.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(videos.router)
    app.include_router(rankings.router)

    app.mount("/static", StaticFiles(directory=str(_DASHBOARD_DIR / "static")), name="static")
    app.include_router(dashboard_router)

    return app
