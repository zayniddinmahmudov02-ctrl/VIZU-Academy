"use client";

import { useEffect, useState } from "react";

import {
  getTelegramColorScheme,
  getTelegramThemeParams,
  getTelegramUser,
  initTelegramWebApp,
  waitForTelegramWebApp,
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
    // A single synchronous check here — the bug this whole file was
    // rewritten to fix — can run before next/script's SDK has finished
    // loading and permanently conclude "not Telegram." Waiting (which
    // resolves immediately if it's already loaded) is what makes this
    // correct instead of racy; the AbortController makes it safe to
    // cancel if the component unmounts (or Strict Mode replays this
    // effect) before that resolves.
    const controller = new AbortController();

    waitForTelegramWebApp({ signal: controller.signal }).then((webApp) => {
      if (!webApp) return;

      setState({
        isTelegram: true,
        user: getTelegramUser(),
        colorScheme: getTelegramColorScheme(),
        themeParams: getTelegramThemeParams(),
      });
    });

    return () => controller.abort();
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
    // Same fix as useTelegramWebApp above: wait for the SDK instead of
    // checking window.Telegram.WebApp exactly once. This is also the
    // effect responsible for calling ready()/expand() at all — if the
    // one-shot check lost the race, this Mini App's chrome/viewport
    // never got initialized either, not just auto-login.
    const controller = new AbortController();
    let cleanupViewportListener: (() => void) | null = null;

    waitForTelegramWebApp({ signal: controller.signal }).then((result) => {
      if (!result) return;

      // Narrowed to a non-null local — TS can't carry the `!result`
      // check above into the nested function declaration below on its
      // own (it only narrows the outer closed-over binding at the point
      // of the check, not inside a separately-called inner function).
      const webApp: TelegramWebApp = result;

      initTelegramWebApp();
      document.documentElement.classList.add("telegram-app");

      function applyViewportHeight() {
        document.documentElement.style.setProperty("--tg-viewport-height", `${webApp.viewportHeight}px`);
      }

      applyViewportHeight();
      webApp.onEvent("viewportChanged", applyViewportHeight);
      cleanupViewportListener = () => webApp.offEvent("viewportChanged", applyViewportHeight);
    });

    return () => {
      controller.abort();
      cleanupViewportListener?.();
    };
  }, []);
}
