"use client";

import { useTelegramWebAppInit } from "@/lib/telegram/use-telegram-webapp";

/** Mounted once in the root layout (mirrors ServiceWorkerRegistration's
 * pattern) — calls WebApp.ready()/expand() and keeps --tg-viewport-height
 * in sync with Telegram's chrome. Renders nothing; a completely inert
 * no-op in any browser without window.Telegram.WebApp (the script tag
 * failing to load, an ad-blocker stripping it, or just a normal tab). */
export default function TelegramWebAppInit() {
  useTelegramWebAppInit();
  return null;
}
