import { api } from "@/src/services/api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type { Video, VideoUpdate } from "../types/content.types";

export async function listVideosByLesson(lessonId: string): Promise<Video[]> {
  const response = await api.get<Video[]>(ADMIN_ENDPOINTS.videos, {
    params: { lesson_id: lessonId },
  });
  return response.data;
}

interface UploadVideoParams {
  lessonId: string;
  title: string;
  description?: string;
  durationSeconds?: number;
  orderIndex?: number;
  isPreview?: boolean;
  isPublished?: boolean;
  file: File;
  thumbnailFile?: File | null;
}

export async function uploadVideo(params: UploadVideoParams): Promise<Video> {
  const formData = new FormData();
  formData.append("lesson_id", params.lessonId);
  formData.append("title", params.title);
  if (params.description) formData.append("description", params.description);
  formData.append("duration_seconds", String(params.durationSeconds ?? 0));
  formData.append("order_index", String(params.orderIndex ?? 1));
  formData.append("is_preview", String(params.isPreview ?? false));
  formData.append("is_published", String(params.isPublished ?? false));
  formData.append("file", params.file);
  if (params.thumbnailFile) formData.append("thumbnail_file", params.thumbnailFile);

  const response = await api.post<Video>(`${ADMIN_ENDPOINTS.videos}/upload`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function replaceVideoFile(
  videoId: string,
  file: File,
  durationSeconds?: number,
): Promise<Video> {
  const formData = new FormData();
  formData.append("file", file);
  if (durationSeconds !== undefined) {
    formData.append("duration_seconds", String(durationSeconds));
  }

  const response = await api.put<Video>(
    `${ADMIN_ENDPOINTS.videos}/${videoId}/replace`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return response.data;
}

export async function updateVideo(videoId: string, data: VideoUpdate): Promise<Video> {
  const response = await api.put<Video>(`${ADMIN_ENDPOINTS.videos}/${videoId}`, data);
  return response.data;
}

export async function deleteVideo(videoId: string): Promise<void> {
  await api.delete(`${ADMIN_ENDPOINTS.videos}/${videoId}`);
}
