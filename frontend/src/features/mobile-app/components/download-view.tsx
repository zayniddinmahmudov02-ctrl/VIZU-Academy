"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle2, Download, ShieldCheck, Smartphone } from "lucide-react";

import Logo from "@/components/common/logo";
import LanguageSwitcher from "@/components/dashboard/languages/language-switcher";
import IosInstallGuide from "@/features/mobile-app/components/ios-install-guide";
import { usePlatform, useRunsAsApp } from "@/features/mobile-app/hooks/use-device";
import { apkUrl, downloadQrUrl, getLatestRelease, type AppReleasePublic } from "@/features/mobile-app/services/app-release-service";
import { formatBytes, groupChecksum } from "@/features/mobile-app/utils/platform";
import { useTranslation } from "@/lib/i18n/use-translation";

function AppleGlyph({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className={className} fill="currentColor">
      <path d="M16.37 12.62c-.02-2.2 1.8-3.26 1.88-3.31-1.03-1.5-2.62-1.7-3.18-1.73-1.35-.14-2.64.8-3.33.8-.69 0-1.74-.78-2.87-.76-1.47.02-2.83.86-3.59 2.18-1.53 2.66-.39 6.6 1.1 8.76.73 1.06 1.59 2.24 2.72 2.2 1.1-.04 1.51-.7 2.83-.7 1.32 0 1.7.7 2.86.68 1.18-.02 1.93-1.07 2.65-2.13.84-1.22 1.18-2.41 1.2-2.47-.03-.01-2.3-.88-2.32-3.52zM14.2 6.16c.6-.73 1.01-1.75.9-2.76-.87.03-1.92.58-2.54 1.31-.56.65-1.05 1.68-.92 2.67.97.08 1.96-.49 2.56-1.22z" />
    </svg>
  );
}

function AndroidGlyph({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className={className} fill="currentColor">
      <path d="M17.6 9.48l1.84-3.18a.38.38 0 00-.65-.38l-1.86 3.22a11.4 11.4 0 00-9.86 0L5.21 5.92a.38.38 0 10-.65.38L6.4 9.48A10.8 10.8 0 001 18h22a10.8 10.8 0 00-5.4-8.52zM7 15.25a1.25 1.25 0 110-2.5 1.25 1.25 0 010 2.5zm10 0a1.25 1.25 0 110-2.5 1.25 1.25 0 010 2.5z" />
    </svg>
  );
}

/** A stylised phone showing the dashboard (decorative). */
function PhoneMockup({ variant }: { variant: "android" | "ios" }) {
  return (
    <div aria-hidden="true"
         className={`relative w-[132px] shrink-0 rounded-[28px] bg-[#05080f] p-[6px] shadow-[0_30px_60px_-20px_rgba(0,0,0,0.8)] ring-1 ring-white/15 sm:w-[156px] ${variant === "ios" ? "translate-y-6" : ""}`}>
      <div className="relative aspect-[9/19] overflow-hidden rounded-[22px] bg-[#0e1834]">
        {variant === "ios"
          ? <div className="absolute left-1/2 top-1.5 z-10 h-3.5 w-12 -translate-x-1/2 rounded-full bg-black" />
          : <div className="absolute left-1/2 top-2 z-10 h-2 w-2 -translate-x-1/2 rounded-full bg-black" />}
        <div className="flex h-full flex-col gap-1.5 p-2 pt-7">
          <div className="flex items-center gap-1">
            <div className="h-4 w-4 rounded-md bg-[#d4af37]/80" />
            <div className="h-1.5 w-14 rounded bg-white/70" />
          </div>
          <div className="grid grid-cols-2 gap-1">
            <div className="h-10 rounded-lg bg-gradient-to-br from-[#172a46] to-[#3984e8] ring-1 ring-[#d4af37]/50" />
            <div className="h-10 rounded-lg bg-gradient-to-br from-blue-600 to-blue-400" />
            <div className="h-10 rounded-lg bg-gradient-to-br from-emerald-600 to-emerald-400" />
            <div className="h-10 rounded-lg bg-gradient-to-br from-purple-600 to-purple-400" />
          </div>
          <div className="h-1.5 w-12 rounded bg-white/50" />
          <div className="grid grid-cols-3 gap-1">
            {["A1", "A2", "B1"].map((l) => (
              <div key={l} className="grid h-9 place-items-center rounded-md bg-white/10 text-[9px] font-bold text-white/80">{l}</div>
            ))}
          </div>
          <div className="mt-auto flex h-1 overflow-hidden rounded-full"><i className="flex-1 bg-black" /><i className="flex-1 bg-[#dd0000]" /><i className="flex-1 bg-[#ffce00]" /></div>
        </div>
      </div>
    </div>
  );
}

function Fact({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex min-w-0 flex-col gap-0.5">
      <dt className="text-[11px] font-semibold uppercase tracking-wide text-white/50">{label}</dt>
      <dd className={`min-w-0 break-words text-sm text-white ${mono ? "font-mono text-xs leading-relaxed" : "font-semibold"}`}>{value}</dd>
    </div>
  );
}

