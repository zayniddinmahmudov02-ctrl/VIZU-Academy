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
}
