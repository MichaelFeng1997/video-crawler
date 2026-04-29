from datetime import UTC, datetime

from video_crawler.db.repository import VideoRepository
from video_crawler.models.domain import RankingEntry, RankingSnapshot, Video


def _make_video(**overrides) -> Video:
    defaults = dict(
        platform="bilibili",
        video_id="BV1test123456",
        title="Test Video",
        author_id="12345",
        author_name="TestAuthor",
        view_count=1000,
        like_count=100,
    )
    defaults.update(overrides)
    return Video(**defaults)


def test_upsert_video_insert(db_session):
    repo = VideoRepository(db_session)
    video = _make_video()
    row = repo.upsert_video(video)
    db_session.commit()

    assert row.id is not None
    assert row.video_id == "BV1test123456"
    assert repo.get_video_count() == 1
    assert repo.get_stat_count() == 1


def test_upsert_video_update(db_session):
    repo = VideoRepository(db_session)
    video = _make_video(view_count=1000)
    repo.upsert_video(video)
    db_session.commit()

    video2 = _make_video(view_count=2000, title="Updated Title")
    repo.upsert_video(video2)
    db_session.commit()

    assert repo.get_video_count() == 1
    assert repo.get_stat_count() == 2


def test_save_ranking_snapshot(db_session):
    repo = VideoRepository(db_session)
    snapshot = RankingSnapshot(
        platform="bilibili",
        category="all",
        snapshot_time=datetime.now(UTC),
        entries=[
            RankingEntry(rank=1, video=_make_video(video_id="BV001"), score=100),
            RankingEntry(rank=2, video=_make_video(video_id="BV002"), score=80),
        ],
    )
    snap_row = repo.save_ranking_snapshot(snapshot)
    db_session.commit()

    assert snap_row.id is not None
    assert repo.get_ranking_snapshot_count() == 1
    assert repo.get_video_count() == 2


def test_log_crawl(db_session):
    repo = VideoRepository(db_session)
    repo.log_crawl("bilibili", "popular", "success", 20, started_at=datetime.now(UTC))
    db_session.commit()

    log = repo.get_latest_crawl_log("bilibili")
    assert log is not None
    assert log.status == "success"
    assert log.items_count == 20
