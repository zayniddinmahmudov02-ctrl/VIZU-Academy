"use client";

import { useLanguageStore } from "@/store/language-store";
import { translations } from "./translations";

export function useTranslation() {
  const { language, setLanguage } = useLanguageStore();

  function t(path: string, vars?: Record<string, string | number>): string {
    const [ns, key] = path.split(".");
    const entry = translations[ns]?.[key];
    let str = entry?.[language] ?? path;

    if (vars) {
      for (const [name, value] of Object.entries(vars)) {
        str = str.replace(new RegExp(`\\{${name}\\}`, "g"), String(value));
      }
    }

    return str;
  }

  return { t, language, setLanguage };
}
