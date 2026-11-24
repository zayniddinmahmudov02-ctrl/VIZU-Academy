"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle2, Smartphone, Wifi } from "lucide-react";

import { LogoMark } from "@/components/common/logo";
import LanguageSwitcher from "@/components/dashboard/languages/language-switcher";
import { useRunsAsApp } from "@/features/mobile-app/hooks/use-device";
import { getLatestRelease } from "@/features/mobile-app/services/app-release-service";
import { translate, useTranslation } from "@/lib/i18n/use-translation";

import { ANDROID_STEPS, AndroidCard } from "./download-view";

/** The guide in both languages side by side (always German AND Uzbek, whatever the page language is). */
function Guide({ language }: { language: "de" | "uz" }) {
  return (
    <section className="min-w-0 rounded-3xl bg-white/[0.06] p-5 ring-1 ring-white/10 sm:p-6" data-testid={`android-guide-${language}`} lang={language}>
      <h2 className="text-base font-bold">{translate(language, language === "de" ? "mobileApp.guideDe" : "mobileApp.guideUz")}</h2>
      <ol className="mt-3 list-decimal space-y-1.5 pl-5 text-sm text-white/80">
        {ANDROID_STEPS.map((k) => <li key={k}>{translate(language, `mobileApp.${k}`)}</li>)}
      </ol>
      <p className="mt-3 text-xs leading-relaxed text-white/60">{translate(language, "mobileApp.androidSafety")}</p>
    </section>
  );
}

/** /download/android: the Android app only — icon, short description, version, size, date, compatibility, the APK button
 * (only when a published release exists: otherwise "Bald verfügbar", never a dead button) and the install guide. */
export default function AndroidDownloadView() {
  const { t } = useTranslation();
  const installed = useRunsAsApp();
  const { data: release, isLoading, isError } = useQuery({ queryKey: ["app-release-latest"], queryFn: getLatestRelease, staleTime: 5 * 60_000 });

  return (
    <main className="relative min-h-dvh overflow-x-hidden bg-[#0a1226] text-white" data-testid="android-download-page">
      <div aria-hidden="true" className="pointer-events-none absolute inset-x-0 top-0 h-[420px] bg-gradient-to-b from-[#12306e]/60 via-[#0a1226]/90 to-[#0a1226]" />
      <div className="safe-top relative mx-auto flex max-w-4xl flex-col gap-7 px-4 pb-16 pt-5 sm:px-6">
        <header className="flex items-center justify-between gap-3">
          <Link href="/download" prefetch={false} className="inline-flex min-h-10 items-center gap-2 rounded-xl px-2 text-sm font-semibold text-white/80 hover:text-white">
            <ArrowLeft size={16} aria-hidden="true" /> {t("mobileApp.pageTitle")}
          </Link>
          <LanguageSwitcher />
        </header>

        <section className="flex flex-col items-center gap-4 text-center sm:flex-row sm:items-center sm:text-left">
          {/* the official logo = the launcher icon of the app (the image is already the icon tile, no extra frame) */}
          <span className="shrink-0" data-testid="android-app-icon">
            <LogoMark size={96} />
          </span>
          <div className="min-w-0">
            <h1 className="text-3xl font-black tracking-tight sm:text-4xl" data-testid="android-page-title">{t("mobileApp.androidPageTitle")}</h1>
            <p className="mt-2 max-w-xl text-sm leading-relaxed text-white/75 sm:text-base">{t("mobileApp.androidPageIntro")}</p>
            <p className="mt-2 inline-flex items-center gap-2 text-xs text-white/60"><Wifi size={14} aria-hidden="true" /> {t("mobileApp.androidPageOnline")}</p>
            {installed && (
              <p className="mt-3 inline-flex items-center gap-2 rounded-full bg-[#3ddc84]/15 px-3 py-1.5 text-sm font-semibold text-[#3ddc84]">
                <CheckCircle2 size={16} aria-hidden="true" /> {t("mobileApp.alreadyInstalled")}
              </p>
            )}
          </div>
        </section>

        <AndroidCard release={release} loading={isLoading} error={isError} primary />

        <div className="grid gap-4 md:grid-cols-2">
          <Guide language="de" />
          <Guide language="uz" />
        </div>

        <Link href="/download" prefetch={false} className="inline-flex items-center gap-2 self-start rounded-xl px-2 py-1 text-sm text-white/70 underline-offset-4 hover:text-white hover:underline">
          <Smartphone size={16} aria-hidden="true" /> {t("mobileApp.iphoneHint")}
        </Link>
      </div>
    </main>
  );
}
