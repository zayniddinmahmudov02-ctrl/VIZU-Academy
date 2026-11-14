"use client";

import { useLanguageStore } from "@/store/language-store";
import { extraTranslations } from "./translations-extra";
import { translations } from "./translations";

/** t("ns.key", vars): uz / de from translations.ts; en / ru from translations-extra.ts ([en, ru] per key). A missing
 * English or Russian text falls back to German, a missing key to the key itself. */
export function translate(language: string, path: string, vars?: Record<string, string | number>): string {
  const [ns, ...rest] = path.split(".");
  const key = rest.join("."); // keys may contain a dot (e.g. "err.GENERIC"); every older key has exactly one
  const entry = translations[ns]?.[key];
  let str: string | undefined;
  if (language === "en" || language === "ru") {
    const extra = extraTranslations[ns]?.[key];
    str = extra?.[language === "en" ? 0 : 1] || entry?.de;
  } else {
    str = entry?.[language as "de" | "uz"];
  }
  str = str ?? path;
  if (vars) {
    for (const [name, value] of Object.entries(vars)) {
      str = str.replace(new RegExp(`\\{${name}\\}`, "g"), String(value));
    }
  }
  return str;
}

export function useTranslation() {
  const { language, setLanguage } = useLanguageStore();

  function t(path: string, vars?: Record<string, string | number>): string {
    return translate(language, path, vars);
  }

  return { t, language, setLanguage };
}
