import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export type Language = "de" | "uz" | "en" | "ru";

export const LANGUAGE_CODES: Language[] = ["uz", "de", "en", "ru"];

export function isLanguage(value: unknown): value is Language {
  return typeof value === "string" && (LANGUAGE_CODES as string[]).includes(value);
}

interface LanguageState {
  language: Language;

  setLanguage: (language: Language) => void;
}

export const useLanguageStore = create<LanguageState>()(
  persist(
    (set) => ({
      language: "de",

      setLanguage: (language) => set({ language }),
    }),
    {
      name: "vizu-language",
      storage: createJSONStorage(() => localStorage),
      skipHydration: true,
    },
  ),
);
