/** Runtime checks for the VIZU DEUTSCH Android app (Capacitor shell) and the installed iOS/Android PWA.
 *
 * The Android app loads this website; Capacitor injects `window.Capacitor` (with its plugins) into the page,
 * so no npm package is needed here. Everything degrades to "plain browser" when the bridge is missing. */

interface CapacitorAppInfo {
  name: string;
  id: string;
  build: string;
  version: string;
}

interface CapacitorGlobal {
  isNativePlatform?: () => boolean;
  getPlatform?: () => string;
  Plugins?: { App?: { getInfo?: () => Promise<CapacitorAppInfo> } };
}

function capacitor(): CapacitorGlobal | undefined {
  if (typeof window === "undefined") return undefined;
  return (window as unknown as { Capacitor?: CapacitorGlobal }).Capacitor;
}

/** Running inside the installed Android app. */
export function isNativeAndroidApp(): boolean {
  const cap = capacitor();
  return Boolean(cap?.isNativePlatform?.() && cap.getPlatform?.() === "android");
}

/** versionCode / versionName of the installed Android app, or null in a browser. */
export async function nativeAppInfo(): Promise<CapacitorAppInfo | null> {
  if (!isNativeAndroidApp()) return null;
  try {
    return (await capacitor()?.Plugins?.App?.getInfo?.()) ?? null;
  } catch {
    return null;
  }
}

/** Opened from the home screen (iOS "Add to Home Screen" or an installed PWA). */
export function isStandalonePwa(): boolean {
  if (typeof window === "undefined") return false;
  const iosStandalone = (navigator as unknown as { standalone?: boolean }).standalone === true;
  return iosStandalone || window.matchMedia?.("(display-mode: standalone)").matches === true;
}
