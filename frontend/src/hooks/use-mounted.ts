"use client";

import { useSyncExternalStore } from "react";

const subscribe = () => () => {};

/** True only after the client has hydrated — use to gate rendering that
 *  depends on browser-only state (theme, localStorage) without causing a
 *  server/client mismatch. Replaces the `useEffect(() => setMounted(true))`
 *  anti-pattern flagged by react-hooks/set-state-in-effect. */
export function useHasMounted() {
  return useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  );
}

/** Reads a boolean localStorage flag, defaulting to `false` on the server
 *  and during the first client render, then flipping to the stored value. */
export function useStoredBoolean(key: string) {
  return useSyncExternalStore(
    subscribe,
    () => localStorage.getItem(key) === "1",
    () => false,
  );
}
