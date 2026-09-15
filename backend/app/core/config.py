from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    app_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    database_url: str = "sqlite:///./data/transcriber.db"
    data_dir: str = "./data"
    max_file_size_mb: int = 1024
    max_duration_minutes: int = 180
    max_concurrent_jobs: int = 1
    default_model: str = "base"
    whisper_device: str = "auto"
    whisper_compute_type: str = "auto"
    job_retention_hours: int = 24
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

settings = Settings()
