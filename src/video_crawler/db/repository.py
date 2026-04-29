from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from video_crawler.models.db import (
    CrawlLogRow,
    RankingEntryRow,
    RankingSnapshotRow,
    VideoRow,
    VideoStatRow,
)
from video_crawler.models.domain import RankingSnapshot, Video

# Re-export for type hints in API layer
__all__ = ["VideoRepository"]


class VideoRepository:
    def __init__(self, session: Session):
        self.session = session

    def upsert_video(self, video: Video) -> VideoRow:
        row = self.session.execute(
            select(VideoRow).where(
                VideoRow.platform == video.platform, VideoRow.video_id == video.video_id
            )
        ).scalar_one_or_none()

        if row is None:
            row = VideoRow(
                platform=video.platform,
                video_id=video.video_id,
                title=video.title,
                author_id=video.author_id,
                author_name=video.author_name,
                description=video.description,
                cover_url=video.cover_url,
                duration=video.duration,
                category=video.category,
                tags=video.tags,
                url=video.url,
                publish_time=video.publish_time,
            )
            self.session.add(row)
            self.session.flush()
        else:
            row.title = video.title
            row.author_name = video.author_name
            row.description = video.description
            row.cover_url = video.cover_url
            row.duration = video.duration
            row.category = video.category
            row.tags = video.tags
            row.url = video.url
            row.updated_at = datetime.now(UTC)

        stat = VideoStatRow(
            video_id=row.id,
            view_count=video.view_count,
            like_count=video.like_count,
            coin_count=video.coin_count,
            favorite_count=video.favorite_count,
            reply_count=video.reply_count,
            share_count=video.share_count,
            danmaku_count=video.danmaku_count,
        )
        self.session.add(stat)
        return row

    def save_ranking_snapshot(self, snapshot: RankingSnapshot) -> RankingSnapshotRow:
        snap_row = RankingSnapshotRow(
            platform=snapshot.platform,
            category=snapshot.category,
            snapshot_time=snapshot.snapshot_time,
        )
        self.session.add(snap_row)
        self.session.flush()

        for entry in snapshot.entries:
            video_row = self.upsert_video(entry.video)
            entry_row = RankingEntryRow(
                snapshot_id=snap_row.id,
                rank=entry.rank,
                video_id=video_row.id,
                score=entry.score,
            )
            self.session.add(entry_row)

        return snap_row

    def get_video_count(self, platform: str | None = None) -> int:
        stmt = select(func.count(VideoRow.id))
        if platform:
            stmt = stmt.where(VideoRow.platform == platform)
        return self.session.execute(stmt).scalar_one()

    def get_stat_count(self) -> int:
        return self.session.execute(select(func.count(VideoStatRow.id))).scalar_one()

    def get_ranking_snapshot_count(self, platform: str | None = None) -> int:
        stmt = select(func.count(RankingSnapshotRow.id))
        if platform:
            stmt = stmt.where(RankingSnapshotRow.platform == platform)
        return self.session.execute(stmt).scalar_one()

    def get_latest_crawl_log(self, platform: str | None = None) -> CrawlLogRow | None:
        stmt = select(CrawlLogRow).order_by(CrawlLogRow.finished_at.desc()).limit(1)
        if platform:
            stmt = stmt.where(CrawlLogRow.platform == platform)
        return self.session.execute(stmt).scalar_one_or_none()

    def log_crawl(
        self,
        platform: str,
        job_type: str,
        status: str,
        items_count: int = 0,
        error_message: str | None = None,
        started_at: datetime | None = None,
    ) -> CrawlLogRow:
        log = CrawlLogRow(
            platform=platform,
            job_type=job_type,
            status=status,
            items_count=items_count,
            error_message=error_message,
            started_at=started_at,
        )
        self.session.add(log)
        return log

    # --- API query methods ---

    def list_videos(
        self,
        platform: str | None = None,
        category: str | None = None,
        keyword: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[VideoRow], int]:
        stmt = select(VideoRow)
        count_stmt = select(func.count(VideoRow.id))

        if platform:
            stmt = stmt.where(VideoRow.platform == platform)
            count_stmt = count_stmt.where(VideoRow.platform == platform)
        if category:
            stmt = stmt.where(VideoRow.category == category)
            count_stmt = count_stmt.where(VideoRow.category == category)
        if keyword:
            pattern = f"%{keyword}%"
            stmt = stmt.where(VideoRow.title.ilike(pattern))
            count_stmt = count_stmt.where(VideoRow.title.ilike(pattern))

        total = self.session.execute(count_stmt).scalar_one()
        rows = (
            self.session.execute(
                stmt.order_by(VideoRow.updated_at.desc()).limit(limit).offset(offset)
            )
            .scalars()
            .all()
        )
        return list(rows), total

    def get_video(self, platform: str, video_id: str) -> VideoRow | None:
        return self.session.execute(
            select(VideoRow).where(
                VideoRow.platform == platform, VideoRow.video_id == video_id
            )
        ).scalar_one_or_none()

    def get_video_stats_history(
        self, db_video_id: int, limit: int = 100
    ) -> list[VideoStatRow]:
        return list(
            self.session.execute(
                select(VideoStatRow)
                .where(VideoStatRow.video_id == db_video_id)
                .order_by(VideoStatRow.crawled_at.asc())
                .limit(limit)
            )
            .scalars()
            .all()
        )

    def get_latest_ranking(
        self, platform: str, category: str = "all"
    ) -> RankingSnapshotRow | None:
        return self.session.execute(
            select(RankingSnapshotRow)
            .where(
                RankingSnapshotRow.platform == platform,
                RankingSnapshotRow.category == category,
            )
            .order_by(RankingSnapshotRow.snapshot_time.desc())
            .limit(1)
        ).scalar_one_or_none()

    def get_ranking_entries(self, snapshot_id: int) -> list[tuple[RankingEntryRow, VideoRow]]:
        rows = self.session.execute(
            select(RankingEntryRow, VideoRow)
            .join(VideoRow, RankingEntryRow.video_id == VideoRow.id)
            .where(RankingEntryRow.snapshot_id == snapshot_id)
            .order_by(RankingEntryRow.rank)
        ).all()
        return [(entry, video) for entry, video in rows]

    def get_ranking_history(
        self, platform: str, category: str = "all", days: int = 7
    ) -> list[RankingSnapshotRow]:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        return list(
            self.session.execute(
                select(RankingSnapshotRow)
                .where(
                    RankingSnapshotRow.platform == platform,
                    RankingSnapshotRow.category == category,
                    RankingSnapshotRow.snapshot_time >= cutoff,
                )
                .order_by(RankingSnapshotRow.snapshot_time.desc())
            )
            .scalars()
            .all()
        )

    def get_crawl_logs(self, limit: int = 20) -> list[CrawlLogRow]:
        return list(
            self.session.execute(
                select(CrawlLogRow).order_by(CrawlLogRow.finished_at.desc()).limit(limit)
            )
            .scalars()
            .all()
        )

    def get_top_videos_by_views(
        self, platform: str | None = None, limit: int = 10
    ) -> list[tuple[VideoRow, VideoStatRow]]:
        latest_stat = (
            select(
                VideoStatRow.video_id,
                func.max(VideoStatRow.id).label("max_id"),
            )
            .group_by(VideoStatRow.video_id)
            .subquery()
        )
        stmt = (
            select(VideoRow, VideoStatRow)
            .join(latest_stat, VideoRow.id == latest_stat.c.video_id)
            .join(VideoStatRow, VideoStatRow.id == latest_stat.c.max_id)
            .order_by(VideoStatRow.view_count.desc())
            .limit(limit)
        )
        if platform:
            stmt = stmt.where(VideoRow.platform == platform)
        return [(video, stat) for video, stat in self.session.execute(stmt).all()]
