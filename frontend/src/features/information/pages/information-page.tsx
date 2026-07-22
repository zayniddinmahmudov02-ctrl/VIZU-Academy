"use client";

import { Info } from "lucide-react";

import Avatar from "@/components/ui/avatar";
import PageHeader from "@/components/dashboard/page-header";
import { InstagramIcon, TelegramIcon, YoutubeIcon } from "@/components/common/social-icons";
import { useInformation } from "../hooks/use-information";
import { useTranslation } from "@/lib/i18n/use-translation";

export default function InformationPage() {
  const { t } = useTranslation();
  const { information } = useInformation();

  const socialLinks = [
    {
      key: "telegram",
      href: information.telegramUrl,
      label: t("informationen.telegramLabel"),
      Icon: TelegramIcon,
    },
    {
      key: "instagram",
      href: information.instagramUrl,
      label: t("informationen.instagramLabel"),
      Icon: InstagramIcon,
    },
    {
      key: "youtube",
      href: information.youtubeUrl,
      label: t("informationen.youtubeLabel"),
      Icon: YoutubeIcon,
    },
  ];

  return (
    <div className="space-y-8">
      <PageHeader
        icon={Info}
        titleKey="sidebar.informationen"
        subtitleKey="informationen.pageSubtitle"
        gradient="from-accent-blue to-purple-600"
      />

      {/* About project */}
      <section className="rounded-card bg-surface-card p-7 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        <h2 className="text-lg font-bold text-text-primary">{t("informationen.aboutTitle")}</h2>

        <h3 className="mt-4 text-2xl font-bold text-accent-blue">{information.projectName}</h3>

        <p className="mt-2 text-sm text-text-secondary">
          {t("informationen.foundedLabel")}{" "}
          <span className="font-medium text-text-primary">{information.foundedDate}</span>
        </p>

        <div className="mt-5 rounded-2xl bg-surface-hover/60 p-5 ring-1 ring-surface-border">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
            {t("informationen.missionLabel")}
          </p>
          <p className="mt-2 text-text-secondary">{t("informationen.missionText")}</p>
        </div>
      </section>

      {/* Author */}
      <section className="rounded-card bg-surface-card p-7 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        <h2 className="text-lg font-bold text-text-primary">{t("informationen.authorTitle")}</h2>

        <div className="mt-5 flex flex-col items-center gap-6 text-center sm:flex-row sm:text-left">
          <Avatar
            src="/images/author.jpg"
            name={information.authorName}
            size={120}
            className="shrink-0 shadow-[var(--shadow-lg)] ring-4 ring-accent-blue/15"
          />

          <div>
            <h3 className="text-xl font-bold text-text-primary">{information.authorName}</h3>

            <p className="mt-1.5 text-sm text-text-secondary">
              {t("informationen.roleLabel")}{" "}
              <span className="font-medium text-text-primary">
                {t("informationen.roleValue")}
              </span>
            </p>

            <p className="mt-1 text-sm text-text-secondary">
              {t("informationen.qualificationLabel")}{" "}
              <span className="font-medium text-text-primary">
                {t("informationen.qualificationValue")}
              </span>
            </p>

            <p className="mt-3 text-text-secondary">{t("informationen.authorDescription")}</p>
          </div>
        </div>
      </section>

      {/* Social links */}
      <section className="rounded-card bg-surface-card p-7 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        <h2 className="text-lg font-bold text-text-primary">{t("informationen.socialTitle")}</h2>

        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          {socialLinks.map(({ key, href, label, Icon }) => (
            <a
              key={key}
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-center gap-3 rounded-2xl bg-surface-hover/60 p-5 ring-1 ring-surface-border transition-all duration-200 hover:-translate-y-1 hover:bg-accent-blue/5 hover:ring-accent-blue/30 hover:shadow-[var(--shadow-md)]"
            >
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-accent-blue to-purple-600 text-white shadow-md">
                <Icon size={20} />
              </span>
              <span className="font-semibold text-text-primary transition-colors group-hover:text-accent-blue">
                {label}
              </span>
            </a>
          ))}
        </div>
      </section>
    </div>
  );
}
