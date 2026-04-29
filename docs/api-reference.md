# API 接口文档

## 概述

Video Crawler 提供两种交互方式：

1. **CLI 命令行**（Phase 1，当前可用）
2. **REST API**（Phase 2，规划中）

本文档描述所有已实现和规划中的接口。

---

## CLI 命令参考

所有命令通过 `python -m video_crawler <command>` 调用。

### crawl-popular

采集 B站 热门推荐视频。

```bash
python -m video_crawler crawl-popular [--pages N]
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--pages` | int | 5 | 采集页数，每页 20 条 |

**行为**:
- 向 B站 热门推荐 API 发送请求，每页 20 条视频
- 对每个视频执行 upsert：新视频插入 `videos` 表，已有视频���新元数据
- 每个视频追加一条 `video_stats` 统计快照
- 记录 `crawl_logs` 日志

**输出示例**:
```
  Page 1: 20 videos
  Page 2: 20 videos
  Page 3: 20 videos

Done. Total: 60 videos saved.
```

**错误处理**:
- API 返回非 0 code → 该页返回空列表，继续下一页
- HTTP 429/5xx → 自动指数退避重试（最多 3 次）
- 全部失败 → 输出错误信息到 stderr，退出码 1

---

### crawl-rankings

采集 B站 分区排行榜。

```bash
python -m video_crawler crawl-rankings [--category CAT] [--show-top N]
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--category` | string | `all` | 排行榜分区，见下方分区列表 |
| `--show-top` | int | 10 | 采集后显示前 N 名，设为 0 则不显示 |

**支持的分区**:

`all` `animation` `music` `dance` `game` `knowledge` `tech` `sports` `car` `life` `food` `animal` `fashion` `entertainment` `movie` `tv` `documentary`

**行为**:
- 创建一条 `ranking_snapshots` 记录
- 对排行榜中的每个视频执行 upsert + 追加 stats
- 创建对应的 `ranking_entries` 记录

**输出示例**:
```
Done. Saved ranking snapshot: 100 entries (category: all).

Top 10:
  #  1  视频标题A                                  views= 5,000,000  score= 1,500,000
  #  2  视频标题B                                  views= 3,200,000  score= 1,200,000
  ...
```

---

### show-stats

显示数据库统计概览。

```bash
python -m video_crawler show-stats
```

无参数。只读操作，不发起网络请求。

**输出示例**:
```
=== Video Crawler Stats ===
  Videos total:             156
    - Bilibili:             156
  Stat records:             312
  Ranking snapshots:          3
  Last crawl:          2026-04-29 08:30:00+00:00 (success)
```

---

## REST API（Phase 2 规划）

Phase 2 将提供 FastAPI REST API，通过 `python -m video_crawler serve` 启动。

### 通用约定

- **Base URL**: `http://localhost:8000/api`
- **Content-Type**: `application/json`
- **认证**: 当前无认证（本地工具）
- **分页参数**: `limit`（默认 20，最大 100）、`offset`（默认 0）
- **排序**: `sort_by`（字段名）、`order`（`asc` / `desc`）
- **时间格式**: ISO 8601（`2026-04-29T12:00:00Z`）

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

HTTP 状态码：
- `400` — 请求参数错误
- `404` — 资源不存在
- `500` — 服务器内部错误

### 端点列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/videos` | 视频列表（分页、筛选） |
| GET | `/api/videos/{platform}/{video_id}` | 视频���情 + 统计历史 |
| GET | `/api/rankings/{platform}` | 最新排行榜 |
| GET | `/api/rankings/{platform}/history` | 排行榜历史变动 |
| POST | `/api/crawl/{platform}` | 手动触发采集 |
| GET | `/api/health` | 健康检查 |

### GET /api/videos

获取已采集的视频列表。

**查询参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `platform` | string | `bilibili` | 平台筛选 |
| `category` | string | (可选) | 分区筛选 |
| `keyword` | string | (可选) | 标题模糊搜索 |
| `limit` | int | 20 | 每页条数 |
| `offset` | int | 0 | 偏移量 |

**响应示例**:
```json
{
  "total": 156,
  "items": [
    {
      "platform": "bilibili",
      "video_id": "BV1xxxxxxxxx",
      "title": "视频标题",
      "author_name": "UP主名称",
      "category": "科技",
      "view_count": 1000000,
      "like_count": 50000,
      "publish_time": "2026-04-28T10:00:00Z",
      "url": "https://www.bilibili.com/video/BV1xxxxxxxxx"
    }
  ]
}
```

### GET /api/videos/{platform}/{video_id}

获取单个视频的详细信息和统计历史。

**响应示例**:
```json
{
  "video": {
    "platform": "bilibili",
    "video_id": "BV1xxxxxxxxx",
    "title": "视频标题",
    "author_id": "12345",
    "author_name": "UP主名称",
    "description": "视频描述...",
    "duration": 300,
    "category": "科技",
    "tags": ["标签A", "标签B"],
    "publish_time": "2026-04-28T10:00:00Z"
  },
  "stats_history": [
    {
      "crawled_at": "2026-04-29T06:00:00Z",
      "view_count": 900000,
      "like_count": 45000
    },
    {
      "crawled_at": "2026-04-29T12:00:00Z",
      "view_count": 1000000,
      "like_count": 50000
    }
  ]
}
```

### GET /api/rankings/{platform}

获取最新一期排行榜快照。

**查询参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `category` | string | `all` | 分区 |

**响应示例**:
```json
{
  "snapshot_time": "2026-04-29T12:00:00Z",
  "category": "all",
  "entries": [
    {
      "rank": 1,
      "video_id": "BV1xxxxxxxxx",
      "title": "排行第一",
      "author_name": "UP主A",
      "score": 1500000,
      "view_count": 5000000
    }
  ]
}
```

### GET /api/rankings/{platform}/history

查询排行榜历史变动。

**查询参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `category` | string | `all` | 分区 |
| `days` | int | 7 | 查询天数 |

### POST /api/crawl/{platform}

手动触发一次采集任务（用于测试和管理）。

**请求体**:
```json
{
  "job_type": "popular",
  "params": {"pages": 3}
}
```

**响应**:
```json
{
  "status": "started",
  "job_id": "abc123"
}
```

### GET /api/health

健康检查。

**响应**:
```json
{
  "status": "ok",
  "database": "connected",
  "last_crawl": "2026-04-29T12:00:00Z",
  "video_count": 156,
  "uptime_seconds": 3600
}
```

---

## OpenAPI 自动文档

Phase 2 启动服务后，可访问 FastAPI 自动生成的交互式文档：

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`
