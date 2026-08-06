from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str
    SQS_QUEUE_URL: str
    MAX_UPLOAD_BYTES: int = 5_242_880


@lru_cache
def get_settings() -> Settings:
    return Settings()
