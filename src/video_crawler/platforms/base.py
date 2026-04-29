from __future__ import annotations

from abc import ABC, abstractmethod

from video_crawler.models.domain import RankingSnapshot, Video

_registry: dict[str, type[PlatformAdapter]] = {}


class PlatformAdapter(ABC):
    platform_name: str

    @abstractmethod
    async def get_popular_videos(self, category: str | None = None, page: int = 1) -> list[Video]:
        ...

    @abstractmethod
    async def get_rankings(self, category: str = "all") -> RankingSnapshot:
        ...

    @abstractmethod
    async def search_videos(self, keyword: str, page: int = 1) -> list[Video]:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...


def register_platform(cls: type[PlatformAdapter]) -> type[PlatformAdapter]:
    _registry[cls.platform_name] = cls
    return cls


def get_platform(name: str) -> PlatformAdapter:
    if name not in _registry:
        raise ValueError(f"Unknown platform: {name}. Available: {list(_registry.keys())}")
    return _registry[name]()


def list_platforms() -> list[str]:
    return list(_registry.keys())
