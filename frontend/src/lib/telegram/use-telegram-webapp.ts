"use client";

import { useEffect, useState } from "react";

import {
  getTelegramColorScheme,
  getTelegramThemeParams,
  getTelegramUser,
  initTelegramWebApp,
  isTelegramWebApp,
} from "./webapp";

interface TelegramWebAppState {
  isTelegram: boolean;
  user: TelegramWebAppUser | null;
  colorScheme: "light" | "dark" | null;
  themeParams: TelegramWebAppThemeParams | null;
}

const INITIAL_STATE: TelegramWebAppState = {
  isTelegram: false,
  user: null,
  colorScheme: null,
  themeParams: null,
};

/** Reusable Telegram Mini App context — mount TelegramWebAppInit once
 * (see components/telegram/telegram-webapp-init.tsx) for the global
 * ready()/expand()/viewport-height side effects; use this hook anywhere
 * else that just needs to read the current state (e.g. to show a
 * Telegram-only UI affordance). Always safe outside Telegram — every
 * field stays at its inert default and nothing here ever throws. */
export function useTelegramWebApp(): TelegramWebAppState {
  // Fixed hook calls, no branching above them — starts from a stable,
  // SSR-safe default (window doesn't exist on the server) and only
  // resolves the real Telegram state client-side after mount, same
  // hydration-safe pattern as every other browser-only hook in this app.
  const [state, setState] = useState<TelegramWebAppState>(INITIAL_STATE);

  useEffect(() => {
    if (!isTelegramWebApp()) return;

    setState({
      isTelegram: true,
      user: getTelegramUser(),
      colorScheme: getTelegramColorScheme(),
      themeParams: getTelegramThemeParams(),
    });
  }, []);

  return state;
}

/** Runs the one-time init side effects (ready/expand + live viewport-
 * height CSS variable) — call exactly once, from
 * TelegramWebAppInit. Kept separate from useTelegramWebApp so a
 * component that only wants to *read* state never accidentally
 * re-triggers ready()/expand(). */
export function useTelegramWebAppInit(): void {
  useEffect(() => {
    const webApp = typeof window !== "undefined" ? window.Telegram?.WebApp : undefined;
    if (!webApp) return;

    initTelegramWebApp();
    document.documentElement.classList.add("telegram-app");

    function applyViewportHeight() {
      document.documentElement.style.setProperty("--tg-viewport-height", `${webApp!.viewportHeight}px`);
    }

    applyViewportHeight();
    webApp.onEvent("viewportChanged", applyViewportHeight);

    return () => {
      webApp.offEvent("viewportChanged", applyViewportHeight);
    };
  }, []);
}
