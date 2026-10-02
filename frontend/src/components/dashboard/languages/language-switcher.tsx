"use client";

import { Switch } from "@base-ui/react/switch";
import { motion } from "framer-motion";
import { Check, ChevronDown } from "lucide-react";

import Popover from "@/components/ui/popover";
import { languages } from "@/constants/languages";
import { useLanguageStore } from "@/store/language-store";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

type Props = {
  /** "sidebar" = compact Deutsch/Uzbek toggle styled for the navy sidebar footer.
   *  "segmented" = small DE | UZ buttons (Registration / Anmeldung pages). */
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
    const isUz = language === "uz";

    return (
      <div className="flex items-center justify-center gap-3 rounded-2xl bg-white/[0.04] px-3 py-2.5">
        <span
          className={cn(
            "text-xs font-semibold transition-colors",
            isUz ? "text-sidebar-muted" : "text-white",
          )}
        >
          Deutsch
        </span>

        <Switch.Root
          checked={isUz}
          onCheckedChange={(checked) => setLanguage(checked ? "uz" : "de")}
          aria-label={t("sidebar.toggleLanguageAria")}
          className="relative inline-flex h-9 w-16 shrink-0 items-center rounded-full bg-white/[0.08] p-0.5 ring-1 ring-white/10 transition-colors duration-200"
        >
          <motion.span
            className="flex h-7 w-7 items-center justify-center rounded-full bg-white text-[9px] font-bold text-brand-900 shadow-md"
            animate={{ x: isUz ? 28 : 0 }}
            transition={{ type: "spring", stiffness: 500, damping: 32 }}
          >
            {isUz ? "UZ" : "DE"}
          </motion.span>
        </Switch.Root>

        <span
          className={cn(
            "text-xs font-semibold transition-colors",
            isUz ? "text-white" : "text-sidebar-muted",
          )}
        >
          Uzbek
        </span>
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
