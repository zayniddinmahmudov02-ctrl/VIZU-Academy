"use client";

import { useSyncExternalStore } from "react";

import { isNativeAndroidApp, isStandalonePwa } from "@/features/mobile-app/utils/native";
import { detectPlatform, type PlatformInfo } from "@/features/mobile-app/utils/platform";

// navigator never changes during a page's life: nothing to subscribe to.
const subscribe = () => () => {};

let platformCache: PlatformInfo | null = null;
function platformSnapshot(): PlatformInfo {
  platformCache ??= detectPlatform(navigator.userAgent, navigator.maxTouchPoints);
  return platformCache;
}

/** Device OS / iOS browser; null during server rendering and hydration. */
export function usePlatform(): PlatformInfo | null {
  return useSyncExternalStore(subscribe, platformSnapshot, () => null);
}

/** True inside the installed Android app or a home-screen web app; false on the server. */
export function useRunsAsApp(): boolean {
  return useSyncExternalStore(subscribe, () => isNativeAndroidApp() || isStandalonePwa(), () => false);
}
