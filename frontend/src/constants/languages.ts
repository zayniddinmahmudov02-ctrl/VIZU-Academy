import type { Language } from "@/store/language-store";

export interface LanguageOption {
  code: Language;
  name: string;
  flag: string;
}

export const languages: LanguageOption[] = [
  {
    code: "de",
    name: "Deutsch",
    flag: "🇩🇪",
  },
  {
    code: "uz",
    name: "Uzbek",
    flag: "🇺🇿",
  },
];
