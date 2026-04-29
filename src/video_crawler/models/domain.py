from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Video:
    platform: str
    video_id: str
    title: str
    author_id: str
    author_name: str
    description: str = ""
    cover_url: str = ""
    duration: int = 0
    view_count: int = 0
    like_count: int = 0
    coin_count: int = 0
    favorite_count: int = 0
    reply_count: int = 0
    share_count: int = 0
    danmaku_count: int = 0
    publish_time: datetime | None = None
    tags: list[str] = field(default_factory=list)
    category: str = ""
    url: str = ""
    crawled_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class RankingEntry:
    rank: int
    video: Video
    score: int = 0


@dataclass
class RankingSnapshot:
    platform: str
    category: str
    snapshot_time: datetime
    entries: list[RankingEntry] = field(default_factory=list)
