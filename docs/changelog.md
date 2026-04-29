# 变更日志

本文档记录 Video Crawler 的所有版本变更，遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式。

版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范。

## [0.1.0] - 2026-04-29

首个 MVP 版本，实现 B站 数据采集核心功能。

### 新增

- **B站热门视频采集** — `crawl-popular` 命令，支持分页采集热门推荐视频
- **B站排行榜采集** — `crawl-rankings` 命令，支持 17 个分区排行榜
- **SQLite 数据存储** — 6 张核心表（videos, video_stats, ranking_snapshots, ranking_entries, crawl_logs, watchlist）
- **统计数据时间序列** — video_stats 追加式设计，支持播放量/点赞/投币等趋势追踪
- **数据库统计概览** — `show-stats` 命令，显示视频数、统计记录数、排行榜快照数
- **限速 HTTP 客户端** — 内置请求限速、并发控制、指数退避重试
- **平台适配器架构** — 可扩展的插件式设计，支持后续添加新平台
- **完整产品文档** — 架构文档、数据库设计、API 参考、适配器开发指南、部署手册

### 技术细节

- Python 3.12 + httpx + SQLAlchemy 2.0
- pydantic-settings 配置管理
- 7 个单元测试（parser + repository）
- ruff 代码质量检查

---

## [Unreleased]

### 规划中

- Phase 2: APScheduler 定时采集 + FastAPI REST API
- Phase 3: Jinja2 + Chart.js 可视化仪表盘 + apprise 多渠道通知
- Phase 4: YouTube Data API v3 适配器 + 抖音网页解析适配器
- Phase 5: 全文搜索 (FTS5)、数据导出、Docker 部署
