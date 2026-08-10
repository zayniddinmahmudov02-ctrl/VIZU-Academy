"use client";

import { useState } from "react";
import { AlertCircle, Check, Globe } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { useLanguageStore, type Language } from "@/store/language-store";

import { useUpdateLanguage } from "../hooks/use-update-language";

const OPTIONS: { code: Language; label: string; flag: string; alt: string }[] = [
  { code: "de", label: "Deutsch", flag: "/flags/de.svg", alt: "Deutschland" },
  { code: "uz", label: "O'zbek", flag: "/flags/uz.svg", alt: "O'zbekiston" },
];

export default function LanguageCard() {
  const { t } = useTranslation();
  const { language, setLanguage } = useLanguageStore();
  const updateLanguage = useUpdateLanguage();
  const [error, setError] = useState(false);

  function select(code: Language) {
    if (code === language) return;

    setError(false);
    setLanguage(code);

    updateLanguage.mutate(code, {
      onError: () => setError(true),
    });
  }

  return (
    <section className="rounded-card bg-surface-card p-7 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
      <h2 className="flex items-center gap-2 text-lg font-bold text-text-primary">
        <Globe size={18} className="text-accent-blue" />
        {t("profile.languageSettings")}
      </h2>
      <p className="mt-1 text-sm text-text-secondary">{t("profile.interfaceLanguage")}</p>

      {error && (
        <div className="mt-3 flex items-center gap-2 rounded-xl bg-danger/10 px-4 py-2.5 text-sm text-danger">
          <AlertCircle size={16} />
          {t("profile.saveError")}
        </div>
      )}

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {OPTIONS.map((option) => {
          const active = option.code === language;
          return (
            <button
              key={option.code}
              type="button"
              onClick={() => select(option.code)}
              disabled={updateLanguage.isPending}
              className={`flex items-center gap-3 rounded-2xl border px-4 py-3.5 text-left transition-all ${
                active
                  ? "border-accent-blue bg-accent-blue/5 ring-2 ring-accent-blue/30"
                  : "border-surface-border bg-surface-hover hover:border-accent-blue/40"
              }`}
            >
              <img src={option.flag} alt={option.alt} width={28} height={20} className="rounded-sm shadow-sm" />
              <span className="flex-1 text-sm font-medium text-text-primary">{option.label}</span>
              {active && <Check size={16} className="text-accent-blue" />}
            </button>
          );
        })}
      </div>
    </section>
  );
}
