import sharp from "sharp";
import { writeFileSync } from "fs";

const BG = "#0e1834";
const GOLD = "#d4af37";
const GOLD_LIGHT = "#e4c877";

// Original icon.svg content, viewBox 0 0 100 100, full-bleed (edges touch
// the viewBox at the star points and the outer ring stroke).
const originalIconBody = `
  <rect width="100" height="100" rx="22" fill="${BG}" />
  <circle cx="50" cy="50" r="46" stroke="${GOLD}" stroke-opacity=".35" stroke-width="1.5" fill="none" />
  <g stroke="${GOLD}" stroke-width="2">
    <rect x="26" y="26" width="48" height="48" fill="none" />
    <rect x="26" y="26" width="48" height="48" transform="rotate(45 50 50)" fill="none" />
  </g>
  <g fill="${GOLD}">
    <ellipse cx="50" cy="24" rx="2.2" ry="6" />
    <ellipse cx="50" cy="24" rx="2.2" ry="6" transform="rotate(45 50 50)" />
    <ellipse cx="50" cy="24" rx="2.2" ry="6" transform="rotate(90 50 50)" />
    <ellipse cx="50" cy="24" rx="2.2" ry="6" transform="rotate(135 50 50)" />
    <ellipse cx="50" cy="24" rx="2.2" ry="6" transform="rotate(180 50 50)" />
    <ellipse cx="50" cy="24" rx="2.2" ry="6" transform="rotate(225 50 50)" />
    <ellipse cx="50" cy="24" rx="2.2" ry="6" transform="rotate(270 50 50)" />
    <ellipse cx="50" cy="24" rx="2.2" ry="6" transform="rotate(315 50 50)" />
  </g>
  <circle cx="50" cy="50" r="7" fill="${BG}" stroke="${GOLD}" stroke-width="1.5" />
  <circle cx="50" cy="50" r="2.6" fill="${GOLD_LIGHT}" />
`;

const squareSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">${originalIconBody}</svg>`;

// Maskable icon: OS may crop to a circle/squircle, so real content must
// stay within the inner ~80% "safe zone" (per W3C maskable-icon spec) —
// full-bleed background, original artwork scaled to 70% and centered.
const maskableSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" fill="${BG}" />
  <g transform="translate(15 15) scale(0.7)">${originalIconBody}</g>
</svg>`;

async function render(svg, size, outPath) {
  await sharp(Buffer.from(svg)).resize(size, size).png().toFile(outPath);
  console.log("wrote", outPath);
}

const outDir = process.argv[2];
await render(squareSvg, 192, `${outDir}/icon-192.png`);
await render(squareSvg, 512, `${outDir}/icon-512.png`);
await render(maskableSvg, 512, `${outDir}/icon-maskable-512.png`);
await render(squareSvg, 180, `${outDir}/apple-touch-icon.png`);
