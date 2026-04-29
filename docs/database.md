# 数据库设计文档

## ER 关系图

```
┌──────────────┐       ┌──────────────────┐
│   videos     │       │   video_stats    │
├──────────────┤       ├──────────────────┤
│ PK id        │──1:N──│ FK video_id      │
│    platform  │       │    view_count    │
│    video_id  │       │    like_count    │
│    title     │       │    coin_count    │
│    author_id │       │    favorite_count│
│    author_name│      │    reply_count   │
│    ...       │       │    share_count   │
└──────┬───────┘       │    danmaku_count │
       │               │    crawled_at    │
       │               └──────────────────┘
       │
       │ 1:N (via ranking_entries)
       │
┌──────┴───────────────┐       ┌──────────────────┐
│  ranking_entries     │       │ranking_snapshots  │
├──────────────────────┤       ├──────────────────┤
│ FK snapshot_id       │──N:1──│ PK id            │
│ FK video_id          │       │    platform      │
│    rank              │       │    category      │
│    score             │       │    snapshot_time  │
└──────────────────────┘       └──────────────────┘

┌──────────────────┐       ┌──────────────────┐
│   crawl_logs     │       │    watchlist     │
├──────────────────┤       ├──────────────────┤
│ PK id            │       │ PK id            │
│    platform      │       │    platform      │
│    job_type      │       │    target_type   │
│    status        │       │    target_id     │
│    items_count   │       │    label         │
│    error_message │       │    notify        │
│    started_at    │       │    created_at    │
│    finished_at   │       └──────────────────┘
└──────────────────┘
```

## 表结构明细

### videos — 视频基础信息

存储视频的身份信息和元数据。同一视频（platform + video_id）只有一行，多次采集时更新元数据。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 内部主键 |
| platform | VARCHAR(32) | NOT NULL | 平台标识：`bilibili`、`douyin`、`youtube` |
| video_id | VARCHAR(64) | NOT NULL | 平台原始 ID（B站 bvid、抖音 aweme_id 等） |
| title | TEXT | NOT NULL | 视频标题 |
| author_id | VARCHAR(64) | NOT NULL | 作者/UP主 ID |
| author_name | VARCHAR(128) | NOT NULL | 作者昵称 |
| description | TEXT | DEFAULT '' | 视频简介 |
| cover_url | TEXT | DEFAULT '' | 封面图 URL |
| duration | INTEGER | DEFAULT 0 | 时长（秒） |
| category | VARCHAR(64) | DEFAULT '' | 分区名称 |
| tags | JSON | DEFAULT [] | 标签列表，存储为 JSON 数组 |
| url | TEXT | DEFAULT '' | 视频页面 URL |
| publish_time | DATETIME | NULLABLE | 发布时间 |
| first_seen_at | DATETIME | DEFAULT NOW | 首次采集时间 |
| updated_at | DATETIME | DEFAULT NOW | 最后更新时间（自动） |

**唯一约束**: `(platform, video_id)`
**索引**: `platform`、`publish_time`、`(platform, category)`

### video_stats — 视频统计快照（时间序列）

追加式（append-only）表。每次采集追加一行，用于追踪统计数据随时间的变化。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 内部主键 |
| video_id | INTEGER | FK → videos.id, NOT NULL | 关联视频 |
| view_count | INTEGER | DEFAULT 0 | 播放量 |
| like_count | INTEGER | DEFAULT 0 | 点赞数 |
| coin_count | INTEGER | DEFAULT 0 | 投币数（B站特有） |
| favorite_count | INTEGER | DEFAULT 0 | 收藏数 |
| reply_count | INTEGER | DEFAULT 0 | 评论数 |
| share_count | INTEGER | DEFAULT 0 | 分享数 |
| danmaku_count | INTEGER | DEFAULT 0 | 弹幕数（B站特有） |
| crawled_at | DATETIME | DEFAULT NOW | 采集时间 |

**索引**: `video_id`、`crawled_at`

### ranking_snapshots — 排行榜快照

每次采集排行榜创建一个快照，记录采集时间和分区。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 内部主键 |
| platform | VARCHAR(32) | NOT NULL | 平台标识 |
| category | VARCHAR(64) | NOT NULL | 分区（`all`、`music`、`game` 等） |
| snapshot_time | DATETIME | DEFAULT NOW | 快照时间 |

**索引**: `(platform, category, snapshot_time)`

### ranking_entries — 排行榜条目

快照中的每一条排名记录。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 内部主键 |
| snapshot_id | INTEGER | FK → ranking_snapshots.id, NOT NULL | 所属快照 |
| rank | INTEGER | NOT NULL | 排名位次 |
| video_id | INTEGER | FK → videos.id, NOT NULL | 关联视频 |
| score | INTEGER | DEFAULT 0 | 平台综合得分 |

**唯一约束**: `(snapshot_id, rank)`
**索引**: `snapshot_id`、`video_id`

### crawl_logs — 爬取日志

