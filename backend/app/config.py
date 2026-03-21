from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://mailmunch:mailmunch@localhost:5432/mailmunch"
    redis_url: str = "redis://localhost:6379"
    secret_key: str = "change-me-in-production"
    fernet_key: str = "change-me-in-production"
    jwt_expiry_minutes: int = 60
    refresh_token_expiry_days: int = 7
    attachment_dir: str = "/app/attachments"
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
