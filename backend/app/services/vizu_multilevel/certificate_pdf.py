"""VIZU-Multilevel certificate PDF (A4 landscape, vector-only, reportlab).

One shared layout (BaseCertificate below) + CERTIFICATE_THEMES: only the
level-specific styling changes — frame, corner ornaments, accent colour,
level badge, seal and (C1) watermark — so A1..C1 read as five levels of the
same certificate system. "Niveau unter A1" (BELOW_A1) has its own calm,
minimal theme and neutral wording ("teilgenommen … Ergebnis erzielt"): the
result is shown in full, never as "nicht bestanden". All visible text is German (the director title is
kept exactly as "Director of VIZU-Academy" by design).

Fonts: the PDF standard fonts Times / Helvetica — built into every PDF reader,
no font files or licences needed, and they render ä ö ü Ä Ö Ü ß. The logo is
the official VIZU mark (frontend components/common/logo.tsx) redrawn as
vectors. No QR code, no images, no external calls.
"""

import io
import math
from dataclasses import dataclass

from fastapi.responses import Response
from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from app.services.vizu_multilevel.certificate_service import (
    BELOW_A1_LEVEL,
    CertificateData,
    format_points,
    german_date,
    level_label,
    pdf_filename,
)

PAGE_W, PAGE_H = landscape(A4)  # 841.89 x 595.28 pt = 297 x 210 mm
WEBSITE = "https://vizu-deutsch.com"
DIRECTOR_NAME = "Zayniddinkhuja Makhmudov"
DIRECTOR_TITLE = "Director of VIZU-Academy"

NAVY = HexColor("#0e1834")  # logo background
INK = HexColor("#0f2a4a")  # VIZU dark blue text
GOLD = HexColor("#c9a227")
GOLD_LIGHT = HexColor("#e4c877")
MUTED = HexColor("#5b6678")
RULE = HexColor("#d5dbe5")

SERIF, SERIF_BOLD, SERIF_ITALIC = "Times-Roman", "Times-Bold", "Times-Italic"
SANS, SANS_BOLD = "Helvetica", "Helvetica-Bold"


@dataclass(frozen=True)
class CertificateTheme:
    level: str
    accent: Color  # level colour (badge, rules, ornaments)
    accent_soft: Color  # tinted backgrounds
    secondary: Color  # second accent (A2+)
    frame: str  # soft | single | double | bracketed | banded | prestige
    corners: str  # none | squares | brackets | diamonds | rosettes
    seal: str  # none | ring | double_ring | rosette
    guilloche: bool  # fine concentric arcs in the corners
    watermark: bool  # large faint logo behind the content
    badge_filled: bool  # level badge filled vs. outlined


CERTIFICATE_THEMES: dict[str, CertificateTheme] = {
    # "Niveau unter A1" — calm and minimal: slate frame with a thin blue top
    # edge, outlined badge, no ornaments or seal. Same family, clearly distinct.
    BELOW_A1_LEVEL: CertificateTheme(
        BELOW_A1_LEVEL, HexColor("#475569"), HexColor("#f1f5f9"), HexColor("#94a3b8"), "soft", "none", "none", False, False, False
    ),
    # Entry level — minimal: one thin frame, light blue, outlined badge.
    "A1": CertificateTheme("A1", HexColor("#3b82f6"), HexColor("#eef4ff"), HexColor("#93c5fd"), "single", "none", "none", False, False, False),
    # Double rule, teal secondary accent, small corner squares.
    "A2": CertificateTheme("A2", HexColor("#2563eb"), HexColor("#eaf1ff"), HexColor("#0d9488"), "double", "squares", "none", False, False, False),
    # Academic: double frame with corner brackets, ring seal, filled badge.
    "B1": CertificateTheme("B1", HexColor("#1d4ed8"), HexColor("#e8eefc"), HexColor("#475569"), "bracketed", "brackets", "ring", False, False, True),
    # Premium: navy band + gold line, diamonds, guilloche corners, double-ring seal.
    "B2": CertificateTheme("B2", HexColor("#1e3a8a"), HexColor("#e7ecf7"), GOLD, "banded", "diamonds", "double_ring", True, False, True),
    # Highest prestige: navy/gold frame, rosettes, guilloche, watermark, gold seal.
    "C1": CertificateTheme("C1", NAVY, HexColor("#f6f1e1"), GOLD, "prestige", "rosettes", "rosette", True, True, True),
}

MARGIN = 22  # outer frame inset (pt)


