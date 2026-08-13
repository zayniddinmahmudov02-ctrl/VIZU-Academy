import type { AxiosProgressEvent } from "axios";

import { api } from "@/src/services/api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type {
  Video,
  VideoUpdate,
  VideoUploadChunkResult,
  VideoUploadInitPayload,
  VideoUploadInitResult,
  VideoUploadStatusResult,
} from "../types/content.types";
import type { UploadRequestOptions } from "../lib/upload";

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

export async function uploadVideo(params: UploadVideoParams, options?: UploadRequestOptions): Promise<Video> {
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
    onUploadProgress: options?.onUploadProgress,
    signal: options?.signal,
  });
  return response.data;
}

export async function replaceVideoFile(
  videoId: string,
  file: File,
  durationSeconds?: number,
  options?: UploadRequestOptions,
): Promise<Video> {
  const formData = new FormData();
  formData.append("file", file);
  if (durationSeconds !== undefined) {
    formData.append("duration_seconds", String(durationSeconds));
  }

  const response = await api.put<Video>(
    `${ADMIN_ENDPOINTS.videos}/${videoId}/replace`,
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: options?.onUploadProgress,
      signal: options?.signal,
    },
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

// ==========================
// Chunked upload — for files too large to survive as a single request
// through the edge proxy (Cloudflare 413s anything above ~50-99MB before
// it reaches the backend at all). See features/admin/lib/chunked-video-upload.ts
// for the orchestrator that drives these three calls.
// ==========================

export async function initVideoUpload(payload: VideoUploadInitPayload): Promise<VideoUploadInitResult> {
  const response = await api.post<VideoUploadInitResult>(`${ADMIN_ENDPOINTS.videos}/upload/init`, payload);
  return response.data;
}

export async function uploadVideoChunk(
  uploadId: string,
  chunkNumber: number,
  totalChunks: number,
  chunk: Blob,
  options?: { onUploadProgress?: (event: AxiosProgressEvent) => void; signal?: AbortSignal },
): Promise<VideoUploadChunkResult> {
  const formData = new FormData();
  formData.append("chunk_number", String(chunkNumber));
  formData.append("total_chunks", String(totalChunks));
  formData.append("file", chunk, "chunk");

  const response = await api.post<VideoUploadChunkResult>(
    `${ADMIN_ENDPOINTS.videos}/upload/${uploadId}/chunk`,
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: options?.onUploadProgress,
      signal: options?.signal,
    },
  );
  return response.data;
}

export async function getVideoUploadStatus(uploadId: string): Promise<VideoUploadStatusResult> {
  const response = await api.get<VideoUploadStatusResult>(`${ADMIN_ENDPOINTS.videos}/upload/${uploadId}/status`);
  return response.data;
}

export async function completeVideoUpload(uploadId: string): Promise<Video> {
  const response = await api.post<Video>(`${ADMIN_ENDPOINTS.videos}/upload/${uploadId}/complete`);
  return response.data;
}
