"""EmailService — sends the VIZU-Academy transactional emails.

Provider (settings.EMAIL_PROVIDER):
* "smtp"   — smtplib (standard library, no extra dependency), STARTTLS on
             587 or implicit TLS (SMTP_USE_SSL) on 465.
* "outbox" — development: writes a .eml file to EMAIL_OUTBOX_DIR
             (git-ignored); nothing is sent.
* ""       — "outbox" in development; any other APP_ENV refuses to send
             (EmailNotConfigured) instead of silently dropping mail.

Never logs codes, passwords or credentials — only "sent"/"failed" events
with a non-identifying reason."""

import smtplib
import ssl
import uuid
from datetime import datetime, timezone
from email.message import EmailMessage as MimeMessage
from email.utils import formataddr, make_msgid
from pathlib import Path

from app.core.config import settings
from app.core.logging.logger import logger
from app.services.email.templates import EmailMessage, password_reset_email, verification_email


class EmailDeliveryError(Exception):
    """Sending failed (provider error, network, rejected)."""


class EmailNotConfigured(EmailDeliveryError):
    """No email provider configured for this environment."""


def _provider() -> str:
    provider = (settings.EMAIL_PROVIDER or "").strip().lower()
    if provider:
        return provider
    return "outbox" if settings.APP_ENV == "development" else ""


def _build(to_address: str, message: EmailMessage) -> MimeMessage:
    sender = settings.EMAIL_FROM or "no-reply@vizu-deutsch.com"
    mime = MimeMessage()
    mime["Subject"] = message.subject
    mime["From"] = formataddr((settings.EMAIL_FROM_NAME or "VIZU-Academy", sender))
    mime["To"] = to_address
    mime["Message-ID"] = make_msgid(domain=sender.split("@")[-1] or "vizu-deutsch.com")
    mime["Date"] = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    mime.set_content(message.text)
    mime.add_alternative(message.html, subtype="html")
    return mime


class EmailService:
    def send(self, to_address: str, message: EmailMessage, kind: str) -> None:
        provider = _provider()
        mime = _build(to_address, message)
        try:
            if provider == "smtp":
                self._send_smtp(mime)
            elif provider == "outbox":
                self._write_outbox(mime)
            else:
                raise EmailNotConfigured("No email provider configured.")
        except EmailDeliveryError:
            logger.error("Email delivery failed: kind=%s provider=%s reason=not_configured", kind, provider or "none")
            raise
        except Exception as exc:  # network / SMTP errors — reason class only, never content
            logger.error("Email delivery failed: kind=%s provider=%s reason=%s", kind, provider, type(exc).__name__)
            raise EmailDeliveryError(type(exc).__name__) from exc
        logger.info("Email sent successfully: kind=%s provider=%s", kind, provider)

    def send_verification_code(self, to_address: str, name: str, code: str) -> None:
        self.send(to_address, verification_email(name, code), kind="registration_verification")

    def send_password_reset_code(self, to_address: str, name: str, code: str) -> None:
        self.send(to_address, password_reset_email(name, code), kind="password_reset")

    # ---- providers ----

    def _send_smtp(self, mime: MimeMessage) -> None:
        if not (settings.SMTP_HOST and settings.EMAIL_FROM):
            raise EmailNotConfigured("SMTP_HOST / EMAIL_FROM missing.")
        context = ssl.create_default_context()
        timeout = settings.SMTP_TIMEOUT_SECONDS
        if settings.SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout, context=context)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout)
        with server:
            if not settings.SMTP_USE_SSL and settings.SMTP_USE_TLS:
                server.starttls(context=context)
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(mime)

    def _write_outbox(self, mime: MimeMessage) -> None:
        if settings.APP_ENV not in ("development", "test"):
            raise EmailNotConfigured("The outbox provider is for development only.")
        folder = Path(settings.EMAIL_OUTBOX_DIR)
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")  # sortable, microseconds
        (folder / f"{stamp}-{uuid.uuid4().hex[:8]}.eml").write_bytes(bytes(mime))
