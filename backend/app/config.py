from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

DEFAULT_SECRET_KEY = "your-secret-key-change-in-production-use-env-variable"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
    )

    SECRET_KEY: str = Field(
        DEFAULT_SECRET_KEY,
        description="Secret key for signing tokens. Must be changed in production.",
    )
    ALGORITHM: str = Field("HS256")
    ACCESS_TOKEN_EXPIRE_DAYS: int = Field(7)
    DATABASE_URL: str = Field("sqlite:///./db.sqlite3")

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = Field(60)
    RATE_LIMIT_WINDOW_SECONDS: int = Field(60)
    REDIS_URL: Optional[str] = Field("redis://redis:6379/0")
    CORS_ALLOWED_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])
    ENV: str = Field("development")

    # Password reset email delivery. If SMTP_HOST is unset, reset links are
    # logged server-side instead of emailed - lets password reset be tested
    # locally before real SMTP credentials are configured.
    SMTP_HOST: Optional[str] = Field(None)
    SMTP_PORT: int = Field(587)
    SMTP_USERNAME: Optional[str] = Field(None)
    SMTP_PASSWORD: Optional[str] = Field(None)
    SMTP_FROM_EMAIL: Optional[str] = Field(None)
    SMTP_USE_TLS: bool = Field(True)
    FRONTEND_BASE_URL: str = Field("http://localhost:3000")

    @field_validator("CORS_ALLOWED_ORIGINS", mode="before")
    @classmethod
    def split_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_not_default(cls, v: str) -> str:
        if v == "your-secret-key-change-in-production-use-env-variable":
            print("WARNING: SECRET_KEY is using the insecure default — set SECRET_KEY in environment for production")
        return v


settings = Settings()


def validate_production_security(config: Settings) -> None:
    """Reject configuration that would expose a production deployment."""
    if config.ENV.lower() != "production":
        return

    if config.SECRET_KEY == DEFAULT_SECRET_KEY or len(config.SECRET_KEY) < 32:
        raise RuntimeError("Production requires SECRET_KEY with at least 32 characters.")

    if "*" in config.CORS_ALLOWED_ORIGINS:
        raise RuntimeError("Production requires explicit CORS_ALLOWED_ORIGINS; wildcard CORS is not allowed.")
