"use client";

import { useState } from "react";

import { useAsyncResource } from "./use-async-resource";
import * as videosService from "../services/videos-service";
import type { UpdateVideoInput, UploadVideoInput } from "../types/video";

export function useAdminVideos(lessonId?: string) {
  const resource = useAsyncResource(
    () => videosService.listVideos(lessonId),
    [lessonId],
  );

  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);

  async function upload(input: UploadVideoInput) {
    setUploading(true);
    setUploadProgress(0);
    setUploadError(null);

    try {
      const video = await videosService.uploadVideo(input, setUploadProgress);
      resource.refetch();
      return video;
    } catch (err: any) {
      setUploadError(err?.response?.data?.message ?? "Failed to upload video.");
      throw err;
    } finally {
      setUploading(false);
    }
  }

  async function update(videoId: string, data: UpdateVideoInput) {
    await videosService.updateVideo(videoId, data);
    resource.refetch();
  }

  async function remove(videoId: string) {
    await videosService.deleteVideo(videoId);
    resource.refetch();
  }

  return {
    ...resource,
    uploading,
    uploadProgress,
    uploadError,
    upload,
    update,
    remove,
  };
}
