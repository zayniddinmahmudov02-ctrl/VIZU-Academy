export interface Lesson {
  id: string;

  moduleId: string;

  number: number;

  title: string;

  duration: number;

  videoUrl: string | null;

  /** Optional listening-exercise audio track for this lesson. */
  audioUrl?: string | null;

  isFree: boolean;

  /** 0 or 100 — derived from StudentProgress.lesson_completed, not a
   *  fractional in-lesson progress tracker. */
  progress: number;

  /** Computed relative to the requesting user (see backend
   *  can_access_lesson) — first 3 lessons per level are always false,
   *  everything else is true unless the viewer is Premium/staff. */
  isLocked: boolean;
  requiresPremium: boolean;
}
