"use client";

import { Award, ShieldCheck } from "lucide-react";

import Badge from "@/components/ui/badge";
import PageHeader from "@/components/dashboard/page-header";
import { useTranslation } from "@/lib/i18n/use-translation";

export default function CertificatesPage() {
  const { t } = useTranslation();
  const certificates: { title: string; level: string; date: string }[] = [];

  return (
    <div className="space-y-8">
      <PageHeader
        icon={Award}
        titleKey="certificates.title"
        subtitleKey="certificates.subtitle"
        gradient="from-warning to-amber-400"
      />

      {certificates.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-card bg-surface-card px-6 py-16 text-center shadow-[var(--shadow-md)] ring-1 ring-surface-border">
          <Award size={44} className="text-text-muted" />
          <h2 className="mt-4 text-lg font-semibold text-text-primary">{t("certificates.emptyTitle")}</h2>
          <p className="mt-2 max-w-md text-sm text-text-secondary">
            {t("certificates.emptyBody")}
          </p>
        </div>
      ) : (
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {certificates.map((c) => (
            <article
              key={c.title}
              className="rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border"
            >
              <div className="flex items-center gap-2 text-warning">
                <ShieldCheck size={18} />
                <span className="text-xs font-semibold uppercase tracking-wide">{t("certificates.verified")}</span>
              </div>
              <h3 className="mt-3 text-lg font-bold text-text-primary">{c.title}</h3>
              <p className="text-sm text-text-secondary">{c.date}</p>
              <Badge variant="warning" className="mt-4">
                {c.level}
              </Badge>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
