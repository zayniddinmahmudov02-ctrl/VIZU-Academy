"""Every VIZU-DEUTSCH brand asset, made from the owner's official logo (2026-11-24).

Source: frontend/public/branding/vizu-logo-original.jpg = byte copy of docs/new_logo/logo png.jpg (640 x 640 JPEG: navy
rounded tile with a gold frame, octagram and the VA monogram, on a white canvas with a soft drop shadow).

The logo is never redrawn, recoloured, reshaped or regenerated. Every output carries the original tile's own pixels:
  1. the white canvas and its drop shadow OUTSIDE the tile become transparent (flood fill from the four corners; the
     anti-aliased rim gets its alpha from its share of gold and its colour un-mixed from the local canvas colour),
  2. the canvas is trimmed to the tile and padded square (nothing of the tile is cut),
  3. smaller sizes are Lanczos downscales with premultiplied alpha.
Icons that must be opaque (apple-touch-icon, maskable PWA icon, Android adaptive / round icon, splash) put the
unchanged tile in the middle of the app navy (#0e1834). The Android status-bar icon must be monochrome (the system
tints it): it is the tile's own light parts (gold frame, octagram, monogram) as white on transparent.

Run (Pillow only), from the repo root:  python frontend/scripts/generate-brand-assets.py
Outputs: frontend/public/branding/*, frontend/src/app/favicon.ico, frontend/public/favicon.png,
backend/app/data/branding/vizu-logo.png, mobile/assets/vizu-logo.png, mobile/android/app/src/main/res/*.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "frontend" / "public" / "branding" / "vizu-logo-original.jpg"
PUBLIC = ROOT / "frontend" / "public"
BRANDING = PUBLIC / "branding"
RES = ROOT / "mobile" / "android" / "app" / "src" / "main" / "res"
NAVY = (14, 24, 52, 255)

BG_MAX_SAT, BG_MIN_LUM = 60, 120  # canvas, shadow and gold/white rim mixes are light and unsaturated
RIM_SAT_FLOOR, GOLD_SAT = 12, 175  # saturation of plain canvas (JPEG noise) / of the solid gold frame


def _sat(p: tuple[int, int, int]) -> int:
    return max(p) - min(p)


def master(src: Path) -> Image.Image:
    """The tile on a transparent square canvas, at the source resolution."""
    rgb = Image.open(src).convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    cand = Image.new("L", (w, h), 0)
    cp = cand.load()
    for y in range(h):
        for x in range(w):
            p = px[x, y]
            if _sat(p) < BG_MAX_SAT and min(p) > BG_MIN_LUM:
                cp[x, y] = 255
    for corner in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        if cp[corner] == 255:
            ImageDraw.floodfill(cand, corner, 128)  # 128 = canvas connected to the edge (the white V inside stays 255)

    def canvas_colour(x: int, y: int) -> tuple[float, float, float]:
        acc, n = [0.0, 0.0, 0.0], 0
        for yy in range(max(0, y - 3), min(h, y + 4)):
            for xx in range(max(0, x - 3), min(w, x + 4)):
                q = px[xx, yy]
                if cp[xx, yy] == 128 and _sat(q) < RIM_SAT_FLOOR:
                    acc = [acc[0] + q[0], acc[1] + q[1], acc[2] + q[2]]
                    n += 1
        return (acc[0] / n, acc[1] / n, acc[2] / n) if n else (252.0, 252.0, 252.0)

    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    op = out.load()
    for y in range(h):
        for x in range(w):
            p = px[x, y]
            if cp[x, y] != 128:
                op[x, y] = (*p, 255)
                continue
            a = min(1.0, max(0.0, (_sat(p) - RIM_SAT_FLOOR) / (GOLD_SAT - RIM_SAT_FLOOR)))
            if a <= 0:
                continue
            b = canvas_colour(x, y)
            f = tuple(int(round(min(255.0, max(0.0, (c - (1 - a) * bc) / a)))) for c, bc in zip(p, b))
            op[x, y] = (*f, int(round(a * 255)))

    left, top, right, bottom = out.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    tile = out.crop((left, top, right, bottom))
    side = max(tile.size) + 2
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(tile, ((side - tile.width) // 2, (side - tile.height) // 2))
    print(f"source {w}x{h}; tile bbox {left},{top}-{right},{bottom} ({tile.width}x{tile.height}); master {side}x{side}")
    return sq


def scaled(img: Image.Image, size: int) -> Image.Image:
    return img.convert("RGBa").resize((size, size), Image.Resampling.LANCZOS).convert("RGBA")


def on_canvas(logo: Image.Image, size: int, scale: float, background: tuple[int, int, int, int] | None = None,
              circle: bool = False, height: int | None = None) -> Image.Image:
    """The logo at `scale` × the short side, centred on a size × height canvas (navy / navy circle / transparent)."""
    height = height or size
    canvas = Image.new("RGBA", (size, height), (0, 0, 0, 0))
    if background and circle:
        big = Image.new("L", (size * 4, height * 4), 0)
        ImageDraw.Draw(big).ellipse((0, 0, size * 4 - 1, height * 4 - 1), fill=255)
        canvas.paste(Image.new("RGBA", (size, height), background), (0, 0), big.resize((size, height), Image.Resampling.LANCZOS))
    elif background:
        canvas = Image.new("RGBA", (size, height), background)
    s = max(1, round(min(size, height) * scale))
    piece = scaled(logo, s)
    canvas.alpha_composite(piece, ((size - s) // 2, (height - s) // 2))
    return canvas


def status_icon(logo: Image.Image, size: int) -> Image.Image:
    """Monochrome notification icon: the tile's light parts (gold / white) as white, navy as transparent."""
    big = scaled(logo, size * 4)
    lum = big.convert("RGB").convert("L").point(lambda v: 0 if v < 70 else 255 if v > 150 else int((v - 70) * 255 / 80))
    alpha = Image.composite(lum, Image.new("L", big.size, 0), big.getchannel("A"))
    white = Image.new("RGBA", big.size, (255, 255, 255, 0))
    white.putalpha(alpha)
    return white.convert("RGBa").resize((size, size), Image.Resampling.LANCZOS).convert("RGBA")


