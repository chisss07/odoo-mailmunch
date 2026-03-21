from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://mailmunch:mailmunch@localhost:5432/mailmunch"
    redis_url: str = "redis://localhost:6379"
    secret_key: str = Field(..., description="JWT signing secret — required")
    fernet_key: str = Field(..., description="Fernet encryption key — required")
    jwt_expiry_minutes: int = 60
    refresh_token_expiry_days: int = 7
    attachment_dir: str = "/app/attachments"
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
