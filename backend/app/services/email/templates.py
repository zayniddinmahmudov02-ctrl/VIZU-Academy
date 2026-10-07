"""German VIZU-Academy email templates (HTML + plain text).

Table-based, inline-styled HTML (what mail clients render reliably),
max-width 560px so it reads well on phones. Only the recipient's name and
the code are personal data in the message."""

from dataclasses import dataclass
from html import escape

WEBSITE = "https://vizu-deutsch.com"
NAVY = "#0f2a4a"
BLUE = "#2563eb"
LIGHT = "#eef4ff"
MUTED = "#5b6678"


@dataclass(frozen=True)
class EmailMessage:
    subject: str
    html: str
    text: str


def _layout(title: str, greeting: str, paragraphs_before: list[str], code: str, paragraphs_after: list[str]) -> str:
    before = "".join(
        f'<p style="margin:0 0 14px;font-size:15px;line-height:1.6;color:#1f2937;">{escape(p)}</p>' for p in paragraphs_before
    )
    after = "".join(
        f'<p style="margin:0 0 12px;font-size:14px;line-height:1.6;color:{MUTED};">{escape(p)}</p>' for p in paragraphs_after
    )
    spaced = " ".join(code)
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>{escape(title)}</title>
</head>
<body style="margin:0;padding:0;background:#f3f6fb;font-family:Arial,Helvetica,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f3f6fb;padding:24px 12px;">
  <tr><td align="center">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #dde5f0;">
      <tr><td style="background:{NAVY};padding:22px 28px;">
        <span style="font-size:20px;font-weight:bold;letter-spacing:2px;color:#ffffff;">VIZU-ACADEMY</span>
      </td></tr>
      <tr><td style="height:4px;background:{BLUE};line-height:4px;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:30px 28px 10px;">
        <h1 style="margin:0 0 18px;font-size:21px;line-height:1.3;color:{NAVY};">{escape(title)}</h1>
        <p style="margin:0 0 14px;font-size:15px;line-height:1.6;color:#1f2937;">{escape(greeting)}</p>
        {before}
        <table role="presentation" cellpadding="0" cellspacing="0" style="margin:8px 0 22px;">
          <tr><td style="background:{LIGHT};border:1px solid #c9d8f5;border-radius:10px;padding:16px 22px;">
            <span style="font-family:'Courier New',Courier,monospace;font-size:28px;font-weight:bold;letter-spacing:4px;white-space:nowrap;color:{NAVY};">{escape(spaced)}</span>
          </td></tr>
        </table>
        {after}
      </td></tr>
      <tr><td style="padding:18px 28px 26px;border-top:1px solid #e6ebf3;">
        <p style="margin:0;font-size:13px;font-weight:bold;color:{NAVY};">VIZU-Academy</p>
        <p style="margin:4px 0 0;font-size:13px;"><a href="{WEBSITE}" style="color:{BLUE};text-decoration:none;">{WEBSITE}</a></p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""


def _text(greeting: str, before: list[str], code: str, after: list[str]) -> str:
    return "\n\n".join([greeting, *before, code, *after, f"VIZU-Academy\n{WEBSITE}"]) + "\n"


def verification_email(name: str, code: str) -> EmailMessage:
    greeting = f"Hallo {name},"
    before = [
        "vielen Dank für Ihre Registrierung bei VIZU-Academy.",
        "Bitte verwenden Sie den folgenden Bestätigungscode:",
    ]
    after = [
        "Der Code ist 10 Minuten gültig.",
        "Wenn Sie diese Registrierung nicht vorgenommen haben, können Sie diese E-Mail ignorieren.",
    ]
    return EmailMessage(
        subject="Ihr Bestätigungscode für VIZU-Academy",
        html=_layout("E-Mail-Adresse bestätigen", greeting, before, code, after),
        text=_text(greeting, before, code, after),
    )


def password_reset_email(name: str, code: str) -> EmailMessage:
    greeting = f"Hallo {name},"
    before = [
        "Sie haben eine Anfrage zum Zurücksetzen Ihres Passworts gestellt.",
        "Ihr Bestätigungscode lautet:",
    ]
    after = [
        "Der Code ist 10 Minuten gültig.",
        "Wenn Sie diese Anfrage nicht gestellt haben, können Sie diese E-Mail ignorieren. Ihr Passwort bleibt unverändert.",
    ]
    return EmailMessage(
        subject="Passwort zurücksetzen – VIZU-Academy",
        html=_layout("Passwort zurücksetzen", greeting, before, code, after),
        text=_text(greeting, before, code, after),
    )
