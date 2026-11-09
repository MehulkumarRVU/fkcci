import logging
import smtplib
from email.mime.text import MIMEText

from ..config import settings

logger = logging.getLogger("pocketcoach.email")


def send_password_reset_email(to_email: str, reset_link: str) -> None:
    """Send a password-reset email when SMTP delivery is configured."""
    subject = "Reset your PocketCoach AI password"
    body = (
        "We received a request to reset your PocketCoach AI password.\n\n"
        f"Reset your password here: {reset_link}\n\n"
        "This link expires in 1 hour. If you didn't request this, you can safely ignore this email."
    )

    if not settings.SMTP_HOST:
        logger.warning("SMTP is not configured; password reset email delivery is disabled")
        return

    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME or "noreply@pocketcoach.ai"
    message["To"] = to_email

    with smtplib.SMTP(
        settings.SMTP_HOST,
        settings.SMTP_PORT,
        timeout=settings.SMTP_TIMEOUT_SECONDS,
    ) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(message)
