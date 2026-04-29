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
│   │   └── bilibili/       # B站适配器
│   ├── models/
│   │   ├── domain.py       # 领域模型 (dataclass)
│   │   └── db.py           # SQLAlchemy ORM 模型
│   ├── db/
│   │   ├── engine.py       # 数据库引擎
│   │   └── repository.py   # 数据访问层
│   ├── utils/
│   │   └── http.py         # 限速 HTTP 客户端
│   ├── api/                # FastAPI (Phase 2)
│   ├── scheduler/          # APScheduler (Phase 2)
│   └── dashboard/          # Web 仪表盘 (Phase 3)
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

# 测试
make test

# Lint
make lint
```

## 环境变量

复制 `.env.example` 为 `.env` 并按需修改。

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
