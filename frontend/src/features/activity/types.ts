/** API shapes of the activity statistics (backend app/services/activity/stats.py). Times in seconds, dates ISO. */

export interface SongStat {
  id: string;
  title: string;
  artist: string | null;
  duration_ms: number | null;
  play_count: number;
  listened_seconds: number;
  last_listened_at: string | null;
}

export interface MusicStats {
  songs_listened: number;
  play_count: number;
  listened_seconds: number;
  top: SongStat[];
  recent: SongStat[];
  history: SongStat[];
  last: SongStat | null;
}

export interface BookStat {
  id: string;
  title: string;
  author: string | null;
  page: number | null;
  pages: number | null;
  completed: boolean;
  reading_seconds: number;
  last_opened_at: string | null;
}

export interface BookStats {
  books_opened: number;
  books_completed: number;
  reading_seconds: number;
  recent: BookStat[];
  history: BookStat[];
  last: BookStat | null;
}

export interface FilmStat {
  id: string;
  title: string;
  position_seconds: number;
  duration_seconds: number | null;
  completed: boolean;
  watched_seconds: number;
  last_watched_at: string | null;
}

export interface FilmStats {
  films_watched: number;
  films_completed: number;
  watched_seconds: number;
  recent: FilmStat[];
  history: FilmStat[];
  continue: FilmStat[];
  last: FilmStat | null;
}

export type DailyRow = { date: string } & Record<string, number | string>;

export interface MediaStats {
  music: MusicStats;
  books: BookStats;
  films: FilmStats;
  media_seconds: number;
  daily: DailyRow[];
  tracking_since: string | null;
}

export interface UsageStats {
  total_seconds: number;
  today_seconds: number;
  week_seconds: number;
  month_seconds: number;
  active_days: number;
  last_activity_at: string | null;
  tracking_since: string | null;
  last_login_at?: string | null;
  timezone: string;
}

export interface CourseStat {
  course_id: string;
  title: string;
  level: string;
  lessons_completed: number;
  lessons_total: number;
  percent: number;
  started_at: string | null;
  last_lesson: { id: string; number: number; title: string; at: string | null } | null;
  seconds: number;
}

export interface VocabularyStats {
  seconds: number;
  words_learned: number;
  words_saved: number;
  words_repeated: number;
  blocks_completed: number;
  last_activity_at: string | null;
}

export type StudentStatus = "active" | "inactive" | "blocked";

export interface KontrollRow {
  id: string;
  name: string;
  email: string;
  registered_at: string;
  status: StudentStatus;
  usage_seconds: number;
  last_activity_at: string | null;
  courses_completed: number;
  lessons_completed: number;
  music_seconds: number;
  vocabulary_seconds: number;
  books_viewed: number;
  films_viewed: number;
}

export interface KontrollList {
  items: KontrollRow[];
  total: number;
  page: number;
  page_size: number;
  sort: string;
}

export interface KontrollDetail {
  student: { id: string; name: string; email: string; username: string; registered_at: string; status: StudentStatus };
  general: UsageStats;
  area_seconds: Record<string, number>;
  courses: CourseStat[];
  music: MusicStats;
  vocabulary: VocabularyStats;
  books: BookStats;
  films: FilmStats;
  daily: DailyRow[];
}

export interface TimelineItem {
  id: string;
  area: string;
  ref_id: string | null;
  started_at: string;
  ended_at: string;
  time: string;
  seconds: number;
  title: string | null;
  level: string | null;
  lesson_number: number | null;
}

export interface Timeline {
  day: string | null;
  days: string[];
  items: TimelineItem[];
}
