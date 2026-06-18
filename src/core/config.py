from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from .env.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    MODEL_PATH: str = Field(default="yolo11n.pt")
    CONF_THRESHOLD: float = Field(default=0.35)
    IOU_THRESHOLD: float = Field(default=0.45)

    ENV: str = Field(default="development")

    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)


@lru_cache
def get_settings() -> Settings:
    return Settings()