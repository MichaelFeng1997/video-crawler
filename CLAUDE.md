# video-crawler

多平台视频数据采集与分析工具。支持 B站、抖音、YouTube。

## 技术栈

- **语言**: Python 3.12
- **HTTP**: httpx (async, HTTP/2)
- **数据库**: SQLite via SQLAlchemy 2.0
- **调度**: APScheduler
- **API**: FastAPI + Uvicorn（端口 8000）
- **可视化**: Jinja2 + Chart.js
- **通知**: apprise
- **测试**: pytest + pytest-asyncio
- **Lint**: ruff

## 目录结构

```
video-crawler/
├── src/video_crawler/
│   ├── __main__.py         # CLI 入口
│   ├── config.py           # pydantic-settings 配置
│   ├── platforms/
│   │   ├── base.py         # PlatformAdapter 抽象接口
│   │   ├── bilibili/       # B站适配器
│   │   └── youtube/        # YouTube 适配器
│   ├── models/
│   │   ├── domain.py       # 领域模型 (dataclass)
│   │   └── db.py           # SQLAlchemy ORM 模型
│   ├── db/
│   │   ├── engine.py       # 数据库引擎
│   │   └── repository.py   # 数据访问层
│   ├── utils/
│   │   └── http.py         # 限速 HTTP 客户端
│   ├── api/
│   │   ├── app.py          # FastAPI 应用 + lifespan
│   │   ├── deps.py         # 依赖注入 (get_db)
│   │   └── routes/         # health, videos, rankings
│   ├── scheduler/
│   │   └── jobs.py         # APScheduler 定时任务
│   ├── notifications/
│   │   └── notifier.py     # apprise 通知封装
│   └── dashboard/
│       ├── routes.py       # 仪表盘 HTML 路由
│       ├── templates/      # Jinja2 模板 (base, index, videos, video_detail, rankings)
│       └── static/         # CSS + JS (dashboard.css, charts.js, etc.)
├── tests/
├── data/                   # SQLite 文件 (gitignored)
└── docs/                   # 产品文档
```

## 启动

```bash
# 初始化
make setup
source .venv/bin/activate

# 采集
python -m video_crawler crawl-popular
python -m video_crawler crawl-rankings
python -m video_crawler show-stats

# 启动服务（API + 定时调度）
python -m video_crawler serve
# API docs: http://localhost:8000/docs

# 测试
make test

# Lint
make lint
```

## 环境变量

复制 `.env.example` 为 `.env` 并按需修改。

关键变量：
- `YOUTUBE_API_KEY` — YouTube Data API v3 密钥（未设置时 YouTube 适配器安全降级返回空结果）
- `YOUTUBE_RPM` — YouTube API 每分钟请求限制（默认 60）
- `NOTIFY_URLS` — 通知渠道 URL（逗号分隔）

## 数据库

6 张表：videos, video_stats, ranking_snapshots, ranking_entries, crawl_logs, watchlist。
videos + video_stats 分离设计，video_stats 为追加式时间序列。

## 平台适配器

所有平台实现 `PlatformAdapter` 接口（`platforms/base.py`）。
通过 `@register_platform` 装饰器注册，`get_platform("bilibili")` 获取实例。

## 命令

| 命令 | 说明 |
|------|------|
| `crawl-popular [--pages N]` | 采集B站热门视频 |
| `crawl-rankings [--category CAT] [--show-top N]` | 采集B站排行榜 |
| `show-stats` | 显示数据库统计 |
| `serve [--host H] [--port P]` | 启动 API 服务 + 定时调度 |

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/health | 健康检查 |
| GET | /api/videos | 视频列表（分页、筛选、搜索） |
| GET | /api/videos/{platform}/{video_id} | 视频详情 + 统计历史 |
| GET | /api/rankings/{platform} | 最新排行榜 |
| GET | /api/rankings/{platform}/history | 排行榜历史 |

## 仪表盘页面

| 路径 | 说明 |
|------|------|
| / | 首页：统计卡片 + 采集日志 + 热门视频 |
| /videos | 视频浏览：搜索/筛选/分页 |
| /videos/{platform}/{video_id} | 视频详情 + Chart.js 趋势图 |
| /rankings | 排行榜表格 + 分区选择 |

## 通知配置

在 `.env` 中设置 `NOTIFY_URLS`（逗号分隔），采集完成/失败时自动推送。
示例：`NOTIFY_URLS=tgram://bot_token/chat_id,serverchan://sendkey`

## 定时任务

| 任务 | 间隔 | 说明 |
|------|------|------|
| crawl_popular_bilibili | 30 分钟 | 采集 B站 热门视频 (3 页) |
| crawl_rankings_bilibili | 1 小时 | 采集 B站 全站排行榜 |
