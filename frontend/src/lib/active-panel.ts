export type ActivePanel = "student" | "teacher" | "admin";

const STORAGE_KEY = "vizu-active-panel";

/** Per-device-only preference (never sent to the backend, never a
 * security boundary — every panel's real gate is its own guard/RBAC
 * dependency) that remembers which panel a multi-role account last
 * chose from the Settings "Panel wechseln" switcher. Its only job is to
 * stop AuthGuard's "SUPER_ADMIN always bounces to /admin" rule from
 * fighting a deliberate switch to the Student Panel — see auth-guard.tsx. */
export function getActivePanel(): ActivePanel | null {
  if (typeof window === "undefined") return null;
  try {
    const value = window.localStorage.getItem(STORAGE_KEY);
    return value === "student" || value === "teacher" || value === "admin" ? value : null;
  } catch {
    return null;
  }
}

export function setActivePanel(panel: ActivePanel): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, panel);
  } catch {
    // Best-effort only — worst case, the next /dashboard visit bounces a
    // SUPER_ADMIN to /admin again, same as before this feature existed.
  }
}
