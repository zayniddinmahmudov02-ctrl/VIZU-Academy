import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

interface LessonProgressState {
  /** lessonId -> array of completed section slugs */
  completedSections: Record<string, string[]>;
  toggleSection: (lessonId: string, slug: string) => void;
  markSectionComplete: (lessonId: string, slug: string) => void;
  isSectionComplete: (lessonId: string, slug: string) => boolean;
  getCompletedCount: (lessonId: string) => number;
}

export const useLessonProgressStore = create<LessonProgressState>()(
  persist(
    (set, get) => ({
      completedSections: {},

      toggleSection: (lessonId, slug) =>
        set((state) => {
          const current = state.completedSections[lessonId] ?? [];
          const next = current.includes(slug)
            ? current.filter((s) => s !== slug)
            : [...current, slug];
          return { completedSections: { ...state.completedSections, [lessonId]: next } };
        }),

      markSectionComplete: (lessonId, slug) =>
        set((state) => {
          const current = state.completedSections[lessonId] ?? [];
          if (current.includes(slug)) return state;
          return {
            completedSections: { ...state.completedSections, [lessonId]: [...current, slug] },
          };
        }),

      isSectionComplete: (lessonId, slug) =>
        (get().completedSections[lessonId] ?? []).includes(slug),

      getCompletedCount: (lessonId) => (get().completedSections[lessonId] ?? []).length,
    }),
    {
      name: "vizu-lesson-progress",
      storage: createJSONStorage(() => localStorage),
      skipHydration: true,
    },
  ),
);
