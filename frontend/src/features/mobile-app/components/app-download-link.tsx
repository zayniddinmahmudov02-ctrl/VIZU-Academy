"use client";

import Link from "next/link";
import { Smartphone } from "lucide-react";

import { useRunsAsApp } from "@/features/mobile-app/hooks/use-device";
import { useTranslation } from "@/lib/i18n/use-translation";

/** "App herunterladen" entry point to /download; hidden when already running as the app. */
export default function AppDownloadLink({ className = "" }: { className?: string }) {
  const { t } = useTranslation();
  const runsAsApp = useRunsAsApp();

  if (runsAsApp) return null;
  return (
    <Link href="/download" prefetch={false} data-testid="app-download-link"
          className={`inline-flex min-h-10 items-center rounded-xl px-4 ring-1 ring-accent-blue/30 transition-colors hover:bg-accent-blue/10 ${className}`}>
      {/* colour on the child: globals.css `a { color: inherit }` beats utilities on the <a> */}
      <span className="inline-flex items-center gap-2 text-sm font-semibold text-accent-blue">
        <Smartphone size={16} aria-hidden="true" /> {t("mobileApp.getTheApp")}
      </span>
    </Link>
  );
}
