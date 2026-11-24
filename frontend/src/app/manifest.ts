import type { MetadataRoute } from "next";

import { BRAND_ICONS } from "@/constants/brand";

// Next.js App Router convention — auto-served at /manifest.webmanifest
// with the correct application/manifest+json content type, and the
// <link rel="manifest"> tag is injected automatically; no manual wiring
// needed in layout.tsx. iOS "Add to Home Screen" uses the apple-touch-icon
// and apple-mobile-web-app-* tags from layout.tsx (docs/ai-context/ios-pwa.md).
export default function manifest(): MetadataRoute.Manifest {
  return {
    id: "/",
    name: "VIZU DEUTSCH",
    short_name: "VIZU",
    description: "Lerne Deutsch. Überall. Jederzeit.",
    lang: "de",
    start_url: "/",
    scope: "/",
    display: "standalone",
    // "any": iPad / tablets in landscape; every page is responsive.
    orientation: "any",
    theme_color: "#0e1834",
    background_color: "#0e1834",
    categories: ["education"],
    // Official logo (constants/brand.ts): "any" = the tile on transparent, "maskable" = the tile inside the safe zone on navy.
    icons: [
      { src: BRAND_ICONS.icon192, sizes: "192x192", type: "image/png", purpose: "any" },
      { src: BRAND_ICONS.icon512, sizes: "512x512", type: "image/png", purpose: "any" },
      { src: BRAND_ICONS.maskable192, sizes: "192x192", type: "image/png", purpose: "maskable" },
      { src: BRAND_ICONS.maskable512, sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  };
}
