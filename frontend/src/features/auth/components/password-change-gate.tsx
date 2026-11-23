"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { KeyRound, Loader2 } from "lucide-react";

import { changePassword } from "@/features/profile/services/profile-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import { getRefreshToken, removeRefreshToken, removeToken } from "@/lib/token";

import { logoutService } from "../services/auth.service";

const MIN = 8;

function detailOf(error: unknown): string {
  const data = (error as { response?: { data?: { message?: string; detail?: string } } })?.response?.data;
  return String(data?.message ?? data?.detail ?? "");
}

/** Shown instead of the panel while users.must_change_password is set (a teacher account an administrator made in Team):
 * the temporary password must be replaced first. The backend enforces it as well (Teacher Panel: 403 PASSWORD_CHANGE_REQUIRED).
 * A password change ends every session, so the user logs in again with the new password. */
export default function PasswordChangeGate() {
  const { t } = useTranslation();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [repeat, setRepeat] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    if (next.length < MIN) return setError(t("pwgate.short"));
    if (next !== repeat) return setError(t("pwgate.mismatch"));
    if (next === current) return setError(t("pwgate.same"));
    setBusy(true);
    try {
      await changePassword({ currentPassword: current, newPassword: next });
      removeToken();
      removeRefreshToken();
      queryClient.clear();
      setDone(true);
    } catch (err) {
      const code = detailOf(err);
      setError(code === "NEW_PASSWORD_SAME" ? t("pwgate.same") : code.startsWith("Current password") ? t("pwgate.wrong") : t("pwgate.failed"));
    } finally {
      setBusy(false);
    }
  }

  async function logout() {
    const refresh = getRefreshToken();
    removeToken();
    removeRefreshToken();
    queryClient.clear();
    if (refresh) await logoutService(refresh).catch(() => undefined);
    router.replace("/login");
  }

  const input = "w-full rounded-xl border border-surface-border bg-surface-bg px-3 py-2.5 text-sm text-text-primary outline-none focus:border-accent-blue focus:ring-2 focus:ring-accent-blue/20";

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-bg px-4 py-10">
      <div className="w-full max-w-md rounded-3xl bg-surface-card p-6 shadow-[var(--shadow-lg)] ring-1 ring-surface-border sm:p-8" data-testid="password-gate">
        <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-blue/10 text-accent-blue"><KeyRound size={22} /></div>
        <h1 className="text-xl font-bold text-text-primary">{t("pwgate.title")}</h1>
        {done ? (
          <>
            <p className="mt-3 text-sm text-text-secondary" role="status" data-testid="password-gate-done">{t("pwgate.done")}</p>
            <button type="button" onClick={() => router.replace("/login")} className="mt-6 w-full rounded-xl bg-accent-blue px-4 py-2.5 text-sm font-semibold text-white">
              {t("pwgate.toLogin")}
            </button>
          </>
        ) : (
          <form onSubmit={submit} className="mt-3 space-y-4" noValidate>
            <p className="text-sm text-text-secondary">{t("pwgate.text")}</p>
            <label className="block text-sm font-medium text-text-primary">{t("pwgate.current")}
              <input type="password" autoComplete="current-password" value={current} onChange={(e) => setCurrent(e.target.value)} className={`${input} mt-1.5`} data-testid="pw-current" required />
            </label>
            <label className="block text-sm font-medium text-text-primary">{t("pwgate.new")}
              <input type="password" autoComplete="new-password" value={next} onChange={(e) => setNext(e.target.value)} className={`${input} mt-1.5`} data-testid="pw-new" required minLength={MIN} />
            </label>
            <label className="block text-sm font-medium text-text-primary">{t("pwgate.repeat")}
              <input type="password" autoComplete="new-password" value={repeat} onChange={(e) => setRepeat(e.target.value)} className={`${input} mt-1.5`} data-testid="pw-repeat" required />
            </label>
            {error && <p className="text-sm text-danger" role="alert" data-testid="pw-error">{error}</p>}
            <button type="submit" disabled={busy} className="flex w-full items-center justify-center gap-2 rounded-xl bg-accent-blue px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60" data-testid="pw-save">
              {busy && <Loader2 size={16} className="animate-spin" />}{busy ? t("pwgate.saving") : t("pwgate.save")}
            </button>
            <button type="button" onClick={logout} className="w-full text-sm text-text-muted hover:text-text-primary">{t("pwgate.logout")}</button>
          </form>
        )}
      </div>
    </div>
  );
}
