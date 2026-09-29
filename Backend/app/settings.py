from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    download_path: str = "./downloads"
    max_concurrent_downloads: int = 3
    cors_origins: list[str] = ["http://localhost:5173"]
    openapi_enabled: bool = True
    log_level: str = "INFO"
    api_key: str = "changeme"
    allowed_download_root: str = "./downloads"

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
