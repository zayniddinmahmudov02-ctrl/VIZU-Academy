"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Award } from "lucide-react";

import { getMyCertificates } from "@/features/certificates/services/my-certificates-service";
import { useTranslation } from "@/lib/i18n/use-translation";

/** "Zertifikate": how many certificates THIS student has (GET /my-certificates,
 * own rows only) — 0 shows the encouragement text in the active language. */
export default function CertificatesCard() {
  const { t } = useTranslation();
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ["my-certificates"], queryFn: getMyCertificates, staleTime: 60_000 });
  const count = data?.length ?? 0;

  return (
    <section className="flex h-full flex-col rounded-card bg-surface-card p-5 shadow-[var(--shadow-card)] ring-1 ring-surface-border" aria-labelledby="cert-title" data-testid="dashboard-certificates">
      <div className="flex items-center gap-2">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent-gold/15 text-accent-gold"><Award size={18} aria-hidden="true" /></span>
        <h2 id="cert-title" className="font-bold text-text-primary">{t("dashboard.certTitle")}</h2>
      </div>

      {isLoading ? (
        <div className="mt-4 h-24 animate-pulse rounded-xl bg-surface-hover" aria-busy="true" aria-label={t("dashboard.loading")} />
      ) : isError ? (
        <p className="mt-4 text-sm text-text-secondary">
          {t("dashboard.loadError")}{" "}
          <button type="button" onClick={() => refetch()} className="font-semibold text-accent-blue hover:underline">{t("dashboard.retry")}</button>
        </p>
      ) : count === 0 ? (
        <div className="mt-4 flex flex-1 flex-col items-center justify-center gap-2 text-center" data-testid="certificates-empty">
          <span className="text-4xl" aria-hidden="true">😔</span>
          <p className="text-sm text-text-secondary">{t("dashboard.certEmpty")}</p>
        </div>
      ) : (
        <div className="mt-4 flex flex-1 flex-col gap-4">
          <p className="text-3xl font-extrabold text-text-primary" data-testid="certificates-count">
            {count === 1 ? t("dashboard.certCountOne") : t("dashboard.certCount", { n: count })}
          </p>
          <Link href="/certificates" prefetch={false}
                className="mt-auto inline-flex w-fit items-center gap-1.5 rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white hover:opacity-90">
            {t("dashboard.certView")} <ArrowRight size={14} aria-hidden="true" />
          </Link>
        </div>
      )}
    </section>
  );
}
