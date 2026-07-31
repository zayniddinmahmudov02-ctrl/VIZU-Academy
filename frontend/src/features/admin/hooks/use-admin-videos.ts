"use client";

import { useState } from "react";
import { isAxiosError } from "axios";

import { useAsyncResource } from "./use-async-resource";
import * as videosService from "../services/videos-service";
import type {
  ReplaceVideoInput,
  UpdateVideoInput,
  UploadVideoInput,
} from "../types/video";

function extractErrorMessage(err: unknown, fallback: string): string {
  if (isAxiosError<{ message?: string }>(err)) {
    return err.response?.data?.message ?? fallback;
  }
  return fallback;
}

export function useAdminVideos(lessonId?: string) {
  const resource = useAsyncResource(
    () => videosService.listVideos(lessonId),
    [lessonId],
  );

  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [replacing, setReplacing] = useState(false);
  const [replaceProgress, setReplaceProgress] = useState(0);
  const [replaceError, setReplaceError] = useState<string | null>(null);

  async function upload(input: UploadVideoInput) {
    setUploading(true);
    setUploadProgress(0);
    setUploadError(null);

    try {
      const video = await videosService.uploadVideo(input, setUploadProgress);
      resource.refetch();
      return video;
    } catch (err) {
      setUploadError(extractErrorMessage(err, "Failed to upload video."));
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

  async function replace(videoId: string, input: ReplaceVideoInput) {
    setReplacing(true);
    setReplaceProgress(0);
    setReplaceError(null);

    try {
      const video = await videosService.replaceVideo(videoId, input, setReplaceProgress);
      resource.refetch();
      return video;
    } catch (err) {
      setReplaceError(extractErrorMessage(err, "Failed to replace video."));
      throw err;
    } finally {
      setReplacing(false);
    }
  }

  return {
    ...resource,
    uploading,
    uploadProgress,
    uploadError,
    upload,
    update,
    remove,
    replacing,
    replaceProgress,
    replaceError,
    replace,
  };
}
