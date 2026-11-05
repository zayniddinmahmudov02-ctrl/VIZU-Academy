/** Pure helpers for the VIZU DEUTSCH app pages (download page, install guide, native update prompt).
 * No DOM access here, so they run in node --test; callers pass navigator values in. */

export type DeviceOs = "android" | "ios" | "desktop";
export type IosBrowser = "safari" | "chrome" | "firefox" | "edge" | "other" | null;

export interface PlatformInfo {
  os: DeviceOs;
  /** iOS only: which browser — "Add to Home Screen" works reliably from Safari. */
  iosBrowser: IosBrowser;
  /** Telegram / Instagram / Facebook in-app browsers cannot install apps. */
  inAppBrowser: boolean;
}

export function detectPlatform(userAgent: string, maxTouchPoints = 0): PlatformInfo {
  const ua = userAgent || "";
  // iPadOS 13+ reports itself as a Mac: a "Macintosh" with a touch screen is an iPad.
  const isIos = /iPhone|iPad|iPod/i.test(ua) || (/Macintosh/i.test(ua) && maxTouchPoints > 1);
  const isAndroid = /Android/i.test(ua);
  const inAppBrowser = /Telegram|Instagram|FBAN|FBAV|Line\//i.test(ua);
  let iosBrowser: IosBrowser = null;
  if (isIos) {
    if (/CriOS/i.test(ua)) iosBrowser = "chrome";
    else if (/FxiOS/i.test(ua)) iosBrowser = "firefox";
    else if (/EdgiOS/i.test(ua)) iosBrowser = "edge";
    else if (inAppBrowser || !/Safari/i.test(ua)) iosBrowser = "other";
    else iosBrowser = "safari";
  }
  return { os: isIos ? "ios" : isAndroid ? "android" : "desktop", iosBrowser, inAppBrowser };
}

/** True when the installed Android app (Capacitor) has a lower versionCode than the latest release. */
export function isUpdateAvailable(installedBuild: string | number | null | undefined, latestVersionCode: number | null | undefined): boolean {
  const installed = Number(installedBuild);
  if (!Number.isFinite(installed) || installed <= 0 || !latestVersionCode) return false;
  return latestVersionCode > installed;
}

export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** Groups a SHA-256 hex digest in blocks of 8 so people can compare it by eye. */
export function groupChecksum(hex: string): string {
  return (hex || "").toLowerCase().replace(/[^0-9a-f]/g, "").match(/.{1,8}/g)?.join(" ") ?? "";
}
