from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
    )

    SECRET_KEY: str = Field(
        "your-secret-key-change-in-production-use-env-variable",
        description="Secret key for signing tokens. Must be changed in production.",
    )
    ALGORITHM: str = Field("HS256")
    ACCESS_TOKEN_EXPIRE_DAYS: int = Field(7)
    DATABASE_URL: str = Field("sqlite:///./db.sqlite3")

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = Field(60)
    RATE_LIMIT_WINDOW_SECONDS: int = Field(60)
    REDIS_URL: Optional[str] = Field(None)
    ENV: str = Field("development")

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_not_default(cls, v: str) -> str:
        if v == "your-secret-key-change-in-production-use-env-variable":
            print("WARNING: SECRET_KEY is using the insecure default — set SECRET_KEY in environment for production")
        return v


settings = Settings()
