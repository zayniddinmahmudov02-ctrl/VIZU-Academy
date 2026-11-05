"use client";

import { useEffect, useState } from "react";
import { Dialog } from "@base-ui/react/dialog";
import { Download } from "lucide-react";

import { apkUrl, getLatestRelease, type AppReleasePublic } from "@/features/mobile-app/services/app-release-service";
import { nativeAppInfo } from "@/features/mobile-app/utils/native";
import { isUpdateAvailable } from "@/features/mobile-app/utils/platform";
import { useTranslation } from "@/lib/i18n/use-translation";

const DISMISS_KEY = "vizu-app-update-dismissed";

/** Inside the installed Android app only: once per app start, compare the installed versionCode with the latest
 * published APK and offer the download. Installing is always the user's choice (Android package installer);
 * nothing is installed silently. Renders nothing in a normal browser or the iOS web app. */
export default function NativeAppUpdate() {
  const { t } = useTranslation();
  const [state, setState] = useState<{ release: AppReleasePublic; current: string } | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const info = await nativeAppInfo();
      if (!info) return;
      let release: AppReleasePublic | null = null;
      try {
        release = await getLatestRelease();
      } catch {
        return; // offline or server error: try again next start
      }
      if (!release || !isUpdateAvailable(info.build, release.version_code)) return;
      try {
        if (sessionStorage.getItem(DISMISS_KEY) === String(release.version_code)) return;
      } catch {
        // storage blocked: just show the prompt
      }
      if (!cancelled) setState({ release, current: info.version });
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  function later() {
    if (state) {
      try {
        sessionStorage.setItem(DISMISS_KEY, String(state.release.version_code));
      } catch {
        // ignore
      }
    }
    setState(null);
  }

  if (!state) return null;
  return (
    <Dialog.Root open onOpenChange={(open) => !open && later()}>
      <Dialog.Portal>
        <Dialog.Backdrop className="fixed inset-0 z-[70] bg-black/60" />
        <Dialog.Popup data-testid="app-update-prompt"
                      className="safe-bottom fixed inset-x-0 bottom-0 z-[70] rounded-t-3xl bg-[#0e1834] p-5 text-white outline-none ring-1 ring-white/10">
          <Dialog.Title className="text-lg font-bold">{t("mobileApp.updateTitle")}</Dialog.Title>
          <p className="mt-1 text-sm text-white/80">{t("mobileApp.updateBody", { latest: state.release.version_name, current: state.current })}</p>
          {state.release.release_notes && (
            <div className="mt-3 max-h-40 overflow-y-auto rounded-2xl bg-white/5 p-3 text-sm ring-1 ring-white/10">
              <p className="mb-1 font-semibold">{t("mobileApp.whatsNew")}</p>
              <p className="whitespace-pre-line text-white/75">{state.release.release_notes}</p>
            </div>
          )}
          <p className="mt-3 text-xs text-white/60">{t("mobileApp.updateHint")}</p>
          <div className="mt-4 flex gap-3">
            <button type="button" onClick={later} className="min-h-12 flex-1 rounded-2xl bg-white/10 font-semibold hover:bg-white/20">
              {t("mobileApp.updateLater")}
            </button>
            <a href={apkUrl(state.release)} onClick={later}
               className="inline-flex min-h-12 flex-[2] items-center justify-center rounded-2xl bg-[#3ddc84]">
              <span className="inline-flex items-center gap-2 font-extrabold text-[#05230f]">
                <Download size={18} aria-hidden="true" /> {t("mobileApp.updateCta")}
              </span>
            </a>
          </div>
        </Dialog.Popup>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
