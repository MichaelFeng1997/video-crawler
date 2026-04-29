from __future__ import annotations

from datetime import UTC, datetime

from video_crawler.models.domain import RankingEntry, RankingSnapshot, Video


def parse_video(item: dict) -> Video:
    stat = item.get("stat", {})
    owner = item.get("owner", {})
    return Video(
        platform="bilibili",
        video_id=item.get("bvid", ""),
        title=item.get("title", ""),
        author_id=str(owner.get("mid", "")),
        author_name=owner.get("name", ""),
        description=item.get("desc", ""),
        cover_url=item.get("pic", ""),
        duration=item.get("duration", 0),
        view_count=stat.get("view", 0),
        like_count=stat.get("like", 0),
        coin_count=stat.get("coin", 0),
        favorite_count=stat.get("favorite", 0),
        reply_count=stat.get("reply", 0),
        share_count=stat.get("share", 0),
        danmaku_count=stat.get("danmaku", 0),
        publish_time=datetime.fromtimestamp(item["pubdate"]) if item.get("pubdate") else None,
        tags=[],
        category=item.get("tname", ""),
        url=f"https://www.bilibili.com/video/{item.get('bvid', '')}",
    )


def parse_popular_response(data: dict) -> list[Video]:
    items = data.get("data", {}).get("list", [])
    return [parse_video(item) for item in items]


def parse_ranking_response(data: dict, category: str) -> RankingSnapshot:
    items = data.get("data", {}).get("list", [])
    entries = []
    for i, item in enumerate(items, start=1):
        video = parse_video(item)
        score = item.get("score", 0)
        entries.append(RankingEntry(rank=i, video=video, score=score))
    return RankingSnapshot(
        platform="bilibili",
        category=category,
        snapshot_time=datetime.now(UTC),
        entries=entries,
    )
