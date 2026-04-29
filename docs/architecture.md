# 系统架构文档

## 架构总览

Video Crawler 采用四层分层架构，各层职责清晰，依赖单向向下：

```
┌─────────────────────────────────────────────────┐
│                   展示层                         │
│  CLI (__main__.py)  │  Dashboard  │  通知推送    │
├─────────────────────────────────────────────────┤
│                   服务层                         │
│  REST API (FastAPI)  │  Scheduler (APScheduler)  │
├─────────────────────────────────────────────────┤
│                   存储层                         │
│  Repository  │  SQLAlchemy ORM  │  SQLite        │
├─────────────────────────────────────────────────┤
│                   采集层                         │
│  PlatformAdapter  │  HTTP Client  │  Parser      │
└─────────────────────────────────────────────────┘
```

## 核心组件关系

```
__main__.py (CLI)
    │
    ├── platforms/base.py ── get_platform("bilibili")
    │       │
    │       └── bilibili/client.py (BilibiliAdapter)
    │               ├── bilibili/constants.py (API 端点)
    │               ├── bilibili/parser.py (JSON → 领域模型)
    │               └── utils/http.py (RateLimitedClient)
    │
    ├── db/repository.py (VideoRepository)
    │       └── db/engine.py (SQLAlchemy engine)
    │               └── models/db.py (ORM 模型)
    │
    └── models/domain.py (Video, RankingSnapshot 等)
```

## 数据流

一次完整的热门视频采集流程：

```
1. CLI 解析命令参数
       │
2. 获取平台适配器: get_platform("bilibili")
       │
3. 调用 adapter.get_popular_videos(page=N)
       │
4. RateLimitedClient 执行限速 HTTP 请求
       │  ├── 检查信号量（并发控制）
       │  ├── 等待间隔（限速）
       │  └── httpx.get() → B站 API
       │
5. bilibili/parser.py 解析 JSON 响应
       │  └── JSON dict → list[Video] 领域模型
       │
6. VideoRepository.upsert_video(video)
       │  ├── 查询是否已存在 (platform + video_id)
       │  ├── 不存在 → INSERT videos 行
       │  ├── 已存在 → UPDATE 元数据字段
       │  └── INSERT video_stats 行（追加统计快照）
       │
7. session.commit() → 写入 SQLite
       │
8. CrawlLogRow → 记录采集日志
```

## 平台适配器模式

### PlatformAdapter 抽象接口

```python
class PlatformAdapter(ABC):
    platform_name: str  # 平台标识符

    async def get_popular_videos(...) -> list[Video]
    async def get_rankings(...) -> RankingSnapshot
    async def search_videos(...) -> list[Video]
    async def close() -> None
```

### 注册机制

使用装饰器 `@register_platform` 将适配器注册到全局注册表：

```python
@register_platform
class BilibiliAdapter(PlatformAdapter):
    platform_name = "bilibili"
    ...
```

运行时通过 `get_platform("bilibili")` 获取实例。
`platforms/__init__.py` 负责导入所有适配器模块以触发注册。

## 技术选型决策记录

### HTTP 客户端: httpx (而非 Scrapy / requests)

**背景**: 需要一个支持异步的 HTTP 客户端，用于调用各平台 JSON API。

**候选方案**:
- Scrapy: 完整爬虫框架，适合 HTML 页面爬取和链接跟踪
- requests + BeautifulSoup: 经典组合，但仅支持同步
- httpx: 支持 sync/async 双模式，内置 HTTP/2

**决策**: 选择 httpx。理由：
1. 目标平台主要暴露 JSON API，不需要 Scrapy 的 Spider/Pipeline 机制
2. 异步支持与 FastAPI 的异步栈天然契合
3. HTTP/2 支持减少连接开销
4. API 设计与 requests 高度一致，学习成本低

### ORM: SQLAlchemy 2.0 (而非 raw SQL / Peewee)

**背景**: 需要数据库抽象层来定义 schema 和执行 CRUD。

**决策**: SQLAlchemy 2.0 新式 API。理由：
1. Python 生态标准 ORM，社区资源丰富
2. Alembic 提供成熟的 schema 迁移方案
3. 可从 SQLite 无缝切换到 PostgreSQL
4. 2.0 API 的 `Mapped` 类型注解提供良好的类型提示

### 调度器: APScheduler (而非 Celery / cron)

**背景**: 需要定时执行采集任务。

**决策**: APScheduler 3.x。理由：
1. 进程内调度，无需额外的 broker (Redis/RabbitMQ)
2. 支持 cron 表达式和固定间隔两种触发方式
3. 对于单节点部署场景完全够用
4. 如果未来需要分布式，可迁移到 Celery

### 数据库: SQLite (而非 PostgreSQL / MongoDB)

**背景**: 需要持久化存储视频数据和统计时间序列。

**决策**: SQLite。理由：
1. 零配置、文件级部署，开发体验好
2. 与用户现有 notes-app 技术栈一致
3. 对于单用户/中等数据量场景性能足够
4. 通过 SQLAlchemy 抽象层，切换到 PostgreSQL 仅需更改连接字符串

### 仪表盘: Jinja2 + Chart.js (而非 React / Vue)

**背景**: 需要一个简单的数据可视化界面。

**决策**: 服务端渲染 HTML + CDN Chart.js。理由：
1. 无需 Node.js 构建工具链，保持项目纯 Python
2. FastAPI 原生支持 Jinja2 模板
3. Chart.js 通过 CDN 引入，零安装
4. 如果仪表盘功能膨胀，可以独立抽取为 SPA

## 扩展点说明

### 新增平台

1. 创建 `platforms/<platform_name>/` 目录
2. 实现 `PlatformAdapter` 接口
3. 添加 `@register_platform` 装饰器
4. 在 `platforms/__init__.py` 中导入
5. 详见 [平台适配器开发指南](platform-adapters.md)

### 切换数据库

修改 `.env` 中的 `DATABASE_URL`：
```
# PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost:5432/video_crawler

# MySQL
DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/video_crawler
```

需要安装对应的数据库驱动（psycopg2、pymysql 等）。

### 新增数据源类型

1. 在 `models/domain.py` 添加领域模型
2. 在 `models/db.py` 添加 ORM 模型
3. 在 `db/repository.py` 添加 CRUD 方法
4. 使用 Alembic 生成迁移脚本
