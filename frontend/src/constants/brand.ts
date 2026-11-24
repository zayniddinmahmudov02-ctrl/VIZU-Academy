/**
 * The one official VIZU-DEUTSCH logo (the owner's file, 2026-11-24). Every logo, favicon and app icon of the platform
 * comes from these files; never draw a logo in code. All of them are made by `frontend/scripts/generate-brand-assets.py`
 * from `public/branding/vizu-logo-original.jpg` (the unchanged original): only the white canvas around the tile is
 * made transparent and sizes are scaled — the logo itself is never redrawn or recoloured.
 */
export const BRAND_NAME = "VIZU-DEUTSCH";

export const BRAND_LOGO = {
  /** 128 px: the default for small places; the browser picks from `srcSet` by the rendered size and screen density. */
  src: "/branding/vizu-logo-128.png",
  srcSet: "/branding/vizu-logo-64.png 64w, /branding/vizu-logo-128.png 128w, /branding/vizu-logo-256.png 256w, /branding/vizu-logo.png 573w",
  /** The master (transparent PNG at the original resolution). */
  master: "/branding/vizu-logo.png",
  /** The owner's original file, byte for byte. */
  original: "/branding/vizu-logo-original.jpg",
} as const;

export const BRAND_ICONS = {
  favicon32: "/branding/favicon-32.png",
  icon192: "/branding/icon-192.png",
  icon512: "/branding/icon-512.png",
  maskable192: "/branding/icon-maskable-192.png",
  maskable512: "/branding/icon-maskable-512.png",
  appleTouch: "/branding/apple-touch-icon.png",
} as const;
