"use client";

import { useState } from "react";
import { Bell, Globe, Settings as SettingsIcon } from "lucide-react";

import PageHeader from "@/components/dashboard/page-header";
import { languages } from "@/constants/languages";
import { useTranslation } from "@/lib/i18n/use-translation";

export default function SettingsPage() {
  const { t, language } = useTranslation();
  const [emailNotif, setEmailNotif] = useState(true);
  const [reminders, setReminders] = useState(true);
  const currentLanguage = languages.find((item) => item.code === language) ?? languages[0];

  return (
    <div className="space-y-8">
      <PageHeader
        icon={SettingsIcon}
        titleKey="settings.title"
        subtitleKey="settings.subtitle"
        gradient="from-accent-blue to-purple-600"
      />

      <section className="rounded-card bg-surface-card p-7 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        <h2 className="text-lg font-bold text-text-primary">{t("settings.notifications")}</h2>
        <div className="mt-5 space-y-2">
          <Toggle
            icon={<Bell size={18} />}
            label={t("settings.emailNotifications")}
            checked={emailNotif}
            onChange={setEmailNotif}
          />
          <Toggle
            icon={<Bell size={18} />}
            label={t("settings.dailyReminders")}
            checked={reminders}
            onChange={setReminders}
          />
        </div>
      </section>

      <section className="rounded-card bg-surface-card p-7 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        <h2 className="text-lg font-bold text-text-primary">{t("settings.appearance")}</h2>
        <p className="mt-1 text-sm text-text-secondary">
          {t("settings.appearanceBody")}
        </p>
        <div className="mt-5 space-y-2">
          <div className="flex items-center justify-between rounded-2xl bg-surface-hover p-4">
            <span className="flex items-center gap-3 text-sm font-medium text-text-primary">
              <Globe size={18} /> {t("settings.language")}
            </span>
            <span className="text-sm text-text-secondary">{currentLanguage.name}</span>
          </div>
        </div>
      </section>
    </div>
  );
}

function Toggle({
  icon,
  label,
  checked,
  onChange,
}: {
  icon: React.ReactNode;
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between rounded-2xl bg-surface-hover p-4">
      <span className="flex items-center gap-3 text-sm font-medium text-text-primary">
        {icon}
        {label}
      </span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative h-6 w-11 rounded-full transition-colors ${
          checked ? "bg-accent-blue" : "bg-surface-border"
        }`}
      >
        <span
          className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all ${
            checked ? "left-[22px]" : "left-0.5"
          }`}
        />
      </button>
    </div>
  );
}
