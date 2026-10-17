/** VIZU LMS (A1–C1) — response shapes of the student API
 * (backend: app/api/lms/router.py, app/services/lms/progress.py). */

export type CompetencyKind =
  | "EINFUEHRUNG"
  | "WORTSCHATZ"
  | "GRAMMATIK"
  | "LESEN"
  | "HOEREN"
  | "SPRECHEN"
  | "SCHREIBEN"
  | "UEBUNGEN"
  | "ABSCHLUSSTEST"
  | "ZUSAMMENFASSUNG";

/** Real progress state (`progress_status`) plus the two display-only states
 * the backend overlays: "locked" (lesson locked) and "not_available". */
export type CompetencyStatus = "not_started" | "in_progress" | "completed" | "locked" | "not_available";
export type LessonStatus = "not_started" | "in_progress" | "completed" | "locked";
export type LockReason = "DRAFT" | "ADMIN_LOCKED" | "PREMIUM_REQUIRED" | "PREVIOUS_LESSON_NOT_COMPLETED" | "LEVEL_COMING_SOON";

/** An Angebote offer as the LMS level API describes it (prices from the
 * backend configuration, Admin -> Angebote). */
export interface LmsSaleOffer {
  code: string;
  kind: "LEVEL" | "PACKAGE";
  label: string;
  levels: string[];
  available_levels: string[];
  original_price: number | null;
  sale_price: number | null;
  discount_percent: number | null;
  purchasable: boolean;
  currency: string;
}

export interface LmsLevelSale {
  available: boolean;
  coming_soon: boolean;
  owned: boolean;
  free_lessons: number;
  offer: LmsSaleOffer | null;
  packages: LmsSaleOffer[];
}

export interface LmsLevelSummary {
  level: string;
  course_id: string | null;
  title: string;
  sequential_unlock: boolean;
  lessons_target: number;
  lessons_published: number;
  lessons_completed: number;
  percent: number;
  last_lesson_id: string | null;
  continue_lesson_id: string | null;
  sale?: LmsLevelSale;
}

export interface LmsLevels {
  total_lessons_target: number;
  levels: LmsLevelSummary[];
}

export interface LmsLessonCard {
  id: string;
  number: number;
  title: string;
  description: string | null;
  duration: number;
  is_published: boolean;
  has_video: boolean;
  status: LessonStatus;
  lock_reason: LockReason | null;
  completed: boolean;
  percent: number;
  competencies_total: number | null;
  competencies_completed: number | null;
  completed_at: string | null;
  last_activity_at: string | null;
}

export interface LmsLevel extends LmsLevelSummary {
  lessons: LmsLessonCard[];
}

export interface LmsCompetency {
  kind: CompetencyKind;
  position: number;
  is_published: boolean;
  /** Admin text — HTML sanitised on the server (allow-list). */
  body: string | null;
  available: boolean;
  tracked: boolean;
  counts_for_completion: boolean;
  status: CompetencyStatus;
  progress_status: Exclude<CompetencyStatus, "locked">;
  /** e.g. "pending_evaluation" while a teacher / the AI grades a submission */
  detail: string | null;
  score: number | null;
  videos: number;
  resources: number;
  visited_at: string | null;
  completed_at: string | null;
}

export interface LmsVideo {
  id: string;
  title: string;
  description: string | null;
  competency: CompetencyKind;
  duration_seconds: number;
  thumbnail_url: string | null;
  order_index: number;
  /** signed, short-lived — relative to the API origin */
  stream_url: string;
  subtitle_url: string | null;
  progress: { last_position: number; watch_percent: number; completed: boolean } | null;
}

export type ResourceType = "AUDIO" | "PDF" | "IMAGE" | "DOCUMENT" | "LINK";

export interface LmsResource {
  id: string;
  lesson_id: string;
  competency: CompetencyKind | null;
  resource_type: ResourceType;
  title: string;
  description: string | null;
  mime_type: string | null;
  size_bytes: number | null;
  duration_seconds: number | null;
  order_index: number;
  external_url: string | null;
  /** signed, short-lived — relative to the API origin (null for links) */
  file_url: string | null;
}

export interface LmsLessonRef {
  id: string;
  number: number;
  title: string;
}

export interface LmsLesson {
  lesson: {
    id: string;
    number: number;
    title: string;
    description: string | null;
    duration: number;
    level: string | null;
    course_id: string | null;
  };
  navigation: { previous: LmsLessonRef | null; next: LmsLessonRef | null };
  competency_order: CompetencyKind[];
  lesson_id: string;
  access: { unlocked: boolean; reason: LockReason | null };
  status: LessonStatus;
  progress_status: Exclude<LessonStatus, "locked">;
  completed: boolean;
  competencies_total: number;
  competencies_completed: number;
  percent: number;
  competencies: LmsCompetency[];
  videos: LmsVideo[];
  resources: LmsResource[];
}

export interface LmsVisitResult {
  lesson_id: string;
  status: LessonStatus;
  completed: boolean;
  percent: number;
  competencies_total: number;
  competencies_completed: number;
  competencies: LmsCompetency[];
}
