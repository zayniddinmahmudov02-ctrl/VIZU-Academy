import type { Language } from "@/store/language-store";

export interface LanguageOption {
  code: Language;
  name: string;
  flag: string;
  /** flag image in /public/flags */
  flagSrc: string;
  /** Intl locale for dates and numbers */
  locale: string;
}

export const languages: LanguageOption[] = [
  { code: "uz", name: "O'zbek", flag: "🇺🇿", flagSrc: "/flags/uz.svg", locale: "uz-UZ" },
  { code: "de", name: "Deutsch", flag: "🇩🇪", flagSrc: "/flags/de.svg", locale: "de-DE" },
  { code: "en", name: "English", flag: "🇬🇧", flagSrc: "/flags/en.svg", locale: "en-GB" },
  { code: "ru", name: "Русский", flag: "🇷🇺", flagSrc: "/flags/ru.svg", locale: "ru-RU" },
];

export function localeFor(language: Language): string {
  return languages.find((item) => item.code === language)?.locale ?? "de-DE";
}
