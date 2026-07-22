import { api } from "@/services/api";

import type {
  AdminVideoItem,
  UpdateVideoInput,
  UploadVideoInput,
} from "../types/video";

function mapVideo(raw: any): AdminVideoItem {
  return {
    id: raw.id,
    lessonId: raw.lesson_id,
    title: raw.title,
    description: raw.description,
    thumbnailUrl: raw.thumbnail_url,
    durationSeconds: raw.duration_seconds,
    orderIndex: raw.order_index,
    isPreview: raw.is_preview,
    isPublished: raw.is_published,
    hasStorageKey: Boolean(raw.storage_key),
  };
}

export async function listVideos(lessonId?: string): Promise<AdminVideoItem[]> {
  const response = await api.get("/admin/videos", {
    params: lessonId ? { lesson_id: lessonId } : undefined,
  });
  return response.data.map(mapVideo);
}

export async function uploadVideo(
  input: UploadVideoInput,
  onProgress?: (percent: number) => void,
): Promise<AdminVideoItem> {
  const formData = new FormData();
  formData.append("lesson_id", input.lessonId);
  formData.append("title", input.title);
  if (input.description) formData.append("description", input.description);
  if (input.thumbnailUrl) formData.append("thumbnail_url", input.thumbnailUrl);
  formData.append("order_index", String(input.orderIndex ?? 1));
  formData.append("is_preview", String(input.isPreview ?? false));
  formData.append("is_published", String(input.isPublished ?? false));
  formData.append("file", input.file);

  const response = await api.post("/admin/videos/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (event) => {
      if (!onProgress || !event.total) return;
      onProgress(Math.round((event.loaded / event.total) * 100));
    },
  });

  return mapVideo(response.data);
}

export async function updateVideo(
  videoId: string,
  data: UpdateVideoInput,
): Promise<AdminVideoItem> {
  const response = await api.put(`/admin/videos/${videoId}`, {
    title: data.title,
    description: data.description,
    thumbnail_url: data.thumbnailUrl,
    order_index: data.orderIndex,
    is_preview: data.isPreview,
    is_published: data.isPublished,
  });
  return mapVideo(response.data);
}

export async function deleteVideo(videoId: string): Promise<void> {
  await api.delete(`/admin/videos/${videoId}`);
}
