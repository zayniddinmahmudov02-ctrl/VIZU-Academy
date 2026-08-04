import { api } from "@/src/services/api";
import { ensureArray } from "@/lib/ensure-array";
import type { MediaAsset } from "../types/content.types";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";

export async function uploadMediaAsset(
  file: File,
  folder: "videos" | "audio" | "images" | "documents" | "thumbnails",
): Promise<MediaAsset> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post<MediaAsset>(
    `${ADMIN_ENDPOINTS.mediaLibraryUpload}?folder=${folder}`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } },
  );

  return response.data;
}

export async function listMediaAssets(
  folder?: string,
  mediaType?: string,
): Promise<MediaAsset[]> {
  const response = await api.get<MediaAsset[]>(ADMIN_ENDPOINTS.mediaLibrary, {
    params: { folder, media_type: mediaType },
  });
  return ensureArray<MediaAsset>(response.data);
}

export async function deleteMediaAsset(id: string): Promise<void> {
  await api.delete(`${ADMIN_ENDPOINTS.mediaLibrary.replace(/\/$/, "")}/${id}`);
}
