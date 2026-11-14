"use client";

import { motion } from "framer-motion";
import { Check, ChevronDown } from "lucide-react";

import Popover from "@/components/ui/popover";
import { languages } from "@/constants/languages";
import { useLanguageStore } from "@/store/language-store";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

type Props = {
  /** "sidebar" = compact UZ | DE | EN | RU control styled for the navy sidebar footer.
   *  "segmented" = small language buttons (Registration / Anmeldung pages). */
  variant?: "default" | "sidebar" | "segmented";
  className?: string;
};

export default function LanguageSwitcher({ variant = "default", className }: Props) {
  const { language, setLanguage } = useLanguageStore();
  const { t } = useTranslation();

  if (variant === "segmented") {
    return (
      <div
        role="group"
        aria-label={t("auth.languageSwitchAria")}
        className={cn("inline-flex rounded-full bg-surface-hover p-1 ring-1 ring-surface-border", className)}
      >
        {languages.map((item) => {
          const active = language === item.code;
          return (
            <button
              key={item.code}
              type="button"
              aria-pressed={active}
              data-lang={item.code}
              onClick={() => setLanguage(item.code)}
              className={cn(
                "min-w-[44px] rounded-full px-3 py-1.5 text-xs font-bold uppercase tracking-wide transition-colors",
                active ? "bg-accent-blue text-white shadow-sm" : "text-text-secondary hover:text-text-primary",
              )}
            >
              {item.code}
            </button>
          );
        })}
      </div>
    );
  }

  if (variant === "sidebar") {
    // four languages: a compact segmented control in the navy sidebar footer (the active one slides)
    return (
      <div
        role="group"
        aria-label={t("sidebar.toggleLanguageAria")}
        className="relative grid grid-cols-4 gap-0.5 rounded-2xl bg-white/[0.04] p-1 ring-1 ring-white/10"
      >
        {languages.map((item) => {
          const active = language === item.code;
          return (
            <button
              key={item.code}
              type="button"
              aria-pressed={active}
              data-lang={item.code}
              title={item.name}
              onClick={() => setLanguage(item.code)}
              className={cn(
                "relative h-9 rounded-xl text-[11px] font-bold uppercase tracking-wide transition-colors",
                active ? "text-brand-900" : "text-sidebar-muted hover:text-white",
              )}
            >
              {active && (
                <motion.span
                  layoutId="sidebar-language-pill"
                  className="absolute inset-0 rounded-xl bg-white shadow-md"
                  transition={{ type: "spring", stiffness: 500, damping: 34 }}
                />
              )}
              <span className="relative">{item.code}</span>
            </button>
          );
        })}
      </div>
    );
  }

  const current = languages.find((item) => item.code === language) ?? languages[0];

  return (
    <Popover
      align="end"
      trigger={
        <span className="flex h-11 items-center gap-2 rounded-button px-3 text-sm font-semibold text-text-secondary transition-colors hover:bg-surface-hover hover:text-text-primary">
          <span>{current.flag}</span>
          <span className="uppercase">{current.code}</span>
          <ChevronDown size={14} className="text-text-muted" />
        </span>
      }
    >
      <p className="mb-2 px-2 text-xs font-semibold uppercase tracking-wide text-text-muted">
        {t("settings.language")}
      </p>
      <div className="flex flex-col gap-0.5">
        {languages.map((item) => {
          const isActive = language === item.code;

          return (
            <button
              key={item.code}
              onClick={() => setLanguage(item.code)}
              className="flex items-center justify-between rounded-xl px-3 py-2.5 text-left text-sm font-medium text-text-primary transition-colors hover:bg-surface-hover"
            >
              <span className="flex items-center gap-2">
                <span>{item.flag}</span>
                {item.name}
              </span>
              {isActive && <Check size={14} className="text-accent-blue" />}
            </button>
          );
        })}
      </div>
    </Popover>
  );
}
