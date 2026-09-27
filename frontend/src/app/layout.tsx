import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import { ThemeProvider } from "next-themes";
import "./globals.css";

import QueryProvider from "@/providers/query-provider";
import LanguageProvider from "@/providers/language-provider";
import ServiceWorkerRegistration from "@/components/pwa/service-worker-registration";
import TelegramWebAppInit from "@/components/telegram/telegram-webapp-init";
import TelegramWebAppScript from "@/components/telegram/telegram-webapp-script";

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "VIZU Academy",
  description: "German Learning Platform",
  // No explicit `manifest:` field here — src/app/manifest.ts (the App
  // Router file convention) already auto-injects the <link
  // rel="manifest"> tag; setting both was redundant (verified: Next
  // only ever renders one <link rel="manifest"> either way, but there's
  // no reason to carry two sources of truth for the same URL).
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "VIZU",
  },
  // Next 16.2.10's `appleWebApp.capable` only emits the generic
  // <meta name="mobile-web-app-capable">, NOT the traditional
  // <meta name="apple-mobile-web-app-capable"> older iOS/Safari
  // versions specifically look for (confirmed by reading
  // node_modules/next/dist/lib/metadata/metadata.js directly — this is
  // the framework's own behavior, not a misconfiguration on our side).
  // Added via `other` since Metadata's typed API has no field for it.
  other: {
    "apple-mobile-web-app-capable": "yes",
  },
  icons: {
    icon: [{ url: "/icon.svg", type: "image/svg+xml" }],
    apple: [{ url: "/icons/apple-touch-icon.png", sizes: "180x180", type: "image/png" }],
  },
};

// viewport-fit=cover is required for env(safe-area-inset-*) to resolve
// to real values on iOS (notch/Dynamic Island/home indicator) instead
// of 0 — see globals.css for the actual safe-area padding rules.
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#0e1834",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="de" className={inter.variable} suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <QueryProvider>
            <LanguageProvider>
              {children}
            </LanguageProvider>
          </QueryProvider>
        </ThemeProvider>
        <ServiceWorkerRegistration />
        {/* Telegram Mini App SDK — a plain <script>, not an npm package
            (see lib/telegram/webapp.ts). afterInteractive: doesn't block
            first paint; its onLoad (wired in TelegramWebAppScript) is
            what lets waitForTelegramWebApp() know the SDK has actually
            finished loading, instead of every caller guessing with a
            single synchronous check. Every accessor already handles
            window.Telegram being undefined regardless (ad-blocked,
            failed to load, or just an ordinary browser tab). */}
        <TelegramWebAppScript />
        <TelegramWebAppInit />
      </body>
    </html>
  );
}
