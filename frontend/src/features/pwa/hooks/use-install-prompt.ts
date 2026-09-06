"use client";

import { useEffect, useState } from "react";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

function isStandaloneDisplay(): boolean {
  if (typeof window === "undefined") return false;
  const iosStandalone = (window.navigator as unknown as { standalone?: boolean }).standalone === true;
  return window.matchMedia?.("(display-mode: standalone)").matches || iosStandalone;
}

function isIOSDevice(): boolean {
  if (typeof window === "undefined") return false;
  // Standard iOS Safari detection: iPhone/iPad/iPod UA, excluding
  // Windows-with-touch devices that spoof "iPad" (MSStream check).
  return /iphone|ipad|ipod/i.test(window.navigator.userAgent) && !(window as unknown as { MSStream?: unknown }).MSStream;
}

/** Cross-browser install affordance state. Chrome/Edge/Android fire
 * `beforeinstallprompt` when installability criteria (manifest + service
 * worker + HTTPS) are met — captured here and replayed on demand via
 * promptInstall(). Safari (iOS and desktop) never fires this event at
 * all, so `isIOS` is exposed separately for the Share -> Add to Home
 * Screen instructions UI, which must only render on iOS Safari, never
 * as a fallback for "browser doesn't support install" in general
 * (desktop Firefox etc. simply gets no install UI at all — a wrong
 * button is worse than no button). */
export function useInstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isInstalled, setIsInstalled] = useState(false);
  const [isIOS, setIsIOS] = useState(false);

  useEffect(() => {
    setIsInstalled(isStandaloneDisplay());
    setIsIOS(isIOSDevice());

    function handleBeforeInstallPrompt(event: Event) {
      event.preventDefault();
      setDeferredPrompt(event as BeforeInstallPromptEvent);
    }

    function handleAppInstalled() {
      setDeferredPrompt(null);
      setIsInstalled(true);
    }

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
    window.addEventListener("appinstalled", handleAppInstalled);
    return () => {
      window.removeEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
      window.removeEventListener("appinstalled", handleAppInstalled);
    };
  }, []);

  async function promptInstall() {
    if (!deferredPrompt) return;
    await deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    setDeferredPrompt(null);
  }

  return {
    /** True once the browser has told us installation is possible right now. */
    canInstall: !isInstalled && deferredPrompt !== null,
    /** True on iOS Safari, not already installed — show the manual instructions instead. */
    showIOSInstructions: !isInstalled && isIOS && deferredPrompt === null,
    isInstalled,
    promptInstall,
  };
}
