"use client";

import { useState } from "react";
import { Dialog } from "@base-ui/react/dialog";
import { Check, Copy, PlusSquare, Share, X } from "lucide-react";

import type { IosBrowser } from "@/features/mobile-app/utils/platform";
import { useTranslation } from "@/lib/i18n/use-translation";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  iosBrowser: IosBrowser;
  inAppBrowser: boolean;
};

const SITE = "https://vizu-deutsch.com";

/** Step-by-step "Add to Home Screen" guide for iPhone / iPad (Safari only can install a web app). */
export default function IosInstallGuide({ open, onOpenChange, iosBrowser, inAppBrowser }: Props) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  const notSafari = iosBrowser !== null && iosBrowser !== "safari";

  async function copy() {
    try {
      await navigator.clipboard.writeText(SITE);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  const steps = [
    { text: t("mobileApp.guideStep1") },
    { text: t("mobileApp.guideStep2"), icon: Share },
    { text: t("mobileApp.guideStep3"), icon: PlusSquare },
    { text: t("mobileApp.guideStep4") },
    { text: t("mobileApp.guideStep5") },
  ];

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Backdrop className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm" />
        <Dialog.Popup
          data-testid="ios-guide"
          className="safe-bottom fixed inset-x-0 bottom-0 z-50 max-h-[90dvh] overflow-y-auto rounded-t-3xl bg-[#0e1834] p-5 text-white shadow-2xl outline-none ring-1 ring-white/10 sm:inset-x-auto sm:bottom-auto sm:left-1/2 sm:top-1/2 sm:w-[440px] sm:-translate-x-1/2 sm:-translate-y-1/2 sm:rounded-3xl"
        >
          <div className="flex items-start justify-between gap-3">
            <Dialog.Title className="text-lg font-bold">{t("mobileApp.guideTitle")}</Dialog.Title>
            <Dialog.Close aria-label={t("mobileApp.close")} className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-white/10 hover:bg-white/20">
              <X size={18} aria-hidden="true" />
            </Dialog.Close>
          </div>

          {notSafari && (
            <div className="mt-4 rounded-2xl bg-[#d4af37]/15 p-4 text-sm leading-relaxed text-[#f5dd8a] ring-1 ring-[#d4af37]/40" data-testid="ios-guide-not-safari">
              <p>{inAppBrowser ? t("mobileApp.guideInApp") : t("mobileApp.guideNotSafari")}</p>
              <button type="button" onClick={copy}
                      className="mt-3 inline-flex min-h-10 items-center gap-2 rounded-xl bg-white/10 px-3 text-sm font-semibold text-white hover:bg-white/20">
                {copied ? <Check size={16} aria-hidden="true" /> : <Copy size={16} aria-hidden="true" />}
                {copied ? t("mobileApp.linkCopied") : t("mobileApp.copyLink")}
              </button>
            </div>
          )}

          <ol className="mt-4 space-y-3">
            {steps.map((s, i) => (
              <li key={i} className="flex items-center gap-3 rounded-2xl bg-white/5 p-3 ring-1 ring-white/10">
                <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[#3984e8] text-sm font-bold">{i + 1}</span>
                <span className="min-w-0 flex-1 text-sm leading-snug">{s.text}</span>
                {s.icon && <s.icon size={20} aria-hidden="true" className="shrink-0 text-[#3984e8]" />}
              </li>
            ))}
          </ol>

          <div className="mt-4 rounded-2xl bg-white/5 p-4 text-xs leading-relaxed text-white/70 ring-1 ring-white/10">
            <p className="mb-1 font-semibold text-white/90">{t("mobileApp.iosLimitsTitle")}</p>
            <p>{t("mobileApp.iosLimits")}</p>
          </div>
        </Dialog.Popup>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
