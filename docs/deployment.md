# 部署运维手册

## 本地开发环境

### 前置依赖

- Python 3.11+（推荐 3.12）
- pip
- virtualenv（如系统无 python3-venv）

### 初始化

```bash
cd ~/projects/video-crawler

# 方式一：使用 Makefile（推荐）
make setup
source .venv/bin/activate

# 方式二：手动
python3 -m venv .venv        # 或 virtualenv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

### 开发命令

```bash
# 运行测试
make test

# 代码检查
make lint

# 代码格式化
make format

# 手动采集
make crawl-popular
make crawl-rankings

# 查看统计
make stats

# 清理临时文件
make clean
```

### 目录权限

- `data/` 目录需要写权限（SQLite 数据库文件）
- 程序会自动创建 `data/` 目录

## 生产部署

### 方式一：systemd 服务

适用于 Linux 服务器上的长期运行。

#### 1. 部署代码

```bash
# 在服务器上
cd /opt
git clone <repo-url> video-crawler
cd video-crawler
make setup
cp .env.example .env
# 编辑 .env 设置生产配置
```

#### 2. 创建 systemd 服务文件

```ini
# /etc/systemd/system/video-crawler.service

[Unit]
Description=Video Crawler Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/video-crawler
ExecStart=/opt/video-crawler/.venv/bin/python -m video_crawler serve
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# 环境变量
EnvironmentFile=/opt/video-crawler/.env

# 安全加固
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/opt/video-crawler/data
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
```

#### 3. 启用服务

```bash
sudo systemctl daemon-reload
sudo systemctl enable video-crawler
sudo systemctl start video-crawler

# 查看状态
sudo systemctl status video-crawler

# 查看日志
sudo journalctl -u video-crawler -f
```

### 方式二：定时任务（cron）

如果不需要 API 服务，可以用 cron 定时执行采集命令。

```bash
# crontab -e

# 每 30 分钟采集热门视频
*/30 * * * * cd /opt/video-crawler && .venv/bin/python -m video_crawler crawl-popular --pages 3 >> /var/log/video-crawler.log 2>&1

# 每小时采集排行榜
0 * * * * cd /opt/video-crawler && .venv/bin/python -m video_crawler crawl-rankings >> /var/log/video-crawler.log 2>&1
```

### 方式三：Docker（Phase 5 规划）

Dockerfile 和 docker-compose.yml 将在 Phase 5 提供。预期配置：

```yaml
# docker-compose.yml (规划)
services:
  video-crawler:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./.env:/app/.env:ro
    restart: unless-stopped
```

## 监控与日志

### 日志配置

通过 `.env` 中的 `LOG_LEVEL` 控制日志级别：

| 级别 | 用途 |
|------|------|
| `DEBUG` | 开发调试��输出每次 HTTP 请求详情 |
| `INFO` | 日常运行，输出采集概要 |
| `WARNING` | 仅输出限速触发、重试等警告 |
| `ERROR` | 仅输出错误 |

### crawl_logs 表

程序自动记录每次采集任务的执行情况到 `crawl_logs` 表。

| 字段 | 含义 |
|------|------|
| `platform` | 目标平台 |
| `job_type` | 任务类型：`popular`（热门）、`ranking`（排行榜）、`search`（搜索） |
| `status` | 结果：`success`（成功）、`failed`（失败）、`partial`（部分成功） |
| `items_count` | 采集到的数据条数 |
| `error_message` | 失败原因（成功时为 NULL） |
| `started_at` | 任务开始时间 |
| `finished_at` | 任务结束时间 |

**查看最近采集记录**:

```sql
sqlite3 data/video_crawler.db \
  "SELECT finished_at, platform, job_type, status, items_count
   FROM crawl_logs ORDER BY finished_at DESC LIMIT 10;"
```

### 常见异常排查

| 现象 | 可能原因 | 排查方式 |
|------|----------|----------|
| 采集结果为 0 条 | B站 API 返回非 0 code | 检查日志中的 `Bilibili API error` |
| HTTP 429 频繁出现 | 限速配置过高 | 降低 `BILIBILI_RPM` |
| 连接超时 | 网络问题或 B站 IP 封禁 | 检查网络，等待一段时间重试 |
| 数据库锁定 | 多进程同时写入 SQLite | 确保同时只有一个进程写入 |
| 磁盘空间不足 | 数据库文件增长 | 清理旧 stats 数据或扩容 |

## 备份与恢复

### SQLite 数据库备份

SQLite 数据库为单文件，备份方式简单。

**手动备份**:
```bash
cp data/video_crawler.db data/video_crawler.db.bak.$(date +%Y%m%d)
```

**定时备份（cron）**:
```bash
# 每天凌晨 3 点备份
0 3 * * * cp /opt/video-crawler/data/video_crawler.db /backup/video_crawler.db.$(date +\%Y\%m\%d)

# 保留最近 30 天备份
0 4 * * * find /backup -name "video_crawler.db.*" -mtime +30 -delete
```

**使用 SQLite 在线备份（推荐，可在运行时安全执行）**:
```bash
sqlite3 data/video_crawler.db ".backup data/video_crawler.db.bak"
```

### 恢复

```bash
# 停止服务
sudo systemctl stop video-crawler

# 恢复备份
cp data/video_crawler.db.bak data/video_crawler.db

# 重启服务
sudo systemctl start video-crawler
```

### 数据清理

随着时间推移，`video_stats` 表会持续增长。可以定期清理旧数据：

```sql
-- 删除 90 天前的统计快照
DELETE FROM video_stats WHERE crawled_at < datetime('now', '-90 days');

-- 删除 90 天前的排行榜快照
DELETE FROM ranking_entries WHERE snapshot_id IN (
    SELECT id FROM ranking_snapshots WHERE snapshot_time < datetime('now', '-90 days')
);
DELETE FROM ranking_snapshots WHERE snapshot_time < datetime('now', '-90 days');

-- 回收空间
VACUUM;
```

## 性能参考

| 指标 | 参考值 |
|------|--------|
| 单次 crawl-popular（5 页） | ~15 秒（含限速间隔） |
| 单次 crawl-rankings | ~3 秒 |
| 数据库大小（10,000 视频 + 100,000 stats） | ~50 MB |
| 内存占用（CLI 模式） | ~50 MB |
| 内存占用（serve 模式，预估） | ~100 MB |
