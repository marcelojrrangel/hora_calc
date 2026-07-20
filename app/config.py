from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HORA_")

    daily_target_minutes: int = 480
    data_dir: str = "data"
    log_level: str = "INFO"
    environment: str = "development"
    auth_password_hash: str = ""
    auth_salt: str = "default-salt-change-in-production"


settings = Settings()
