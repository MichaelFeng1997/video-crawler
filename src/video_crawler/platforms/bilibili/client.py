from __future__ import annotations

import logging
from datetime import UTC, datetime

from video_crawler.config import settings
from video_crawler.models.domain import RankingSnapshot, Video
from video_crawler.platforms.base import PlatformAdapter, register_platform
from video_crawler.platforms.bilibili.constants import (
    BASE_URL,
    DEFAULT_HEADERS,
    POPULAR_URL,
    RANKING_CATEGORIES,
    RANKING_URL,
    SEARCH_URL,
)
from video_crawler.platforms.bilibili.parser import parse_popular_response, parse_ranking_response
from video_crawler.utils.http import RateLimitedClient

logger = logging.getLogger(__name__)


@register_platform
class BilibiliAdapter(PlatformAdapter):
    platform_name = "bilibili"

    def __init__(self):
        self._client = RateLimitedClient(
            requests_per_minute=settings.bilibili_rpm,
            max_concurrent=3,
        )

    async def get_popular_videos(self, category: str | None = None, page: int = 1) -> list[Video]:
        url = BASE_URL + POPULAR_URL
        params = {"pn": page, "ps": 20}
        resp = await self._client.get(url, params=params, headers=DEFAULT_HEADERS)
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 0:
            logger.error("Bilibili API error: %s", data.get("message", "unknown"))
            return []

        videos = parse_popular_response(data)
        logger.info("Fetched %d popular videos (page %d)", len(videos), page)
        return videos

    async def get_rankings(self, category: str = "all") -> RankingSnapshot:
        url = BASE_URL + RANKING_URL
        tid = RANKING_CATEGORIES.get(category, 0)
        params = {"rid": tid, "type": "all"}
        resp = await self._client.get(url, params=params, headers=DEFAULT_HEADERS)
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 0:
            logger.error("Bilibili ranking API error: %s", data.get("message", "unknown"))
            return RankingSnapshot(
                platform="bilibili",
                category=category,
                snapshot_time=datetime.now(UTC),
                entries=[],
            )

        snapshot = parse_ranking_response(data, category)
        logger.info(
            "Fetched %d ranking entries for category '%s'", len(snapshot.entries), category
        )
        return snapshot

    async def search_videos(self, keyword: str, page: int = 1) -> list[Video]:
        url = BASE_URL + SEARCH_URL
        params = {
            "search_type": "video",
            "keyword": keyword,
            "page": page,
            "pagesize": 20,
        }
        resp = await self._client.get(url, params=params, headers=DEFAULT_HEADERS)
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 0:
            logger.error("Bilibili search API error: %s", data.get("message", "unknown"))
            return []

        items = data.get("data", {}).get("result", [])
        from video_crawler.platforms.bilibili.parser import parse_video

        return [parse_video(item) for item in items if item.get("bvid")]

    async def close(self) -> None:
        await self._client.close()
