// Generates the Android launcher icons (legacy, round, adaptive foreground) and splash images from
// assets/vizu-mark.svg. Run: `npm run assets` (from mobile/). Output overwrites android/app/src/main/res.
// Logo proportions are never stretched: the mark is always scaled uniformly and centered.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const res = join(root, "android", "app", "src", "main", "res");
const NAVY = "#0e1834";
const NAVY_2 = "#1b2a52";
// Inner content of the source SVG; the root's fill="none" is kept on a wrapper group (otherwise shapes fill black).
const mark = `<g fill="none">${readFileSync(join(root, "assets", "vizu-mark.svg"), "utf8")
  .replace(/^\s*<svg[^>]*>/, "").replace(/<\/svg>\s*$/, "").replace(/<!--[\s\S]*?-->/g, "")}</g>`;

// The mark (viewBox 0..100) placed at `scale` (fraction of the canvas) in the middle of a size×size canvas.
function markGroup(size, scale) {
  const s = (size * scale) / 100;
  const off = (size - size * scale) / 2;
  return `<g transform="translate(${off} ${off}) scale(${s})">${mark}</g>`;
}

function svg(size, body, { background = true, rounded = 0, circle = false } = {}) {
  const bg = `<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${NAVY}"/><stop offset="1" stop-color="${NAVY_2}"/></linearGradient></defs>`;
  const shape = circle
    ? `<circle cx="${size / 2}" cy="${size / 2}" r="${size / 2}" fill="url(#g)"/>`
    : `<rect width="${size}" height="${size}" rx="${rounded}" fill="url(#g)"/>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">${background ? bg + shape : ""}${body}</svg>`;
}

async function png(file, svgText, width, height = width) {
  mkdirSync(dirname(file), { recursive: true });
  await sharp(Buffer.from(svgText)).resize(width, height).png({ compressionLevel: 9 }).toFile(file);
}

const densities = { mdpi: 1, hdpi: 1.5, xhdpi: 2, xxhdpi: 3, xxxhdpi: 4 };

for (const [d, f] of Object.entries(densities)) {
  const legacy = Math.round(48 * f);
  const adaptive = Math.round(108 * f);
  // Legacy square icon (pre-Android 8): rounded navy square, mark at 72 %.
  await png(join(res, `mipmap-${d}`, "ic_launcher.png"), svg(512, markGroup(512, 0.72), { rounded: 96 }), legacy);
  await png(join(res, `mipmap-${d}`, "ic_launcher_round.png"), svg(512, markGroup(512, 0.7), { circle: true }), legacy);
  // Adaptive foreground: transparent, mark inside the 66 dp safe zone (≈ 56 % of 108 dp) so masks never cut it.
  await png(join(res, `mipmap-${d}`, "ic_launcher_foreground.png"), svg(1080, markGroup(1080, 0.56), { background: false }), adaptive);
}

// Splash (legacy drawable used by Theme.SplashScreen's window background): navy, mark at 26 % of the short side.
const splashSizes = { mdpi: [320, 480], hdpi: [480, 800], xhdpi: [720, 1280], xxhdpi: [960, 1600], xxxhdpi: [1280, 1920] };
async function splash(file, w, h) {
  const m = Math.round(Math.min(w, h) * 0.26);
  const body = `<rect width="${w}" height="${h}" fill="${NAVY}"/><g transform="translate(${(w - m) / 2} ${(h - m) / 2}) scale(${m / 100})">${mark}</g>`;
  await png(file, `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${body}</svg>`, w, h);
}
for (const [d, [w, h]] of Object.entries(splashSizes)) {
  await splash(join(res, `drawable-port-${d}`, "splash.png"), w, h);
  await splash(join(res, `drawable-land-${d}`, "splash.png"), h, w);
}
await splash(join(res, "drawable", "splash.png"), 480, 800);

// Android 12+ system splash icon: the mark on navy (shown inside the system's circular mask).
await png(join(res, "drawable", "splash_icon.png"), svg(432, markGroup(432, 0.5), { background: false }), 432);

writeFileSync(join(res, "values", "ic_launcher_background.xml"),
  `<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">${NAVY}</color>\n</resources>\n`);
console.log("assets written to", res);
