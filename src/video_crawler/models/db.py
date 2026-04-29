from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow():
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class VideoRow(Base):
    __tablename__ = "videos"
    __table_args__ = (
        UniqueConstraint("platform", "video_id", name="uq_platform_video_id"),
        Index("idx_videos_platform", "platform"),
        Index("idx_videos_publish_time", "publish_time"),
        Index("idx_videos_category", "platform", "category"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    video_id: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[str] = mapped_column(String(64), nullable=False)
    author_name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    cover_url: Mapped[str] = mapped_column(Text, default="")
    duration: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[str] = mapped_column(String(64), default="")
    tags: Mapped[dict | list] = mapped_column(JSON, default=list)
    url: Mapped[str] = mapped_column(Text, default="")
    publish_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )

    stats: Mapped[list["VideoStatRow"]] = relationship(back_populates="video")


class VideoStatRow(Base):
    __tablename__ = "video_stats"
    __table_args__ = (
        Index("idx_stats_video_id", "video_id"),
        Index("idx_stats_crawled_at", "crawled_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_id: Mapped[int] = mapped_column(Integer, ForeignKey("videos.id"), nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    coin_count: Mapped[int] = mapped_column(Integer, default=0)
    favorite_count: Mapped[int] = mapped_column(Integer, default=0)
    reply_count: Mapped[int] = mapped_column(Integer, default=0)
    share_count: Mapped[int] = mapped_column(Integer, default=0)
    danmaku_count: Mapped[int] = mapped_column(Integer, default=0)
    crawled_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    video: Mapped["VideoRow"] = relationship(back_populates="stats")


class RankingSnapshotRow(Base):
    __tablename__ = "ranking_snapshots"
    __table_args__ = (
        Index("idx_ranking_snapshots_lookup", "platform", "category", "snapshot_time"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot_time: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    entries: Mapped[list["RankingEntryRow"]] = relationship(back_populates="snapshot")


class RankingEntryRow(Base):
    __tablename__ = "ranking_entries"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "rank", name="uq_snapshot_rank"),
        Index("idx_ranking_entries_snapshot", "snapshot_id"),
        Index("idx_ranking_entries_video", "video_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ranking_snapshots.id"), nullable=False
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    video_id: Mapped[int] = mapped_column(Integer, ForeignKey("videos.id"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0)

    snapshot: Mapped["RankingSnapshotRow"] = relationship(back_populates="entries")


class CrawlLogRow(Base):
    __tablename__ = "crawl_logs"
    __table_args__ = (Index("idx_crawl_logs_platform", "platform", "job_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    job_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    items_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class WatchlistRow(Base):
    __tablename__ = "watchlist"
    __table_args__ = (
        UniqueConstraint("platform", "target_type", "target_id", name="uq_watchlist_target"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    target_type: Mapped[str] = mapped_column(String(16), nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(256), default="")
    notify: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
