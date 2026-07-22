import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export type Language = "de" | "uz";

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