每次采集任务的执行记录，用于运维监控和问题排查。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 内部主键 |
| platform | VARCHAR(32) | NOT NULL | 平台标识 |
| job_type | VARCHAR(32) | NOT NULL | 任务类型：`popular`、`ranking`、`search` |
| status | VARCHAR(16) | NOT NULL | 状态：`success`、`failed`、`partial` |
| items_count | INTEGER | DEFAULT 0 | 采集条目数 |
| error_message | TEXT | NULLABLE | 错误信息（失败时） |
| started_at | DATETIME | NULLABLE | 开始时间 |
| finished_at | DATETIME | DEFAULT NOW | 结束时间 |

**索引**: `(platform, job_type)`

### watchlist — 关注列表

用户标记要持续追踪的视频或作者，可配置是否推送通知。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 内部主键 |
| platform | VARCHAR(32) | NOT NULL | 平台标识 |
| target_type | VARCHAR(16) | NOT NULL | 追踪类型：`video` 或 `author` |
| target_id | VARCHAR(64) | NOT NULL | 目标 ID |
| label | VARCHAR(256) | DEFAULT '' | 用户备注 |
| notify | INTEGER | DEFAULT 0 | 是否推送通知（0=否，1=是） |
| created_at | DATETIME | DEFAULT NOW | 创建时间 |

**唯一约束**: `(platform, target_type, target_id)`

## 设计决策

### videos 与 video_stats 分离

**问题**: 视频的元数据（标题、作者等）变化少，但统计数据（播放量、点赞等）每次采集都不同。如果合并在一张表中，只能保留最新值，无法回溯历史趋势。

**方案**: 将稳定元数据存在 `videos` 表（upsert 更新），统计数据追加到 `video_stats` 表（每次 INSERT 新行）。

**收益**:
- 可以查询任意时间点的播放量/点赞数
- 可以计算增长速度（两次采集之间的差值）
- 可以生成趋势图表
- 存储开销可控（每条 stat 记录仅 ~100 bytes）

### 排行榜快照模式

**问题**: 排行榜是一个时间点的全量排名，需要保留历史快照来分析排名变动。

**方案**: `ranking_snapshots` 记录快照维度，`ranking_entries` 记录每条排名。一对多关系。

**收益**:
- 可以查询"视频 X 的排名历史"
- 可以对比不同时间点的 Top 10
- 可以发现新上榜/掉出榜的视频

### Tags 存储为 JSON

SQLite 没有原生数组类型。将标签列表存为 JSON 字符串，通过 SQLAlchemy 的 `JSON` 类型自动序列化/反序列化。SQLite 的 `json_each()` 函数可用于查询特定标签。

## 常用查询示例

### 查看某视频的播放量趋势

```sql
SELECT s.crawled_at, s.view_count, s.like_count
FROM video_stats s
JOIN videos v ON v.id = s.video_id
WHERE v.platform = 'bilibili' AND v.video_id = 'BV1xxxxxxxxx'
ORDER BY s.crawled_at;
```

### 查看最新排行榜

```sql
SELECT e.rank, v.title, v.author_name, e.score
FROM ranking_entries e
JOIN ranking_snapshots rs ON rs.id = e.snapshot_id
JOIN videos v ON v.id = e.video_id
WHERE rs.platform = 'bilibili' AND rs.category = 'all'
ORDER BY rs.snapshot_time DESC, e.rank
LIMIT 100;
```

### 发现播放量飙升的视频

```sql
-- 最近两次采集之间播放量增长最多的视频
WITH recent_stats AS (
    SELECT
        s.video_id,
        s.view_count,
        s.crawled_at,
        ROW_NUMBER() OVER (PARTITION BY s.video_id ORDER BY s.crawled_at DESC) AS rn
    FROM video_stats s
)
SELECT
    v.title,
    v.author_name,
    curr.view_count AS current_views,
    prev.view_count AS previous_views,
    (curr.view_count - prev.view_count) AS growth
FROM recent_stats curr
JOIN recent_stats prev ON prev.video_id = curr.video_id AND prev.rn = 2
JOIN videos v ON v.id = curr.video_id
WHERE curr.rn = 1
ORDER BY growth DESC
LIMIT 20;
```

### 查看排名变动

```sql
-- 对比最近两个快照的排名变化
WITH snapshots AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY snapshot_time DESC) AS rn
    FROM ranking_snapshots
    WHERE platform = 'bilibili' AND category = 'all'
    LIMIT 2
)
SELECT
    curr.rank AS current_rank,
    prev.rank AS previous_rank,
    (prev.rank - curr.rank) AS rank_change,
    v.title
FROM ranking_entries curr
JOIN snapshots s1 ON s1.id = curr.snapshot_id AND s1.rn = 1
LEFT JOIN ranking_entries prev ON prev.video_id = curr.video_id
LEFT JOIN snapshots s2 ON s2.id = prev.snapshot_id AND s2.rn = 2
JOIN videos v ON v.id = curr.video_id
ORDER BY curr.rank;
```

## 迁移指南

项目使用 Alembic 管理数据库迁移。

### 生成迁移脚本

```bash
# 在修改 models/db.py 后
cd src && alembic revision --autogenerate -m "description of change"
```

### 执行迁移

```bash
alembic upgrade head
```

### 回滚

```bash
alembic downgrade -1
```

> 注意: 当前 MVP 阶段通过 `Base.metadata.create_all()` 自动建表，Alembic 迁移将在 Phase 2 正式启用。