def save(img: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)
    print(f"  {path.relative_to(ROOT).as_posix()}  {img.width}x{img.height}  {path.stat().st_size} B")


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else SRC
    logo = master(src)

    # web: the one central logo (+ sizes for srcset), favicons, PWA, iOS
    save(logo, BRANDING / "vizu-logo.png")
    for s in (64, 128, 256):
        save(scaled(logo, s), BRANDING / f"vizu-logo-{s}.png")
    save(scaled(logo, 32), PUBLIC / "favicon.png")
    save(scaled(logo, 32), BRANDING / "favicon-32.png")
    ico = ROOT / "frontend" / "src" / "app" / "favicon.ico"
    scaled(logo, 48).save(ico, sizes=[(48, 48), (32, 32), (16, 16)], append_images=[scaled(logo, 32), scaled(logo, 16)])
    print(f"  {ico.relative_to(ROOT).as_posix()}  16/32/48  {ico.stat().st_size} B")
    save(on_canvas(logo, 180, 0.86, NAVY), BRANDING / "apple-touch-icon.png")
    save(scaled(logo, 192), BRANDING / "icon-192.png")
    save(scaled(logo, 512), BRANDING / "icon-512.png")
    for s in (192, 512):
        save(on_canvas(logo, s, 0.6, NAVY), BRANDING / f"icon-maskable-{s}.png")

    # backend (Multilevel certificate PDF: the logo is printed at 30-34 pt, 192 px = 400+ dpi and keeps the PDF small) and the mobile copy
    save(scaled(logo, 192), ROOT / "backend" / "app" / "data" / "branding" / "vizu-logo.png")
    save(logo, ROOT / "mobile" / "assets" / "vizu-logo.png")

    # Android: launcher icons, splash, status-bar icon
    densities = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}
    for d, f in densities.items():
        legacy, adaptive = round(48 * f), round(108 * f)
        save(scaled(logo, legacy), RES / f"mipmap-{d}" / "ic_launcher.png")  # pre-Android 8: the tile itself
        save(on_canvas(logo, legacy, 0.66, NAVY, circle=True), RES / f"mipmap-{d}" / "ic_launcher_round.png")
        save(on_canvas(logo, adaptive, 0.6), RES / f"mipmap-{d}" / "ic_launcher_foreground.png")  # inside the 66 dp safe zone
        save(status_icon(logo, round(24 * f)), RES / f"drawable-{d}" / "ic_stat_vizu.png")
    splash = {"mdpi": (320, 480), "hdpi": (480, 800), "xhdpi": (720, 1280), "xxhdpi": (960, 1600), "xxxhdpi": (1280, 1920)}
    for d, (w, h) in splash.items():
        save(on_canvas(logo, w, 0.3, NAVY, height=h), RES / f"drawable-port-{d}" / "splash.png")
        save(on_canvas(logo, h, 0.3, NAVY, height=w), RES / f"drawable-land-{d}" / "splash.png")
    save(on_canvas(logo, 480, 0.3, NAVY, height=800), RES / "drawable" / "splash.png")
    save(on_canvas(logo, 432, 0.48), RES / "drawable" / "splash_icon.png")  # Android 12+: inside the 2/3 circle
    return 0


if __name__ == "__main__":
    sys.exit(main())
