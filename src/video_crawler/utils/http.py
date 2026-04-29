from __future__ import annotations

import asyncio
import logging
import time

import httpx

from video_crawler.config import settings

logger = logging.getLogger(__name__)


class RateLimitedClient:
    def __init__(self, requests_per_minute: int = 30, max_concurrent: int = 3):
        self._min_interval = 60.0 / requests_per_minute
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._last_request = 0.0
        self._client = httpx.AsyncClient(
            timeout=settings.request_timeout,
            follow_redirects=True,
            http2=True,
        )

    async def get(self, url: str, **kwargs) -> httpx.Response:
        async with self._semaphore:
            elapsed = time.monotonic() - self._last_request
            if elapsed < self._min_interval:
                await asyncio.sleep(self._min_interval - elapsed)
            self._last_request = time.monotonic()

            for attempt in range(settings.max_retries):
                try:
                    resp = await self._client.get(url, **kwargs)
                    if resp.status_code == 429 or resp.status_code >= 500:
                        wait = settings.backoff_base ** (attempt + 1)
                        logger.warning(
                            "HTTP %d from %s, retrying in %.1fs", resp.status_code, url, wait
                        )
                        await asyncio.sleep(wait)
                        continue
                    return resp
                except httpx.TransportError as exc:
                    if attempt == settings.max_retries - 1:
                        raise
                    wait = settings.backoff_base ** (attempt + 1)
                    logger.warning("%s for %s, retrying in %.1fs", exc, url, wait)
                    await asyncio.sleep(wait)

            return resp  # type: ignore[possibly-undefined]

    async def close(self):
        await self._client.aclose()
