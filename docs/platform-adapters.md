# 平台适配器开发指南

## PlatformAdapter 接口契约

所有平台适配器必须继承 `PlatformAdapter` 抽象基类并实现以下方法：

```python
# src/video_crawler/platforms/base.py

class PlatformAdapter(ABC):
    platform_name: str  # 类属性，平台唯一标识符

    async def get_popular_videos(
        self, category: str | None = None, page: int = 1
    ) -> list[Video]:
        """
        获取热门/推荐视频列表。

        参数:
            category: 分区/频道筛选，None 表示全部
            page: 页码，从 1 开始

        返回:
            Video 领域模型列表。API 异常时返回空列表，不抛出异常。

        限速:
            由各适配器内部的 RateLimitedClient 保证。
        """

    async def get_rankings(self, category: str = "all") -> RankingSnapshot:
        """
        获取排行榜快照。

        参数:
            category: 排行榜分区，"all" 表示全站

        返回:
            RankingSnapshot 对象，包含排名条目列表。
            API 异常时返回空 entries 的 snapshot，不抛出异常。
        """

    async def search_videos(self, keyword: str, page: int = 1) -> list[Video]:
        """
        搜索视频。

        参数:
            keyword: 搜索关键词
            page: 页码

        返回:
            Video 列表。无结果或异常时返回空列表。
        """

    async def close(self) -> None:
        """
        释放资源（关闭 HTTP 客户端连接池等）。
        调用方负责在使用完毕后调用此方法。
        """
```

### 异常处理约定

- 适配器**不应向调用方抛出异常**（除非是不可恢复的配置错误）
- HTTP 错误、API 返回异常码 → 记录 `logger.error()`，返回空结果
- 超时、网络异常 → 由 `RateLimitedClient` 自动重试，最终失败时记录日志并返回空结果
- 调用方（CLI / Scheduler）负责根据返回结果决定是否记录 `crawl_logs`

### 领域模型映射约定

- `Video.platform` 必须与 `platform_name` 一致
- `Video.video_id` 使用平台原始唯一标识
- `Video.url` 构造完整的视频页面 URL
- 平台不支持的字段（如抖音没有 `coin_count`）保持默认值 0
- `publish_time` 统一为 UTC 或本地时区的 `datetime` 对象

## 新增平台的步骤清单

以添加"小红书"适配器为例：

### 1. 创建目录结构

```bash
mkdir -p src/video_crawler/platforms/xiaohongshu
touch src/video_crawler/platforms/xiaohongshu/__init__.py
touch src/video_crawler/platforms/xiaohongshu/client.py
touch src/video_crawler/platforms/xiaohongshu/parser.py
touch src/video_crawler/platforms/xiaohongshu/constants.py
```

### 2. 实现 constants.py

定义 API 端点、请求头、分区映射等平台特定常量。

```python
# platforms/xiaohongshu/constants.py

BASE_URL = "https://..."
DEFAULT_HEADERS = { ... }
CATEGORIES = { ... }
```

### 3. 实现 parser.py

编写 JSON 响应到领域模型的映射函数。

```python
# platforms/xiaohongshu/parser.py

def parse_video(item: dict) -> Video:
    return Video(
        platform="xiaohongshu",
        video_id=item["note_id"],
        title=item["title"],
        ...
    )
```

### 4. 实现 client.py

继承 `PlatformAdapter`，使用 `@register_platform` 装饰器注册。

```python
# platforms/xiaohongshu/client.py

@register_platform
class XiaohongshuAdapter(PlatformAdapter):
    platform_name = "xiaohongshu"

    def __init__(self):
        self._client = RateLimitedClient(
            requests_per_minute=settings.xiaohongshu_rpm,
        )

    async def get_popular_videos(self, ...) -> list[Video]: ...
    async def get_rankings(self, ...) -> RankingSnapshot: ...
    async def search_videos(self, ...) -> list[Video]: ...
    async def close(self) -> None: ...
```

### 5. 注册适配器

在 `platforms/__init__.py` 中添加导入：

