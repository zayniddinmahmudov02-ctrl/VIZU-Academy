import { api } from "@/lib/api";

import type { LessonVideo, VideoProgress } from "../types/video";

interface VideoStreamPayload {
  id: string;
  title: string;
  description: string | null;
  thumbnail_url: string | null;
  duration_seconds: number;
  video_url: string;
}

interface VideoProgressPayload {
  video_id: string;
  lesson_id: string;
  last_position: number;
  watch_percent: number;
  completed: boolean;
}

function mapVideo(payload: VideoStreamPayload): LessonVideo {
  return {
    id: payload.id,
    title: payload.title,
    description: payload.description,
    thumbnailUrl: payload.thumbnail_url,
    durationSeconds: payload.duration_seconds,
    videoUrl: payload.video_url,
  };
}

function mapProgress(payload: VideoProgressPayload): VideoProgress {
  return {
    videoId: payload.video_id,
    lessonId: payload.lesson_id,
    lastPosition: payload.last_position,
    watchPercent: payload.watch_percent,
    completed: payload.completed,
  };
}

export async function getLessonVideo(lessonId: string): Promise<LessonVideo> {
  const payload = await api<VideoStreamPayload>(`/api/v1/videos/by-lesson/${lessonId}`);
  return mapVideo(payload);
}

export async function getVideoProgress(lessonId: string): Promise<VideoProgress> {
  const payload = await api<VideoProgressPayload>(`/api/v1/videos/progress/${lessonId}`);
  return mapProgress(payload);
}

export async function updateVideoProgress(
  videoId: string,
  position: number,
  ended = false,
): Promise<VideoProgress> {
  const payload = await api<VideoProgressPayload>("/api/v1/videos/progress", {
    method: "POST",
    body: JSON.stringify({ video_id: videoId, position, ended }),
  });
  return mapProgress(payload);
}

export async function completeVideo(videoId: string, ended = false): Promise<VideoProgress> {
  const payload = await api<VideoProgressPayload>("/api/v1/videos/complete", {
    method: "POST",
    body: JSON.stringify({ video_id: videoId, ended }),
  });
  return mapProgress(payload);
}
