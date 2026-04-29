# Video Crawler

多平台视频数据采集与分析工具。自动爬取 B站、抖音、YouTube 等视频平台的热门视频、排行榜和内容数据，提供趋势分析、实时监控和内容聚合能力。

## 功能特性

| 功能 | 说明 | 状态 |
|------|------|------|
| B站热门视频采集 | 采集 bilibili 热门推荐视频，存储视频信息和统计数据 | v0.1.0 |
| B站排行榜采集 | 采集全站及分区排行榜，支持 17 个分区 | v0.1.0 |
| 统计数据时间序列 | 每次采集追加统计快照，支持播放量/点赞/投币等趋势分析 | v0.1.0 |
| CLI 工具 | 命令行采集和数据查看 | v0.1.0 |
| 定时调度 | APScheduler 自动定时采集 | 规划中 |
| REST API | FastAPI 数据查询接口 | 规划中 |
| 可视化仪表盘 | 排行榜、趋势图表、数据总览 | 规划中 |
| 多渠道通知 | 热度异常检测 + 邮件/Telegram/Server酱推送 | 规划中 |
| 抖音/YouTube | 跨平台数据采集 | 规划中 |

## 快速开始

### 前置依赖

- Python 3.11+
- pip

### 安装

```bash
cd ~/projects
git clone <repo-url> video-crawler
cd video-crawler

# 一键初始化（创建虚拟环境 + 安装依赖 + 复制配置文件）
make setup

# 激活虚拟环境
source .venv/bin/activate
```

### 配置

复制 `.env.example` 为 `.env` 并按需修改：

```bash
cp .env.example .env
```

默认配置即可直接使用，无需额外设置。

### 第一次数据采集

```bash
# 采集 B站 热门视频（默认 5 页，约 100 条）
python -m video_crawler crawl-popular

# 采集 B站 全站排行榜
python -m video_crawler crawl-rankings

# 查看数据库统计
python -m video_crawler show-stats
```

## 使用示例

### 采集热门视频

```bash
# 采集 5 页热门视频（默认）
$ python -m video_crawler crawl-popular
  Page 1: 20 videos
  Page 2: 20 videos
  Page 3: 20 videos
  Page 4: 20 videos
  Page 5: 20 videos

Done. Total: 100 videos saved.

# 指定页数
$ python -m video_crawler crawl-popular --pages 10
```

### 采集排行榜

```bash
# 全站排行榜
$ python -m video_crawler crawl-rankings
Done. Saved ranking snapshot: 100 entries (category: all).

Top 10:
  #  1  视频标题...                                views= 5,000,000  score= 1,500,000
  #  2  视频标题...                                views= 3,000,000  score= 1,200,000
  ...

# 指定分区
$ python -m video_crawler crawl-rankings --category music

# 不显示排名详情
$ python -m video_crawler crawl-rankings --show-top 0
```

**支持的排行榜分区：**

| 分区 ID | 分区名 | 分区 ID | 分区名 |
|---------|--------|---------|--------|
| all | 全站 | game | 游戏 |
| animation | 动画 | knowledge | 知识 |
| music | 音乐 | tech | 科技 |
| dance | 舞蹈 | sports | 运动 |
| life | 生活 | food | 美食 |
| animal | 动物圈 | fashion | 时尚 |
| entertainment | 娱乐 | car | 汽车 |
| movie | 电影 | tv | 电视剧 |
| documentary | 纪录片 | | |

### 查看统计

```bash
$ python -m video_crawler show-stats
=== Video Crawler Stats ===
  Videos total:             100
    - Bilibili:             100
  Stat records:             100
  Ranking snapshots:          1
  Last crawl:          2026-04-29 12:00:00 (success)
```

## 配置说明

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `sqlite:///data/video_crawler.db` | 数据库连接字符串 |
| `SERVER_HOST` | `0.0.0.0` | API 服务监听地址 |
| `SERVER_PORT` | `8000` | API 服务端口 |
| `BILIBILI_RPM` | `30` | B站请求限速（每分钟请求数） |
| `DOUYIN_RPM` | `10` | 抖音请求限速（每分钟请求数） |
| `YOUTUBE_API_KEY` | (空) | YouTube Data API v3 密钥 |
| `NOTIFY_URLS` | (空) | 通知渠道 URL，多个用逗号分隔 |
| `LOG_LEVEL` | `INFO` | 日志级别（DEBUG/INFO/WARNING/ERROR） |

## 项目路线图

- [x] **Phase 1 — MVP**: B站数据采集 CLI + SQLite 存储 + 统计时间序列
- [ ] **Phase 2 — 调度 + API**: APScheduler 定时采集 + FastAPI REST API
- [ ] **Phase 3 — 仪表盘 + 通知**: Web 可视化 + 多渠道异常通知
- [ ] **Phase 4 — 平台扩展**: YouTube Data API + 抖音网页解析
- [ ] **Phase 5 — 高级功能**: 全文搜索、数据导出、Docker 部署

## 技术栈

- **语言**: Python 3.12
- **HTTP 客户端**: httpx (async, HTTP/2)
- **数据库**: SQLite via SQLAlchemy 2.0
- **迁移**: Alembic
- **调度器**: APScheduler
- **API 框架**: FastAPI + Uvicorn
- **可视化**: Jinja2 + Chart.js
- **通知**: apprise
- **测试**: pytest + pytest-asyncio
- **代码质量**: ruff

## 许可证

MIT License