```python
import video_crawler.platforms.xiaohongshu.client  # noqa: F401
```

### 6. 添加配置

在 `config.py` 的 `Settings` 类中添加限速配置：

```python
xiaohongshu_rpm: int = 10
```

在 `.env.example` 中添加对应变量。

### 7. 编写测试

```bash
touch tests/fixtures/xiaohongshu_popular.json
touch tests/test_xiaohongshu_parser.py
```

编写 fixture JSON 和对应的 parser 测试。

### 8. 更新 CLI（可选）

如果新平台需要在 CLI 中直接使用，更新 `__main__.py` 添加 `--platform` 参数。

### 9. 更新文档

- 更新 `README.md` 功能特性表
- 更新本文档的平台对照表
- 更新 `docs/changelog.md`

## 各平台特点对照

| 特性 | B站 (bilibili) | 抖音 (douyin) | YouTube |
|------|---------------|--------------|---------|
| API 类型 | 公开 Web API (JSON) | 网页 + 私有 API | 官方 Data API v3 |
| 认证要求 | 无（基础数据） | 无（网页数据） | API Key |
| 反爬强度 | 低 | 高 | 无（官方 API） |
| 限速建议 | 30 req/min | 10 req/min | 按 quota（10000 units/day） |
| 视频 ID 格式 | bvid (BV1xxx) | aweme_id | YouTube video ID |
| 特有字段 | coin_count, danmaku_count | — | — |
| 排行榜 | 17 个分区 | 按话题/热搜 | 按地区趋势 |
| 数据完整度 | 高 | 中（受限于网页可见内容） | 高 |

### B站 (bilibili)

**数据获取方式**: 直接调用 Web API，返回 JSON，无需认证。

**API 端点**:
- 热门推荐: `GET /x/web-interface/popular`
- 排行榜: `GET /x/web-interface/ranking/v2`
- 搜索: `GET /x/web-interface/search/type`
- 视频详情: `GET /x/web-interface/view`

**注意事项**:
- 部分 API 需要 wbi 签名（目前使用的端点不需要）
- 需要设置合理的 `User-Agent` 和 `Referer` 头
- 热门推荐和排行榜数据为公开数据，无法律风险

### 抖音 (douyin)

**数据获取方式**: 解析网页分享页面。抖音的 APP API 有强加密和设备指纹验证，不建议逆向。

**注意事项**:
- 反爬机制最强，需要非常保守的限速
- 可能需要 Playwright 进行 JS 渲染
- 数据完整度受限于网页可展示的内容
- 建议优先级最低，作为最后实现的平台

### YouTube

**数据获取方式**: 官方 YouTube Data API v3，需要申请 Google API Key。

**注意事项**:
- 免费 quota: 每天 10,000 units
- search.list 消耗 100 units/次，videos.list 消耗 1 unit/次
- 需要合理规划 quota 使用
- 需要网络代理访问（国内环境）

## 反爬合规要求

### 通用原则

1. **遵守 robots.txt**: 在实现新平台前，检查目标站点的 robots.txt
2. **只采集公开数据**: 不访问需要登录的接口，不爬取私有/未公开内容
3. **合理限速**: 单平台不超过 1 req/s，严格遵守 429 响应
4. **正确标识**: User-Agent 真实标识爬虫身份
5. **数据最小化**: 只采集分析所需的字段，不存储敏感信息

### B站 robots.txt 要点

B站 robots.txt 允许大部分 API 路径。`/x/web-interface/` 下的端点属于网站正常 AJAX 请求的接口，访问等同于浏览器用户行为。

### YouTube 合规

使用官方 API，完全符合 YouTube Terms of Service。注意：
- 不得缓存数据超过 YouTube API Terms 允许的期限
- 需在应用中标注"使用 YouTube API 服务"
- 遵守 YouTube API Services Terms of Service

### 抖音合规

- 仅解析公开的分享页面
- 不逆向 APP 通信协议
- 不使用自动化工具模拟登录
- 严格限速，发现被封立即停止
