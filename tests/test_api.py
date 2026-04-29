from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from video_crawler.api.deps import get_db
from video_crawler.api.routes import health, rankings, videos
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
    app = FastAPI()
    app.include_router(health.router)
    app.include_router(videos.router)
    app.include_router(rankings.router)
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
                video_id=f"BV1api{i:04d}",
                title=f"API Test Video {i}",
                author_id=str(1000 + i),
                author_name=f"Author{i}",
                view_count=(i + 1) * 10000,
                like_count=(i + 1) * 500,
                category="tech" if i % 2 == 0 else "game",
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
                        video_id="BV1rank0001",
                        title="Rank 1 Video",
                        author_id="9001",
                        author_name="RankAuthor",
                        view_count=999999,
                    ),
                    score=150000,
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


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["video_count"] >= 3
    assert data["last_crawl"]["status"] == "success"


def test_list_videos(client):
    resp = client.get("/api/videos")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 3
    assert len(data["items"]) >= 3
    assert data["items"][0]["platform"] == "bilibili"


def test_list_videos_with_filter(client):
    resp = client.get("/api/videos", params={"category": "tech"})
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["category"] == "tech"


def test_list_videos_with_keyword(client):
    resp = client.get("/api/videos", params={"keyword": "Video 0"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


def test_list_videos_pagination(client):
    resp = client.get("/api/videos", params={"limit": 2, "offset": 0})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0


def test_get_video_detail(client):
    resp = client.get("/api/videos/bilibili/BV1api0000")
    assert resp.status_code == 200
    data = resp.json()
    assert data["video_id"] == "BV1api0000"
    assert data["title"] == "API Test Video 0"
    assert "stats_history" in data
    assert len(data["stats_history"]) >= 1


def test_get_video_not_found(client):
    resp = client.get("/api/videos/bilibili/NONEXISTENT")
    assert resp.status_code == 404


def test_get_latest_ranking(client):
    resp = client.get("/api/rankings/bilibili")
    assert resp.status_code == 200
    data = resp.json()
    assert data["category"] == "all"
    assert len(data["entries"]) >= 1
    assert data["entries"][0]["rank"] == 1
    assert data["entries"][0]["score"] == 150000


def test_get_ranking_empty(client):
    resp = client.get("/api/rankings/youtube")
    assert resp.status_code == 200
    data = resp.json()
    assert data["entries"] == []


def test_get_ranking_history(client):
    resp = client.get("/api/rankings/bilibili/history", params={"days": 7})
    assert resp.status_code == 200
    data = resp.json()
    assert data["platform"] == "bilibili"
    assert len(data["snapshots"]) >= 1