# ============================================================
# Primitives
# ============================================================


def _text_width(text: str, font: str, size: float, char_space: float = 0) -> float:
    return stringWidth(text, font, size) + char_space * max(len(text) - 1, 0)


def _centered(c: Canvas, text: str, y: float, font: str, size: float, color: Color, char_space: float = 0, x: float = PAGE_W / 2) -> None:
    width = _text_width(text, font, size, char_space)
    t = c.beginText(x - width / 2, y)
    t.setFont(font, size)
    t.setCharSpace(char_space)
    t.setFillColor(color)
    t.textOut(text)
    c.drawText(t)


def _fit_size(text: str, font: str, max_width: float, start: float, minimum: float) -> float:
    size = start
    while size > minimum and stringWidth(text, font, size) > max_width:
        size -= 0.5
    return size


def _with_alpha(color: Color, alpha: float) -> Color:
    # reportlab takes the transparency from the colour object itself, so a
    # faint drawing needs colours that carry their alpha.
    return Color(color.red, color.green, color.blue, alpha=alpha)


def draw_logo(c: Canvas, cx: float, cy: float, size: float, alpha: float = 1.0, background: bool = True) -> None:
    """The official VIZU mark (logo.tsx, viewBox 0..100) as vectors."""
    gold, navy, light = (_with_alpha(x, alpha) for x in (GOLD, NAVY, GOLD_LIGHT))
    c.saveState()
    if background:
        c.setFillColor(navy)
        c.roundRect(cx - size / 2, cy - size / 2, size, size, size * 0.22, stroke=0, fill=1)
    s = size * 0.7 / 100
    c.translate(cx - 50 * s, cy + 50 * s)
    c.scale(s, -s)
    c.setStrokeColor(_with_alpha(GOLD, 0.35 * alpha))
    c.setLineWidth(1.5)
    c.circle(50, 50, 46, stroke=1, fill=0)
    c.setStrokeColor(gold)
    c.setLineWidth(2)
    c.rect(26, 26, 48, 48, stroke=1, fill=0)
    c.saveState()
    c.translate(50, 50)
    c.rotate(45)
    c.rect(-24, -24, 48, 48, stroke=1, fill=0)
    c.restoreState()
    c.setFillColor(gold)
    for deg in range(0, 360, 45):
        c.saveState()
        c.translate(50, 50)
        c.rotate(deg)
        c.ellipse(-2.2, -32, 2.2, -20, stroke=0, fill=1)
        c.restoreState()
    c.setFillColor(navy if background else _with_alpha(white, alpha))
    c.setLineWidth(1.5)
    c.circle(50, 50, 7, stroke=1, fill=1)
    c.setFillColor(light)
    c.circle(50, 50, 2.6, stroke=0, fill=1)
    c.restoreState()


# ============================================================
# Level-specific decoration
# ============================================================


def _frame(c: Canvas, theme: CertificateTheme) -> None:
    x0, y0, w, h = MARGIN, MARGIN, PAGE_W - 2 * MARGIN, PAGE_H - 2 * MARGIN
    c.saveState()
    if theme.frame == "soft":
        # unter A1: one slate hairline frame, fine blue rules top and bottom
        c.setStrokeColor(theme.accent)
        c.setLineWidth(0.6)
        c.rect(x0, y0, w, h)
        c.setStrokeColor(HexColor("#3b82f6"))
        c.setLineWidth(1.2)
        c.line(x0 + 40, y0 + h - 8, x0 + w - 40, y0 + h - 8)
        c.line(x0 + 40, y0 + 8, x0 + w - 40, y0 + 8)
    elif theme.frame == "single":
        c.setStrokeColor(INK)
        c.setLineWidth(0.8)
        c.rect(x0, y0, w, h)
        c.setStrokeColor(theme.accent)
        c.setLineWidth(2)
        c.line(x0, y0 + h, x0 + w, y0 + h)  # accent top edge only
    elif theme.frame == "double":
        c.setStrokeColor(INK)
        c.setLineWidth(1)
        c.rect(x0, y0, w, h)
        c.setStrokeColor(theme.secondary)
        c.setLineWidth(0.6)
        c.rect(x0 + 6, y0 + 6, w - 12, h - 12)
    elif theme.frame == "bracketed":
        c.setStrokeColor(INK)
        c.setLineWidth(1.4)
        c.rect(x0, y0, w, h)
        c.setStrokeColor(theme.accent)
        c.setLineWidth(0.5)
        c.rect(x0 + 8, y0 + 8, w - 16, h - 16)
        c.rect(x0 + 11, y0 + 11, w - 22, h - 22)
    elif theme.frame == "banded":
        c.setFillColor(theme.accent)
        c.rect(x0, y0, w, h, stroke=0, fill=1)
        c.setFillColor(white)
        c.rect(x0 + 7, y0 + 7, w - 14, h - 14, stroke=0, fill=1)
        c.setStrokeColor(GOLD)
        c.setLineWidth(0.8)
        c.rect(x0 + 12, y0 + 12, w - 24, h - 24)
    elif theme.frame == "prestige":
        c.setFillColor(NAVY)
        c.rect(x0, y0, w, h, stroke=0, fill=1)
        c.setFillColor(white)
        c.rect(x0 + 11, y0 + 11, w - 22, h - 22, stroke=0, fill=1)
        c.setStrokeColor(GOLD)
        c.setLineWidth(1.2)
        c.rect(x0 + 4, y0 + 4, w - 8, h - 8)
        c.setLineWidth(0.6)
        c.rect(x0 + 16, y0 + 16, w - 32, h - 32)
        c.rect(x0 + 19, y0 + 19, w - 38, h - 38)
    c.restoreState()


