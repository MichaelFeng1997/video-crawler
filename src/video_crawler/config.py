from pathlib import Path

from pydantic_settings import BaseSettings


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = {"env_file": str(_project_root() / ".env"), "env_file_encoding": "utf-8"}

    database_url: str = f"sqlite:///{_project_root() / 'data' / 'video_crawler.db'}"

    server_host: str = "0.0.0.0"
    server_port: int = 8000

    bilibili_rpm: int = 30
    douyin_rpm: int = 10
    youtube_api_key: str = ""
    youtube_rpm: int = 60

    notify_urls: str = ""

    log_level: str = "INFO"

    request_timeout: float = 30.0
    max_retries: int = 3
    backoff_base: float = 2.0

    @property
    def project_root(self) -> Path:
        return _project_root()

    @property
    def data_dir(self) -> Path:
        d = _project_root() / "data"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def notify_url_list(self) -> list[str]:
        if not self.notify_urls:
            return []
        return [u.strip() for u in self.notify_urls.split(",") if u.strip()]


settings = Settings()
