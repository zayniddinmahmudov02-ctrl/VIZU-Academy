"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { saveRefreshToken, saveToken } from "@/lib/token";
import { getTelegramInitData, isTelegramWebApp } from "@/lib/telegram/webapp";

import { telegramLoginService } from "../services/auth.service";

type Status = "idle" | "checking" | "failed";

/** Auto-login for a Telegram Mini App launch, sitting *beside*
 * LoginForm (see login-card.tsx) — never replacing it. Outside
 * Telegram, isTelegramWebApp() is false and this renders nothing at
 * all; the existing manual login/register flow is completely
 * untouched, hook order and all (fixed useState/useEffect calls, no
 * branch runs before them).
 *
 * On success: same saveToken/saveRefreshToken this app's own login
 * already uses, then a plain redirect to /dashboard — deliberately
 * NOT role-branching here. A SUPER_ADMIN account is bounced from
 * /dashboard to /admin by AuthGuard's own existing check
 * (components/auth/auth-guard.tsx), exactly like visiting /dashboard
 * directly after any other login already behaves; this component
 * doesn't need to (and shouldn't) reimplement that.
 *
 * On failure (not in Telegram, no initData, invalid/expired signature,
 * network error): shows a small non-blocking notice and stops — it
 * never hides or disables the form underneath, so manual login always
 * keeps working. */
export default function TelegramAutoLogin() {
  const router = useRouter();
  const [status, setStatus] = useState<Status>("idle");

  useEffect(() => {
    if (!isTelegramWebApp()) return;

    const initData = getTelegramInitData();
    if (!initData) {
      setStatus("failed");
      return;
    }

    setStatus("checking");

    telegramLoginService(initData)
      .then((response) => {
        // A Mini App launch is a fresh session each time, not a
        // "remember me" choice — same non-persistent storage path
        // saveToken/saveRefreshToken already use for that case.
        saveToken(response.access_token, false);
        saveRefreshToken(response.refresh_token, false);
        router.push("/dashboard");
      })
      .catch(() => {
        setStatus("failed");
      });
  }, [router]);

  if (status === "idle") return null;

  if (status === "checking") {
    return (
      <div className="mb-6 flex items-center justify-center gap-2 rounded-2xl bg-surface-hover px-4 py-3 text-sm text-text-secondary">
        <Loader2 size={15} className="animate-spin" />
        Telegram-Authentifizierung läuft...
      </div>
    );
  }

  return (
    <div className="mb-6 rounded-2xl bg-warning/10 px-4 py-3 text-center text-sm text-warning">
      Telegram-Anmeldung nicht möglich. Bitte melde dich unten manuell an.
    </div>
  );
}
