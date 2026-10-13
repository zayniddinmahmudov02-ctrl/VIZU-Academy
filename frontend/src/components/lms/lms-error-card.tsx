"use client";

import Link from "next/link";
import { AlertTriangle, Lock, RotateCcw } from "lucide-react";

import { describeLmsError } from "@/features/lms/errors";
import { useTranslation } from "@/lib/i18n/use-translation";

/** A failed LMS request, explained: 401 / 403 (Premium or locked) / 404 /
 * 5xx each have their own text; retry only where it can help. The request
 * id (X-Request-ID) is shown for support. */
export default function LmsErrorCard({ error, onRetry, backHref, backLabelKey }: {
  error: unknown;
  onRetry?: () => void;
  backHref?: string;
  backLabelKey?: string;
}) {
  const { t } = useTranslation();
  const info = describeLmsError(error);
  const Icon = info.status === 403 ? Lock : AlertTriangle;

  return (
    <div role="alert" data-testid="lms-error" data-status={info.status ?? "network"}
         className="mx-auto flex max-w-lg flex-col items-center gap-3 rounded-card bg-surface-card p-8 text-center shadow-[var(--shadow-md)] ring-1 ring-surface-border">
      <div className={`flex h-12 w-12 items-center justify-center rounded-2xl ${info.status === 403 ? "bg-warning/15 text-warning" : "bg-danger/10 text-danger"}`}>
        <Icon size={22} />
      </div>
      <p className="text-lg font-semibold text-text-primary">{t(info.titleKey)}</p>
      <p className="text-sm text-text-secondary">{t(info.hintKey)}</p>
      <div className="mt-2 flex flex-wrap justify-center gap-2">
        {info.premium && (
          <Link href="/angebote" className="rounded-xl bg-accent-blue px-5 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90">
            {t("lms.toAngebote")}
          </Link>
        )}
        {info.retry && onRetry && (
          <button type="button" onClick={onRetry}
                  className="inline-flex items-center gap-2 rounded-xl bg-surface-hover px-5 py-2.5 text-sm font-semibold text-text-primary ring-1 ring-surface-border hover:text-accent-blue">
            <RotateCcw size={15} /> {t("lms.retry")}
          </button>
        )}
        {backHref && (
          <Link href={backHref} className="rounded-xl px-5 py-2.5 text-sm font-semibold text-text-secondary ring-1 ring-surface-border hover:text-accent-blue">
            {t(backLabelKey ?? "lms.back")}
          </Link>
        )}
      </div>
      {info.requestId && <p className="mt-1 text-[11px] text-text-muted">Request-ID: {info.requestId}</p>}
    </div>
  );
}
