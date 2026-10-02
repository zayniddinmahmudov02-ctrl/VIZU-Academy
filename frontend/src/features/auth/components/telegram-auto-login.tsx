"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { saveRefreshToken, saveToken } from "@/lib/token";
import { getTelegramInitData, waitForTelegramWebApp } from "@/lib/telegram/webapp";

import { telegramLoginService } from "../services/auth.service";

type Status = "idle" | "checking" | "failed";

/** Auto-login for a Telegram Mini App launch, sitting *beside*
 * LoginForm (see login-card.tsx) — never replacing it.
 *
 * Root cause of the "no request ever reaches /auth/telegram" production
 * bug: this used to check `isTelegramWebApp()` exactly once, synchronously,
 * on mount. The SDK (next/script, strategy="afterInteractive") finishes
 * loading asynchronously on its own schedule — if that single check ran
 * before window.Telegram.WebApp existed yet, it concluded "not Telegram"
 * forever and never looked again, so a real Telegram launch could open
 * this page and simply never attempt login. Fixed by waiting for the SDK
 * (waitForTelegramWebApp(), which resolves immediately if already loaded
 * or once the script's load event fires — see lib/telegram/webapp.ts)
 * instead of checking once and giving up.
 *
 * Outside Telegram — the SDK never loads, or loads but initData is empty
 * (an ordinary browser tab, no real Telegram bridge) — this stays "idle"
 * (renders nothing) forever; the existing manual login/register flow is
 * completely untouched. "failed" is reserved for a *confirmed* Telegram
 * launch (real, non-empty initData) whose backend call then failed, so a
 * plain website visitor never sees a Telegram-specific error banner.
 *
 * StrictMode-safe: `cancelled` (checked before every state update) plus
 * the AbortController passed into waitForTelegramWebApp cover both the
 * dev-only mount -> cleanup -> mount replay and a real unmount — neither
 * can produce a duplicate login request whose result is actually acted
 * on. */
export default function TelegramAutoLogin() {
  const router = useRouter();
  const { t } = useTranslation();
  const [status, setStatus] = useState<Status>("idle");

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;

    waitForTelegramWebApp({ signal: controller.signal })
      .then((webApp) => {
        if (cancelled || !webApp) return;

        const initData = getTelegramInitData();
        if (!initData) return;

        setStatus("checking");

        return telegramLoginService(initData).then((response) => {
          if (cancelled) return;

          // A Mini App launch is a fresh session each time, not a
          // "remember me" choice — same non-persistent storage path
          // saveToken/saveRefreshToken already use for that case.
          saveToken(response.access_token, false);
          saveRefreshToken(response.refresh_token, false);
          router.push("/dashboard");
        });
      })
      .catch(() => {
        if (!cancelled) setStatus("failed");
      });

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [router]);

  if (status === "idle") return null;

  if (status === "checking") {
    return (
      <div className="mb-6 flex items-center justify-center gap-2 rounded-2xl bg-surface-hover px-4 py-3 text-sm text-text-secondary">
        <Loader2 size={15} className="animate-spin" />
        {t("auth.telegramChecking")}
      </div>
    );
  }

  return (
    <div className="mb-6 rounded-2xl bg-warning/10 px-4 py-3 text-center text-sm text-warning">
      {t("auth.telegramFailed")}
    </div>
  );
}
