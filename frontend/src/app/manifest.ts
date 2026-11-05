import type { MetadataRoute } from "next";

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
    icons: [
      {
        src: "/icons/icon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icons/icon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icons/icon-maskable-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
  };
}