function AndroidCard({ release, loading, error, primary }: { release: AppReleasePublic | null | undefined; loading: boolean; error: boolean; primary: boolean }) {
  const { t, language } = useTranslation();
  const locale = language === "uz" ? "uz-UZ" : "de-DE";

  return (
    <section data-testid="download-android" aria-labelledby="android-title"
             className={`flex min-w-0 flex-col gap-4 rounded-3xl bg-white/[0.06] p-5 ring-1 backdrop-blur sm:p-6 ${primary ? "ring-[#3ddc84]/50" : "ring-white/10"}`}>
      <div className="flex items-center gap-3">
        <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-[#3ddc84]/15 text-[#3ddc84]"><AndroidGlyph className="h-7 w-7" /></span>
        <div className="min-w-0">
          <h2 id="android-title" className="text-lg font-bold leading-tight">{t("mobileApp.androidTitle")}</h2>
          <p className="mt-0.5 text-sm text-white/75">{t("mobileApp.androidBody")}</p>
        </div>
      </div>

      {loading ? (
        <div className="h-12 animate-pulse rounded-2xl bg-white/10" />
      ) : release ? (
        <>
          <a href={apkUrl(release)} data-testid="download-apk" download
             className="inline-flex min-h-12 w-full items-center justify-center rounded-2xl bg-[#3ddc84] px-5 shadow-[0_12px_30px_-12px_rgba(61,220,132,0.7)] transition-transform hover:-translate-y-0.5 active:translate-y-0">
            {/* colour on the child: globals.css `a { color: inherit }` beats utilities on the <a> */}
            <span className="inline-flex items-center gap-2 text-base font-extrabold tracking-wide text-[#05230f]">
              <Download size={20} aria-hidden="true" /> {t("mobileApp.androidCta")}
            </span>
          </a>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-3" data-testid="download-android-facts">
            <Fact label={t("mobileApp.version")} value={release.version_name} />
            <Fact label={t("mobileApp.fileSize")} value={formatBytes(release.size_bytes)} />
            <Fact label={t("mobileApp.releaseDate")} value={release.published_at ? new Date(release.published_at).toLocaleDateString(locale, { dateStyle: "medium" }) : "—"} />
            <Fact label={t("mobileApp.minAndroid")} value={t("mobileApp.minAndroidValue", { v: release.min_android_version })} />
            <div className="col-span-2"><Fact label={t("mobileApp.checksum")} value={groupChecksum(release.sha256)} mono /></div>
          </dl>
          {release.release_notes && (
            <div className="rounded-2xl bg-black/20 p-4 text-sm ring-1 ring-white/10">
              <p className="mb-1 font-semibold">{t("mobileApp.whatsNew")}</p>
              <p className="whitespace-pre-line text-white/75">{release.release_notes}</p>
            </div>
          )}
        </>
      ) : (
        <div data-testid="download-android-soon">
          <span aria-disabled="true" className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl bg-white/10 px-5 text-base font-bold text-white/60">
            {t("mobileApp.androidSoonCta")}
          </span>
          <p className="mt-2 text-sm text-white/60">{error ? t("dashboard.loadError") : t("mobileApp.androidSoon")}</p>
        </div>
      )}

      <div className="rounded-2xl bg-black/20 p-4 ring-1 ring-white/10">
        <p className="mb-2 text-sm font-semibold">{t("mobileApp.androidStepsTitle")}</p>
        <ol className="list-decimal space-y-1 pl-5 text-sm text-white/75">
          <li>{t("mobileApp.androidStep1")}</li>
          <li>{t("mobileApp.androidStep2")}</li>
          <li>{t("mobileApp.androidStep3")}</li>
          <li>{t("mobileApp.androidStep4")}</li>
        </ol>
        <p className="mt-3 flex gap-2 text-xs leading-relaxed text-white/60">
          <ShieldCheck size={16} aria-hidden="true" className="shrink-0 text-[#3ddc84]" /> {t("mobileApp.androidSafety")}
        </p>
      </div>
    </section>
  );
}

function IosCard({ onInstall, primary }: { onInstall: () => void; primary: boolean }) {
  const { t } = useTranslation();
  return (
    <section data-testid="download-ios" aria-labelledby="ios-title"
             className={`flex min-w-0 flex-col gap-4 rounded-3xl bg-white/[0.06] p-5 ring-1 backdrop-blur sm:p-6 ${primary ? "ring-[#3984e8]/60" : "ring-white/10"}`}>
      <div className="flex items-center gap-3">
        <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-white/10 text-white"><AppleGlyph className="h-7 w-7" /></span>
        <div className="min-w-0">
          <h2 id="ios-title" className="text-lg font-bold leading-tight">{t("mobileApp.iosTitle")}</h2>
          <p className="mt-0.5 text-sm text-white/75">{t("mobileApp.iosBody")}</p>
        </div>
      </div>
      <button type="button" onClick={onInstall} data-testid="ios-install"
              className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl bg-[#3984e8] px-5 text-base font-extrabold tracking-wide text-white shadow-[0_12px_30px_-12px_rgba(57,132,232,0.8)] transition-transform hover:-translate-y-0.5 active:translate-y-0">
        <Smartphone size={20} aria-hidden="true" /> {t("mobileApp.iosCta")}
      </button>
      <p className="text-sm text-white/60">{t("mobileApp.iosNote")}</p>
    </section>
  );
}

export default function DownloadView() {
  const { t } = useTranslation();
  // navigator is only known in the browser: null / false while server-rendering, then the real device
  const platform = usePlatform();
  const installed = useRunsAsApp();
  const [guideOpen, setGuideOpen] = useState(false);
  const { data: release, isLoading, isError } = useQuery({ queryKey: ["app-release-latest"], queryFn: getLatestRelease, staleTime: 5 * 60_000 });

  const os = platform?.os ?? "desktop";
  const android = <AndroidCard key="a" release={release} loading={isLoading} error={isError} primary={os === "android"} />;
  const ios = <IosCard key="i" onInstall={() => setGuideOpen(true)} primary={os === "ios"} />;

  return (
    <main className="relative min-h-dvh overflow-x-hidden bg-[#0a1226] text-white" data-testid="download-page">
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 -z-0">
        <picture>
          <source media="(max-width: 767px)" srcSet="/battle/themes/berlin-mobile.webp" />
          <img src="/battle/themes/berlin-desktop.webp" alt="" decoding="async" className="h-[560px] w-full object-cover object-[50%_35%] opacity-40" />
        </picture>
        <div className="absolute inset-x-0 top-0 h-[560px] bg-gradient-to-b from-[#0a1226]/40 via-[#0a1226]/80 to-[#0a1226]" />
      </div>

      <div className="safe-top relative mx-auto flex max-w-5xl flex-col gap-8 px-4 pb-16 pt-5 sm:px-6">
        <header className="flex items-center justify-between gap-3">
          <Link href="/" prefetch={false} className="inline-flex min-h-10 items-center gap-2 rounded-xl px-2 text-sm font-semibold text-white/80 hover:text-white">
            <ArrowLeft size={16} aria-hidden="true" /> {t("mobileApp.backHome")}
          </Link>
          <LanguageSwitcher />
        </header>

        <section className="flex flex-col items-center gap-8 text-center md:flex-row md:items-center md:text-left">
          <div className="flex min-w-0 flex-1 flex-col items-center gap-4 md:items-start">
            <Logo size={64} showText={false} />
            <h1 className="text-3xl font-black tracking-tight sm:text-5xl">
              VIZU <span className="text-[#3984e8]">DEUTSCH</span> <span className="text-[#d4af37]">APP</span>
            </h1>
            <div aria-hidden="true" className="flex h-1.5 w-24 overflow-hidden rounded-full"><i className="flex-1 bg-black" /><i className="flex-1 bg-[#dd0000]" /><i className="flex-1 bg-[#ffce00]" /></div>
            <p className="text-xl font-bold text-white sm:text-2xl" data-testid="download-slogan">{t("mobileApp.slogan")}</p>
            <p className="max-w-md text-sm leading-relaxed text-white/75 sm:text-base">{t("mobileApp.intro")}</p>
            {installed && (
              <p className="inline-flex items-center gap-2 rounded-full bg-[#3ddc84]/15 px-3 py-1.5 text-sm font-semibold text-[#3ddc84]" data-testid="download-installed">
                <CheckCircle2 size={16} aria-hidden="true" /> {t("mobileApp.alreadyInstalled")}
              </p>
            )}
          </div>
          <div className="flex items-start justify-center gap-4">
            <PhoneMockup variant="android" />
            <PhoneMockup variant="ios" />
          </div>
        </section>

        <div className="grid gap-5 md:grid-cols-2">{os === "ios" ? [ios, android] : [android, ios]}</div>

        {os === "desktop" && (
          <section data-testid="download-qr" aria-labelledby="qr-title"
                   className="flex flex-col items-center gap-5 rounded-3xl bg-white/[0.06] p-6 text-center ring-1 ring-white/10 sm:flex-row sm:text-left">
            {/* eslint-disable-next-line @next/next/no-img-element -- server-generated SVG from the API origin */}
            <img src={downloadQrUrl()} alt={t("mobileApp.qrAlt")} width={160} height={160} className="h-40 w-40 shrink-0 rounded-2xl bg-white p-2" />
            <div className="min-w-0">
              <h2 id="qr-title" className="text-lg font-bold">{t("mobileApp.desktopTitle")}</h2>
              <p className="mt-1 text-sm text-white/75">{t("mobileApp.desktopBody")}</p>
              <p className="mt-2 font-mono text-sm text-[#3984e8]">vizu-deutsch.com/download</p>
            </div>
          </section>
        )}
      </div>

      <IosInstallGuide open={guideOpen} onOpenChange={setGuideOpen} iosBrowser={platform?.iosBrowser ?? null} inAppBrowser={platform?.inAppBrowser ?? false} />
    </main>
  );
}
