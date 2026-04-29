from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import UTC, datetime

from video_crawler.config import settings


def setup_logging():
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


async def cmd_crawl_popular(args):
    from video_crawler.db.engine import get_session, init_db
    from video_crawler.db.repository import VideoRepository
    from video_crawler.platforms.base import get_platform

    init_db()
    adapter = get_platform("bilibili")
    session = get_session()
    repo = VideoRepository(session)

    started_at = datetime.now(UTC)
    total = 0

    try:
        pages = args.pages
        for page in range(1, pages + 1):
            videos = await adapter.get_popular_videos(page=page)
            for video in videos:
                repo.upsert_video(video)
            total += len(videos)
            print(f"  Page {page}: {len(videos)} videos")

        session.commit()
        repo.log_crawl("bilibili", "popular", "success", total, started_at=started_at)
        session.commit()
        print(f"\nDone. Total: {total} videos saved.")
    except Exception as exc:
        session.rollback()
        repo.log_crawl("bilibili", "popular", "failed", 0, str(exc), started_at=started_at)
        session.commit()
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        await adapter.close()
        session.close()


async def cmd_crawl_rankings(args):
    from video_crawler.db.engine import get_session, init_db
    from video_crawler.db.repository import VideoRepository
    from video_crawler.platforms.base import get_platform

    init_db()
    adapter = get_platform("bilibili")
    session = get_session()
    repo = VideoRepository(session)

    started_at = datetime.now(UTC)
    category = args.category

    try:
        snapshot = await adapter.get_rankings(category=category)
        repo.save_ranking_snapshot(snapshot)
        session.commit()

        count = len(snapshot.entries)
        repo.log_crawl("bilibili", "ranking", "success", count, started_at=started_at)
        session.commit()
        print(f"Done. Saved ranking snapshot: {count} entries (category: {category}).")

        if args.show_top:
            n = min(args.show_top, count)
            print(f"\nTop {n}:")
            for entry in snapshot.entries[:n]:
                v = entry.video
                print(
                    f"  #{entry.rank:>3}  {v.title[:40]:<42} "
                    f"views={v.view_count:>10,}  score={entry.score:>8,}"
                )
    except Exception as exc:
        session.rollback()
        repo.log_crawl("bilibili", "ranking", "failed", 0, str(exc), started_at=started_at)
        session.commit()
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        await adapter.close()
        session.close()


def cmd_show_stats(args):
    from video_crawler.db.engine import get_session, init_db
    from video_crawler.db.repository import VideoRepository

    init_db()
    session = get_session()
    repo = VideoRepository(session)

    video_count = repo.get_video_count()
    bilibili_count = repo.get_video_count("bilibili")
    stat_count = repo.get_stat_count()
    ranking_count = repo.get_ranking_snapshot_count()
    last_crawl = repo.get_latest_crawl_log()

    print("=== Video Crawler Stats ===")
    print(f"  Videos total:        {video_count:>8,}")
    print(f"    - Bilibili:        {bilibili_count:>8,}")
    print(f"  Stat records:        {stat_count:>8,}")
    print(f"  Ranking snapshots:   {ranking_count:>8,}")
    if last_crawl:
        print(f"  Last crawl:          {last_crawl.finished_at} ({last_crawl.status})")
    else:
        print("  Last crawl:          never")

    session.close()


def cmd_serve(args):
    import uvicorn

    from video_crawler.api.app import create_app

    host = args.host or settings.server_host
    port = args.port or settings.server_port

    app = create_app()
    print(f"Starting Video Crawler server at http://{host}:{port}")
    print(f"  API docs: http://{host}:{port}/docs")
    print("  Scheduler: enabled (popular every 30min, rankings every 1h)")
    uvicorn.run(app, host=host, port=port, log_level=settings.log_level.lower())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="video-crawler",
        description="多平台视频数据采集与分析工具",
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    p_popular = sub.add_parser("crawl-popular", help="Crawl popular videos from Bilibili")
    p_popular.add_argument("--pages", type=int, default=5, help="Number of pages (default: 5)")

    p_ranking = sub.add_parser("crawl-rankings", help="Crawl rankings from Bilibili")
    p_ranking.add_argument(
        "--category", type=str, default="all", help="Ranking category (default: all)"
    )
    p_ranking.add_argument(
        "--show-top", type=int, default=10, help="Show top N after crawl (default: 10)"
    )

    sub.add_parser("show-stats", help="Show database statistics")

    p_serve = sub.add_parser("serve", help="Start API server with scheduler")
    p_serve.add_argument(
        "--host", type=str, default=None, help="Host (default: from .env)"
    )
    p_serve.add_argument(
        "--port", type=int, default=None, help="Port (default: from .env)"
    )

    return parser


def main():
    setup_logging()

    import video_crawler.platforms  # noqa: F401 — register adapters

    parser = build_parser()
    args = parser.parse_args()

    if args.command == "crawl-popular":
        asyncio.run(cmd_crawl_popular(args))
    elif args.command == "crawl-rankings":
        asyncio.run(cmd_crawl_rankings(args))
    elif args.command == "show-stats":
        cmd_show_stats(args)
    elif args.command == "serve":
        cmd_serve(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