def _corner_points(inset: float) -> list[tuple[float, float, int, int]]:
    """(x, y, dx, dy) for each corner; d* point inwards."""
    l, r = MARGIN + inset, PAGE_W - MARGIN - inset
    b, t = MARGIN + inset, PAGE_H - MARGIN - inset
    return [(l, t, 1, -1), (r, t, -1, -1), (l, b, 1, 1), (r, b, -1, 1)]


def _corners(c: Canvas, theme: CertificateTheme) -> None:
    c.saveState()
    if theme.corners == "squares":
        c.setFillColor(theme.accent)
        for x, y, dx, dy in _corner_points(6):
            c.rect(x - 3, y - 3, 6, 6, stroke=0, fill=1)
    elif theme.corners == "brackets":
        c.setStrokeColor(theme.accent)
        c.setLineWidth(2)
        for x, y, dx, dy in _corner_points(18):
            c.line(x, y, x + dx * 34, y)
            c.line(x, y, x, y + dy * 34)
            c.setLineWidth(0.6)
            c.line(x + dx * 6, y + dy * 6, x + dx * 22, y + dy * 6)
            c.line(x + dx * 6, y + dy * 6, x + dx * 6, y + dy * 22)
            c.setLineWidth(2)
    elif theme.corners == "diamonds":
        for x, y, dx, dy in _corner_points(20):
            cx, cy = x + dx * 10, y + dy * 10
            c.setFillColor(theme.accent)
            p = c.beginPath()
            p.moveTo(cx, cy + 9)
            p.lineTo(cx + 9, cy)
            p.lineTo(cx, cy - 9)
            p.lineTo(cx - 9, cy)
            p.close()
            c.drawPath(p, stroke=0, fill=1)
            c.setFillColor(GOLD)
            c.circle(cx, cy, 2.2, stroke=0, fill=1)
            c.setStrokeColor(GOLD)
            c.setLineWidth(0.6)
            c.line(cx + dx * 14, cy, cx + dx * 60, cy)
            c.line(cx, cy + dy * 14, cx, cy + dy * 40)
    elif theme.corners == "rosettes":
        for x, y, dx, dy in _corner_points(30):
            draw_logo(c, x + dx * 4, y + dy * 4, 30, background=False)
            c.setStrokeColor(GOLD)
            c.setLineWidth(0.6)
            c.line(x + dx * 24, y + dy * 4, x + dx * 90, y + dy * 4)
            c.line(x + dx * 4, y + dy * 24, x + dx * 4, y + dy * 60)
    c.restoreState()


def _guilloche(c: Canvas, theme: CertificateTheme) -> None:
    """Fine concentric arcs radiating from each corner (security-print feel)."""
    c.saveState()
    c.setStrokeColor(theme.secondary)
    c.setStrokeAlpha(0.18)
    c.setLineWidth(0.35)
    for x, y, dx, dy in _corner_points(14):
        start = {(1, -1): 270, (-1, -1): 180, (1, 1): 0, (-1, 1): 90}[(dx, dy)]
        for r in range(18, 120, 6):
            c.arc(x - r, y - r, x + r, y + r, startAng=start, extent=90)
    c.restoreState()


