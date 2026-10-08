"""Login identifier: an e-mail address OR a phone number ("E-mail yoki
telefon raqami"). One function decides which it is and normalises it, so
registration and login always compare the same canonical value.

* E-mail: trimmed + lower-cased (lookups are case-insensitive anyway).
* Phone: stored as "+<digits>" (E.164 style). Spaces, dashes, dots and
  brackets are ignored; a 9-digit local Uzbek number ("90 123 45 67") gets
  the +998 country code; "998..." without "+" is accepted too.

Phone-only accounts get an internal placeholder e-mail on a dedicated
subdomain (PHONE_EMAIL_DOMAIN) so every existing `users.email NOT NULL`
assumption keeps working — the same idea as the @telegram.local placeholder
of Telegram accounts. Nothing is ever sent to these addresses."""

import re
from dataclasses import dataclass

from email_validator import EmailNotValidError, validate_email

PHONE_EMAIL_DOMAIN = "phone.vizu-deutsch.com"
# Placeholder domains that can never be registered or typed as a real e-mail.
RESERVED_EMAIL_DOMAINS = (PHONE_EMAIL_DOMAIN, "telegram.local")

KIND_EMAIL = "email"
KIND_PHONE = "phone"

_PHONE_CHARS = re.compile(r"[\s\-().]")
UZ_COUNTRY_CODE = "998"


class InvalidIdentifier(ValueError):
    """Neither a valid e-mail address nor a valid phone number."""


@dataclass(frozen=True)
class LoginIdentifier:
    kind: str  # KIND_EMAIL | KIND_PHONE
    value: str  # normalised e-mail or "+<digits>"


def normalize_phone(raw: str) -> str | None:
    """"+<digits>" for a plausible phone number, else None."""
    text = _PHONE_CHARS.sub("", raw.strip())
    if text.startswith("00"):
        text = "+" + text[2:]
    has_plus = text.startswith("+")
    digits = text[1:] if has_plus else text
    if not digits.isdigit():
        return None
    if not has_plus and len(digits) == 9:  # local Uzbek mobile number
        digits = UZ_COUNTRY_CODE + digits
    if not 9 <= len(digits) <= 15:
        return None
    return "+" + digits


def parse_identifier(raw: str, strict: bool = False) -> LoginIdentifier:
    """`strict` (registration): the e-mail must be a valid address. Login is
    lenient on purpose — any existing account (admin, teacher, legacy data)
    is found by its stored address exactly as before, even one that today's
    validator would reject."""
    text = (raw or "").strip()
    if not text:
        raise InvalidIdentifier("empty")
    if "@" in text:
        if strict:
            try:
                validate_email(text, check_deliverability=False)
            except EmailNotValidError as exc:
                raise InvalidIdentifier("email") from exc
        local, _, domain = text.rpartition("@")
        if not local or not domain:
            raise InvalidIdentifier("email")
        return LoginIdentifier(KIND_EMAIL, text.lower())
    phone = normalize_phone(text)
    if phone is None:
        raise InvalidIdentifier("phone")
    return LoginIdentifier(KIND_PHONE, phone)


def is_reserved_email(email: str) -> bool:
    return email.lower().rsplit("@", 1)[-1] in RESERVED_EMAIL_DOMAINS


def phone_placeholder_email(phone: str) -> str:
    return f"{phone.lstrip('+')}@{PHONE_EMAIL_DOMAIN}"
