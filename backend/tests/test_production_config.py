import pytest

from backend.app.config import Settings, validate_production_security


def test_production_rejects_default_or_short_secret():
    config = Settings(
        ENV="production",
        SECRET_KEY="short-secret",
        CORS_ALLOWED_ORIGINS=["http://localhost:3000"],
    )

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        validate_production_security(config)


def test_production_rejects_wildcard_cors():
    config = Settings(
        ENV="production",
        SECRET_KEY="s" * 32,
        CORS_ALLOWED_ORIGINS=["*"],
    )

    with pytest.raises(RuntimeError, match="CORS_ALLOWED_ORIGINS"):
        validate_production_security(config)


def test_production_requires_password_reset_email_delivery():
    config = Settings(
        ENV="production",
        SECRET_KEY="s" * 32,
        CORS_ALLOWED_ORIGINS=["https://app.example.com"],
    )

    with pytest.raises(RuntimeError, match="SMTP_HOST and SMTP_FROM_EMAIL"):
        validate_production_security(config)


def test_production_requires_encrypted_smtp_and_paired_credentials():
    config = Settings(
        ENV="production",
        SECRET_KEY="s" * 32,
        CORS_ALLOWED_ORIGINS=["https://app.example.com"],
        SMTP_HOST="smtp.example.com",
        SMTP_FROM_EMAIL="noreply@example.com",
        SMTP_USE_TLS=False,
    )

    with pytest.raises(RuntimeError, match="encrypted SMTP"):
        validate_production_security(config)

    config.SMTP_USE_TLS = True
    config.SMTP_USERNAME = "sender"
    with pytest.raises(RuntimeError, match="must be configured together"):
        validate_production_security(config)


def test_nonproduction_allows_local_defaults_for_development():
    config = Settings(
        ENV="development",
        SECRET_KEY="short-secret",
        CORS_ALLOWED_ORIGINS=["*"],
    )

    validate_production_security(config)
