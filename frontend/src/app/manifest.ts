import type { MetadataRoute } from "next";

// Next.js App Router convention — auto-served at /manifest.webmanifest
// with the correct application/manifest+json content type, and the
// <link rel="manifest"> tag is injected automatically; no manual wiring
// needed in layout.tsx.
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "VIZU Academy",
    short_name: "VIZU",
    description: "VIZU Academy",
    start_url: "/",
    scope: "/",
    display: "standalone",
    orientation: "portrait-primary",
    theme_color: "#0e1834",
    background_color: "#0e1834",
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
