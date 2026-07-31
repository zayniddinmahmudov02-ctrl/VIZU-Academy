export interface LessonVideo {
  id: string;
  title: string;
  description: string | null;
  thumbnailUrl: string | null;
  durationSeconds: number;
  videoUrl: string;
}

export interface VideoProgress {
  videoId: string;
  lessonId: string;
  lastPosition: number;
  watchPercent: number;
  completed: boolean;
}
