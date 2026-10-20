import { api } from "@/src/services/api";

/** Server-confirmed learning activity (GET /dashboard/me/learning-activity) —
 * only playback that really advanced and submitted tasks count. */
export interface LearningActivity {
  timezone: string;
  streak_days: number;
  total_seconds: number;
  last_activity_at: string | null;
  active_days_week: number;
  week_seconds: number;
  week: { date: string; seconds: number }[];
}

/** The browser's IANA time zone — the streak counts the student's local days. */
export function browserTimeZone(): string | undefined {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || undefined;
  } catch {
    return undefined;
  }
}

export async function getLearningActivity(): Promise<LearningActivity> {
  const tz = browserTimeZone();
  return (await api.get<LearningActivity>("/api/v1/dashboard/me/learning-activity", { params: tz ? { tz } : {} })).data;
}
