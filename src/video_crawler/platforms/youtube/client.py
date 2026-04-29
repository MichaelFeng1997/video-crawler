from __future__ import annotations

import logging
from datetime import UTC, datetime

from video_crawler.config import settings
from video_crawler.models.domain import RankingSnapshot, Video
from video_crawler.platforms.base import PlatformAdapter, register_platform
from video_crawler.platforms.youtube.constants import (
    BASE_URL,
    RANKING_CATEGORIES,
    SEARCH_URL,
    VIDEO_PARTS,
    VIDEOS_URL,
)
from video_crawler.platforms.youtube.parser import (
    parse_popular_response,
    parse_ranking_response,
    parse_video,
)
from video_crawler.utils.http import RateLimitedClient

logger = logging.getLogger(__name__)


@register_platform
class YouTubeAdapter(PlatformAdapter):
    platform_name = "youtube"

    def __init__(self):
        self._api_key = settings.youtube_api_key
        self._client = RateLimitedClient(
            requests_per_minute=settings.youtube_rpm,
            max_concurrent=3,
        )
        if not self._api_key:
            logger.warning(
                "YouTube API key not configured (YOUTUBE_API_KEY is empty). "
                "All YouTube requests will return empty results."
            )

    async def get_popular_videos(
        self, category: str | None = None, page: int = 1
    ) -> list[Video]:
        if not self._api_key:
            return []

        params: dict = {
            "chart": "mostPopular",
            "part": VIDEO_PARTS,
            "maxResults": 50,
            "key": self._api_key,
        }
        if category and category in RANKING_CATEGORIES and category != "all":
            params["videoCategoryId"] = RANKING_CATEGORIES[category]

        try:
            resp = await self._client.get(BASE_URL + VIDEOS_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                logger.error("YouTube API error: %s", data["error"].get("message", ""))
                return []
            return parse_popular_response(data)
        except Exception as exc:
            logger.error("Failed to fetch YouTube popular videos: %s", exc)
            return []

    async def get_rankings(self, category: str = "all") -> RankingSnapshot:
        if not self._api_key:
            return RankingSnapshot(
                platform="youtube",
                category=category,
                snapshot_time=datetime.now(UTC),
                entries=[],
            )

        params: dict = {
            "chart": "mostPopular",
            "part": VIDEO_PARTS,
            "maxResults": 50,
            "key": self._api_key,
        }
        if category != "all" and category in RANKING_CATEGORIES:
            params["videoCategoryId"] = RANKING_CATEGORIES[category]

        try:
            resp = await self._client.get(BASE_URL + VIDEOS_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                logger.error("YouTube API error: %s", data["error"].get("message", ""))
                return parse_ranking_response({"items": []}, category)
            return parse_ranking_response(data, category)
        except Exception as exc:
            logger.error("Failed to fetch YouTube rankings: %s", exc)
            return parse_ranking_response({"items": []}, category)

    async def search_videos(self, keyword: str, page: int = 1) -> list[Video]:
        if not self._api_key:
            return []

        params: dict = {
            "q": keyword,
            "part": "snippet",
            "type": "video",
            "maxResults": 20,
            "key": self._api_key,
        }

        try:
            resp = await self._client.get(BASE_URL + SEARCH_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                logger.error("YouTube API error: %s", data["error"].get("message", ""))
                return []
            videos = []
            for item in data.get("items", []):
                vid = item.get("id", {}).get("videoId")
                if vid:
                    item["id"] = vid
                    videos.append(parse_video(item))
            return videos
        except Exception as exc:
            logger.error("Failed to search YouTube videos: %s", exc)
            return []

    async def close(self) -> None:
        await self._client.close()
