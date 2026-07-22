"use client";

import { Mail, MapPin, Sparkles, User } from "lucide-react";

import Avatar from "@/components/ui/avatar";
import PageHeader from "@/components/dashboard/page-header";
import { useTranslation } from "@/lib/i18n/use-translation";

export default function ProfilePage() {
  const { t } = useTranslation();

  return (
    <div className="space-y-8">
      <PageHeader
        icon={User}
        titleKey="sidebar.profile"
        subtitleKey="profile.pageSubtitle"
        gradient="from-brand-900 to-accent-blue"
      />

      {/* Header card */}
      <section className="relative overflow-hidden rounded-card bg-gradient-to-br from-brand-900 via-brand-700 to-accent-blue p-8 text-white shadow-[var(--shadow-lg)]">
        <div className="flex flex-wrap items-center gap-5">
          <Avatar name="Zayniddin" size={80} />
          <div>
            <h1 className="text-2xl font-bold">{t("profile.title")}</h1>
            <p className="mt-1 flex items-center gap-2 text-white/80">
              <Mail size={15} /> —
            </p>
          </div>
        </div>
      </section>

      {/* Details */}
      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-card bg-surface-card p-7 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
          <h2 className="text-lg font-bold text-text-primary">{t("profile.personalInfo")}</h2>
          <dl className="mt-5 space-y-4 text-sm">
            <Row icon={<User size={16} />} label={t("profile.name")} value="—" />
            <Row icon={<Mail size={16} />} label={t("profile.email")} value="—" />
            <Row icon={<MapPin size={16} />} label={t("profile.country")} value="—" />
          </dl>
        </section>

        <section className="rounded-card bg-surface-card p-7 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
          <h2 className="flex items-center gap-2 text-lg font-bold text-text-primary">
            <Sparkles size={18} className="text-accent-blue" /> {t("profile.interests")}
          </h2>
          <p className="mt-3 text-sm text-text-secondary">
            {t("profile.interestsBody")}
          </p>
        </section>
      </div>
    </div>
  );
}

function Row({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-surface-border pb-3 last:border-0 last:pb-0">
      <dt className="flex items-center gap-2 text-text-secondary">
        {icon}
        {label}
      </dt>
      <dd className="font-medium text-text-primary">{value}</dd>
    </div>
  );
}