def _seal(c: Canvas, theme: CertificateTheme, cx: float, cy: float) -> None:
    if theme.seal == "none":
        return
    c.saveState()
    if theme.seal == "ring":
        c.setStrokeColor(theme.accent)
        c.setLineWidth(1.4)
        c.circle(cx, cy, 30)
        c.setLineWidth(0.5)
        c.circle(cx, cy, 25)
        color = theme.accent
    elif theme.seal == "double_ring":
        c.setFillColor(theme.accent)
        c.circle(cx, cy, 32, stroke=0, fill=1)
        c.setStrokeColor(GOLD)
        c.setLineWidth(1)
        c.circle(cx, cy, 28)
        c.setLineWidth(0.4)
        c.circle(cx, cy, 25)
        color = white
    else:  # rosette (C1)
        c.setFillColor(GOLD)
        for i in range(24):
            ang = math.radians(i * 15)
            c.circle(cx + 33 * math.cos(ang), cy + 33 * math.sin(ang), 4.2, stroke=0, fill=1)
        c.circle(cx, cy, 33, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.circle(cx, cy, 27, stroke=0, fill=1)
        c.setStrokeColor(GOLD_LIGHT)
        c.setLineWidth(0.6)
        c.circle(cx, cy, 24)
        color = GOLD_LIGHT
    _centered(c, "VIZU", cy + 8, SANS_BOLD, 6.5, color, char_space=1.2, x=cx)
    _centered(c, theme.level, cy - 8, SERIF_BOLD, 17, color, x=cx)
    c.restoreState()


def _watermark(c: Canvas) -> None:
    draw_logo(c, PAGE_W / 2, PAGE_H / 2 - 10, 300, alpha=0.035, background=False)


# ============================================================
# Shared layout
# ============================================================


def _header(c: Canvas, theme: CertificateTheme) -> None:
    mark = 34
    word = "VIZU-AKADEMIE"
    word_w = _text_width(word, SANS_BOLD, 15, 2.2)
    total = mark + 12 + word_w
    x = PAGE_W / 2 - total / 2
    y = PAGE_H - 92
    draw_logo(c, x + mark / 2, y + 6, mark)
    t = c.beginText(x + mark + 12, y + 6)
    t.setFont(SANS_BOLD, 15)
    t.setCharSpace(2.2)
    t.setFillColor(INK)
    t.textOut(word)
    c.drawText(t)
    t = c.beginText(x + mark + 12, y - 7)
    t.setFont(SANS, 7.5)
    t.setCharSpace(0.4)
    t.setFillColor(MUTED)
    t.textOut("Visuales Institut für Zukunft und Unterricht")
    c.drawText(t)


def _body(c: Canvas, theme: CertificateTheme, data: CertificateData) -> None:
    cx = PAGE_W / 2
    _centered(c, "ZERTIFIKAT", 432, SERIF_BOLD, 40, INK, char_space=7)
    c.setStrokeColor(theme.accent)
    c.setLineWidth(1.2)
    c.line(cx - 46, 418, cx + 46, 418)
    _centered(c, "VIZU-Multilevel-Prüfung", 400, SANS, 10, MUTED, char_space=2)

    _centered(c, "Hiermit wird bestätigt, dass", 368, SERIF_ITALIC, 13, MUTED)
    size = _fit_size(data.student_name, SERIF_BOLD, 560, 31, 16)
    _centered(c, data.student_name, 334, SERIF_BOLD, size, INK)
    c.setStrokeColor(RULE)
    c.setLineWidth(0.7)
    c.line(cx - 210, 324, cx + 210, 324)
    below_a1 = data.level == BELOW_A1_LEVEL
    if below_a1:
        _centered(c, "an der VIZU-Multilevel-Prüfung teilgenommen und folgendes Ergebnis erzielt hat:", 302, SERIF, 13, INK)
    else:
        _centered(c, "die VIZU-Multilevel-Prüfung erfolgreich abgelegt und das", 302, SERIF, 13, INK)

    label = f"Niveau {level_label(data.level)}"
    bw, bh = _text_width(label, SERIF_BOLD, 22, 1.5) + 48, 36
    c.saveState()
    if theme.badge_filled:
        c.setFillColor(theme.accent)
        c.roundRect(cx - bw / 2, 255, bw, bh, 6, stroke=0, fill=1)
        if theme.level in ("B2", "C1"):
            c.setStrokeColor(GOLD)
            c.setLineWidth(0.8)
            c.roundRect(cx - bw / 2 + 3, 258, bw - 6, bh - 6, 4, stroke=1, fill=0)
        text_color = GOLD_LIGHT if theme.level == "C1" else white
    else:
        c.setFillColor(theme.accent_soft)
        c.setStrokeColor(theme.accent)
        c.setLineWidth(1)
        c.roundRect(cx - bw / 2, 255, bw, bh, 6, stroke=1, fill=1)
        text_color = theme.accent
    c.restoreState()
    _centered(c, label, 266, SERIF_BOLD, 22, text_color, char_space=1.5)
    if not below_a1:
        _centered(c, "erreicht hat.", 234, SERIF, 13, INK)

    # Competencies — four cells, then the total line.
    cell_w, cell_h, gap = 112, 40, 12
    row_w = 4 * cell_w + 3 * gap
    x = cx - row_w / 2
    y = 172
    for line in data.competencies:
        c.saveState()
        c.setFillColor(theme.accent_soft)
        c.setStrokeColor(RULE)
        c.setLineWidth(0.5)
        c.roundRect(x, y, cell_w, cell_h, 5, stroke=1, fill=1)
        c.restoreState()
        _centered(c, line.label.upper(), y + 26, SANS_BOLD, 7.5, MUTED, char_space=1.2, x=x + cell_w / 2)
        value = f"{format_points(line.points)} / 25" if line.points is not None else "—"
        _centered(c, value, y + 9, SANS_BOLD, 13, INK, x=x + cell_w / 2)
        x += cell_w + gap
    _centered(c, f"Gesamtergebnis: {data.total_score} / 100 Punkte", 150, SANS_BOLD, 11.5, theme.accent if theme.level != "C1" else INK)


def _footer(c: Canvas, theme: CertificateTheme, data: CertificateData) -> None:
    left_x = MARGIN + 62
    c.setFillColor(INK)
    c.setFont(SANS_BOLD, 10.5)
    c.drawString(left_x, 98, f"Ausgestellt am: {german_date(data.completed_at)}")
    c.setFont(SANS, 8.5)
    c.setFillColor(MUTED)
    c.drawString(left_x, 82, f"Zertifikatsnummer: {data.certificate_number}")

    right_cx = PAGE_W - MARGIN - 150
    c.setStrokeColor(INK)
    c.setLineWidth(0.7)
    c.line(right_cx - 95, 106, right_cx + 95, 106)
    _centered(c, DIRECTOR_NAME, 90, SERIF_BOLD, 13, INK, x=right_cx)
    _centered(c, DIRECTOR_TITLE, 76, SANS, 8.5, MUTED, char_space=0.6, x=right_cx)

    _seal(c, theme, PAGE_W / 2, 106)

    link_y = 50
    _centered(c, WEBSITE, link_y, SANS, 9, theme.accent if theme.level != "C1" else INK, char_space=0.4)
    w = _text_width(WEBSITE, SANS, 9, 0.4)
    c.linkURL(WEBSITE, (PAGE_W / 2 - w / 2, link_y - 3, PAGE_W / 2 + w / 2, link_y + 10), relative=0, thickness=0)


def render_certificate_pdf(data: CertificateData) -> bytes:
    """BaseCertificate: shared layout; the theme supplies the level identity."""
    theme = CERTIFICATE_THEMES[data.level]
    buffer = io.BytesIO()
    c = Canvas(buffer, pagesize=(PAGE_W, PAGE_H), pageCompression=1)
    c.setTitle(f"VIZU-Multilevel-Zertifikat – Niveau {level_label(data.level)}")
    c.setAuthor("VIZU-Akademie")
    c.setSubject("VIZU-Multilevel-Prüfung")
    c.setCreator("VIZU-Akademie")
    c.setKeywords(f"Zertifikat, Niveau {level_label(data.level)}, {data.certificate_number}")

    c.setFillColor(white)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    _frame(c, theme)  # paints the white inner area — decorations go on top
    if theme.watermark:
        _watermark(c)
    if theme.guilloche:
        _guilloche(c, theme)
    _corners(c, theme)
    _header(c, theme)
    _body(c, theme, data)
    _footer(c, theme, data)
    c.showPage()
    c.save()
    return buffer.getvalue()


def certificate_pdf_response(data: CertificateData) -> Response:
    """Download response (student and admin share it)."""
    return Response(
        content=render_certificate_pdf(data),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{pdf_filename(data)}"',
            "Cache-Control": "private, no-store",
        },
    )
