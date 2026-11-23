"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { decideBack, homeOf } from "@/features/mobile-app/utils/back-button";
import { isNativeAndroidApp } from "@/features/mobile-app/utils/native";
import { useTranslation } from "@/lib/i18n/use-translation";

interface Listener {
  remove: () => Promise<void> | void;
}

interface AppPlugin {
  addListener?: (event: "backButton", cb: (e: { canGoBack: boolean }) => void) => Promise<Listener> | Listener;
  exitApp?: () => Promise<void>;
}

function appPlugin(): AppPlugin | null {
  return (window as unknown as { Capacitor?: { Plugins?: { App?: AppPlugin } } }).Capacitor?.Plugins?.App ?? null;
}

/** An open modal of the page (base-ui dialogs, drawers, sheets): role dialog / alertdialog that is not hidden. */
function openDialog(): HTMLElement | null {
  const all = Array.from(document.querySelectorAll<HTMLElement>('[role="dialog"], [role="alertdialog"]'));
  return all.reverse().find((el) => el.getAttribute("aria-hidden") !== "true" && !el.hidden && el.getClientRects().length > 0) ?? null;
}

/** Android app only: the back button closes an open dialog first, then goes back; on a start page (Dashboard, Lehrer-Panel,
 * Admin, Login) the first press shows "press again to close", the second one closes the app. Renders nothing elsewhere. */
export default function NativeBackButton() {
  const { t } = useTranslation();
  const router = useRouter();
  const lastHint = useRef<number | null>(null);
  const [hint, setHint] = useState(false);

  useEffect(() => {
    if (!isNativeAndroidApp()) return;
    const app = appPlugin();
    if (!app?.addListener) return;
    let handle: Listener | null = null;
    let hideTimer = 0;
    const onBack = ({ canGoBack }: { canGoBack: boolean }) => {
      const dialog = openDialog();
      const decision = decideBack({ dialogOpen: !!dialog, path: window.location.pathname, canGoBack: canGoBack || window.history.length > 1,
                                    now: Date.now(), lastHintAt: lastHint.current });
      if (decision === "close-dialog") {
        const target = dialog ?? document.body;
        target.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", code: "Escape", bubbles: true }));
      } else if (decision === "history-back") {
        window.history.back();
      } else if (decision === "home") {
        router.replace(homeOf(window.location.pathname));
      } else if (decision === "exit-hint") {
        lastHint.current = Date.now();
        setHint(true);
        window.clearTimeout(hideTimer);
        hideTimer = window.setTimeout(() => setHint(false), 2000);
      } else {
        void app.exitApp?.();
      }
    };
    Promise.resolve(app.addListener("backButton", onBack)).then((h) => { handle = h; }).catch(() => undefined);
    return () => {
      window.clearTimeout(hideTimer);
      void handle?.remove();
    };
  }, [router]);

  if (!hint) return null;
  return (
    <div role="status" data-testid="back-exit-hint"
         className="pointer-events-none fixed inset-x-0 bottom-24 z-[80] mx-auto w-fit rounded-full bg-[#0e1834]/95 px-4 py-2 text-sm font-medium text-white shadow-lg ring-1 ring-[#d4af37]/40">
      {t("mobileApp.backAgainToExit")}
    </div>
  );
}
