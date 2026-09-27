"use client";

import Script from "next/script";

import { notifyTelegramScriptLoaded } from "@/lib/telegram/webapp";

/** The one and only <script src="https://telegram.org/js/telegram-web-app.js">
 * tag in the app (mounted once from app/layout.tsx) — wrapped in its own
 * Client Component only because next/script's `onLoad` prop requires
 * one (a Server Component can't pass an event-handler function to a
 * Client Component). `onLoad` firing is what lets
 * lib/telegram/webapp.ts's waitForTelegramWebApp() resolve as soon as
 * the SDK is genuinely ready, instead of every caller guessing with a
 * single synchronous check that can run before the script has finished
 * loading. */
export default function TelegramWebAppScript() {
  return (
    <Script
      src="https://telegram.org/js/telegram-web-app.js"
      strategy="afterInteractive"
      onLoad={notifyTelegramScriptLoaded}
    />
  );
}
