from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from video_crawler.api.deps import get_db
from video_crawler.api.routes import health, rankings, videos
from video_crawler.dashboard.routes import router as dashboard_router
from video_crawler.db.repository import VideoRepository
from video_crawler.models.db import Base
from video_crawler.models.domain import RankingEntry, RankingSnapshot, Video

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=engine)


def override_get_db():
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


def _create_test_app() -> FastAPI:
    from pathlib import Path

    app = FastAPI()
    app.include_router(health.router)
    app.include_router(videos.router)
    app.include_router(rankings.router)

    dashboard_dir = Path(__file__).resolve().parent.parent / "src" / "video_crawler" / "dashboard"
    app.mount("/static", StaticFiles(directory=str(dashboard_dir / "static")), name="static")
    app.include_router(dashboard_router)

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(engine)

    session = TestSession()
    repo = VideoRepository(session)
    for i in range(3):
        repo.upsert_video(
            Video(
                platform="bilibili",
                video_id=f"BV1dash{i:04d}",
                title=f"Dashboard Test Video {i}",
                author_id=str(2000 + i),
                author_name=f"DashAuthor{i}",
                view_count=(i + 1) * 50000,
                like_count=(i + 1) * 1000,
                category="tech",
            )
        )
    repo.save_ranking_snapshot(
        RankingSnapshot(
            platform="bilibili",
            category="all",
            snapshot_time=datetime.now(UTC),
            entries=[
                RankingEntry(
                    rank=1,
                    video=Video(
                        platform="bilibili",
                        video_id="BV1dashrank1",
                        title="Dashboard Rank 1",
                        author_id="9010",
                        author_name="RankDash",
                        view_count=500000,
                    ),
                    score=200000,
                ),
            ],
        )
    )
    repo.log_crawl("bilibili", "popular", "success", 3, started_at=datetime.now(UTC))
    session.commit()
    session.close()

    app = _create_test_app()
    with TestClient(app) as c:
        yield c

    Base.metadata.drop_all(engine)


def test_dashboard_home(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "视频总数" in resp.text
    assert "统计记录" in resp.text


def test_dashboard_home_has_crawl_logs(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "bilibili" in resp.text
    assert "success" in resp.text


def test_videos_page(client):
    resp = client.get("/videos")
    assert resp.status_code == 200
    assert "视频浏览" in resp.text
    assert "filterKeyword" in resp.text


def test_video_detail_page(client):
    resp = client.get("/videos/bilibili/BV1dash0000")
    assert resp.status_code == 200
    assert "Dashboard Test Video 0" in resp.text
    assert "statsChart" in resp.text


def test_video_detail_not_found(client):
    resp = client.get("/videos/bilibili/NONEXIST")
    assert resp.status_code == 200
    assert "视频未找到" in resp.text


def test_rankings_page(client):
    resp = client.get("/rankings")
    assert resp.status_code == 200
    assert "排行榜" in resp.text
    assert "categorySelect" in resp.text
