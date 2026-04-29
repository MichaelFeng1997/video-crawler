from __future__ import annotations

import re
from datetime import UTC, datetime

from video_crawler.models.domain import RankingEntry, RankingSnapshot, Video
from video_crawler.platforms.youtube.constants import CATEGORY_NAMES

_DURATION_RE = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")


def parse_duration(iso_duration: str) -> int:
    m = _DURATION_RE.match(iso_duration)
    if not m:
        return 0
    hours = int(m.group(1) or 0)
    minutes = int(m.group(2) or 0)
    seconds = int(m.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def _best_thumbnail(snippet: dict) -> str:
    thumbs = snippet.get("thumbnails", {})
    for key in ("high", "medium", "default"):
        if key in thumbs:
            return thumbs[key].get("url", "")
    return ""


def _parse_publish_time(snippet: dict) -> datetime | None:
    raw = snippet.get("publishedAt", "")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_video(item: dict) -> Video:
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    content = item.get("contentDetails", {})
    video_id = item.get("id", "")
    category_id = snippet.get("categoryId", "")

    return Video(
        platform="youtube",
        video_id=video_id,
        title=snippet.get("title", ""),
        author_id=snippet.get("channelId", ""),
        author_name=snippet.get("channelTitle", ""),
        description=snippet.get("description", ""),
        cover_url=_best_thumbnail(snippet),
        duration=parse_duration(content.get("duration", "")),
        view_count=int(stats.get("viewCount", 0)),
        like_count=int(stats.get("likeCount", 0)),
        reply_count=int(stats.get("commentCount", 0)),
        publish_time=_parse_publish_time(snippet),
        tags=snippet.get("tags", []),
        category=CATEGORY_NAMES.get(category_id, category_id),
        url=f"https://www.youtube.com/watch?v={video_id}",
    )


def parse_popular_response(data: dict) -> list[Video]:
    return [parse_video(item) for item in data.get("items", [])]


def parse_ranking_response(data: dict, category: str) -> RankingSnapshot:
    entries = []
    for i, item in enumerate(data.get("items", []), start=1):
        video = parse_video(item)
        entries.append(RankingEntry(rank=i, video=video, score=video.view_count))
    return RankingSnapshot(
        platform="youtube",
        category=category,
        snapshot_time=datetime.now(UTC),
        entries=entries,
    )
