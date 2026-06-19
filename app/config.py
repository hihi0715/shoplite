from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    app_name: str = "ShopLite"
    api_secret_key: str = ""
    use_multiprocessing: bool = False
    kmeans_clusters: int = 3
    kmeans_max_iter: int = 10
    mapreduce_workers: int = 4


@lru_cache
def get_settings() -> Settings:
    return Settings()
