from datetime import date, datetime
from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="HORA_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    daily_target_minutes: int = 480
    data_dir: str = "data"
    log_level: str = "INFO"
    environment: str = "development"
    auth_password_hash: str = ""
    auth_bcrypt_rounds: int = 12
    timezone: str = "America/Sao_Paulo"


settings = Settings()


def today() -> date:
    return datetime.now(ZoneInfo(settings.timezone)).date()
