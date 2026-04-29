from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from video_crawler.notifications.notifier import send_notification

logger = logging.getLogger(__name__)


async def crawl_popular_job(platform_name: str = "bilibili", pages: int = 3):
    from video_crawler.db.engine import get_session
    from video_crawler.db.repository import VideoRepository
    from video_crawler.platforms.base import get_platform

    adapter = get_platform(platform_name)
    session = get_session()
    repo = VideoRepository(session)
    started_at = datetime.now(UTC)
    total = 0

    try:
        for page in range(1, pages + 1):
            videos = await adapter.get_popular_videos(page=page)
            for video in videos:
                repo.upsert_video(video)
            total += len(videos)

        session.commit()
        repo.log_crawl(platform_name, "popular", "success", total, started_at=started_at)
        session.commit()
        logger.info("[scheduler] Crawled %d popular videos from %s", total, platform_name)
        await asyncio.to_thread(
            send_notification,
            "采集完成: 热门视频",
            f"成功采集 {total} 个热门视频 (平台: {platform_name})",
            "success",
        )
    except Exception as exc:
        session.rollback()
        repo.log_crawl(platform_name, "popular", "failed", 0, str(exc), started_at=started_at)
        session.commit()
        logger.error("[scheduler] Failed to crawl popular from %s: %s", platform_name, exc)
        await asyncio.to_thread(
            send_notification,
            "采集失败: 热门视频",
            f"平台 {platform_name} 热门视频采集失败: {exc}",
            "failure",
        )
    finally:
        await adapter.close()
        session.close()


async def crawl_rankings_job(platform_name: str = "bilibili", category: str = "all"):
    from video_crawler.db.engine import get_session
    from video_crawler.db.repository import VideoRepository
    from video_crawler.platforms.base import get_platform

    adapter = get_platform(platform_name)
    session = get_session()
    repo = VideoRepository(session)
    started_at = datetime.now(UTC)

    try:
        snapshot = await adapter.get_rankings(category=category)
        repo.save_ranking_snapshot(snapshot)
        session.commit()

        count = len(snapshot.entries)
        repo.log_crawl(platform_name, "ranking", "success", count, started_at=started_at)
        session.commit()
        logger.info(
            "[scheduler] Crawled %d ranking entries from %s (%s)", count, platform_name, category
        )
        await asyncio.to_thread(
            send_notification,
            "采集完成: 排行榜",
            f"成功采集 {count} 条排行榜数据 (平台: {platform_name}, 分类: {category})",
            "success",
        )
    except Exception as exc:
        session.rollback()
        repo.log_crawl(platform_name, "ranking", "failed", 0, str(exc), started_at=started_at)
        session.commit()
        logger.error("[scheduler] Failed to crawl rankings from %s: %s", platform_name, exc)
        await asyncio.to_thread(
            send_notification,
            "采集失败: 排行榜",
            f"平台 {platform_name} 排行榜采集失败: {exc}",
            "failure",
        )
    finally:
        await adapter.close()
        session.close()


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        crawl_popular_job,
        "interval",
        minutes=30,
        id="crawl_popular_bilibili",
        name="Bilibili popular videos",
        kwargs={"platform_name": "bilibili", "pages": 3},
    )

    scheduler.add_job(
        crawl_rankings_job,
        "interval",
        hours=1,
        id="crawl_rankings_bilibili",
        name="Bilibili rankings",
        kwargs={"platform_name": "bilibili", "category": "all"},
    )

    return scheduler
