"use client";

import { useMemo } from "react";
import { Video as VideoIcon } from "lucide-react";

import { useLessons } from "@/features/lessons/hooks/use-lessons";
import { useAdminVideos } from "../hooks/use-admin-videos";
import VideoUploadForm from "../components/video-upload-form";
import VideosTable from "../components/videos-table";
import type { AdminVideoItem } from "../types/video";

export default function AdminVideosPage() {
  const { lessons } = useLessons();
  const videos = useAdminVideos();

  const lessonTitleById = useMemo(
    () => Object.fromEntries(lessons.map((lesson) => [lesson.id, lesson.title])),
    [lessons],
  );

  async function handleTogglePublished(video: AdminVideoItem) {
    await videos.update(video.id, { isPublished: !video.isPublished });
  }

  async function handleDelete(videoId: string) {
    if (!window.confirm("Delete this video? This also removes its uploaded file.")) return;
    await videos.remove(videoId);
  }

  async function handleReplace(videoId: string, file: File, durationSeconds: number) {
    await videos.replace(videoId, { file, durationSeconds });
  }

  return (
    <div className="space-y-6">
      <div className="admin-glass flex flex-wrap items-center justify-between gap-4 rounded-2xl p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--admin-primary)] to-[var(--admin-secondary)] text-white">
            <VideoIcon size={20} />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">Videos</h1>
            <p className="text-xs text-[var(--admin-text-muted)]">{videos.data?.length ?? 0} videos</p>
          </div>
        </div>
      </div>

      <VideoUploadForm
        uploading={videos.uploading}
        uploadProgress={videos.uploadProgress}
        uploadError={videos.uploadError}
        onUpload={videos.upload}
      />

      <VideosTable
        videos={videos.data ?? []}
        loading={videos.loading}
        lessonTitleById={lessonTitleById}
        replacing={videos.replacing}
        onTogglePublished={handleTogglePublished}
        onDelete={handleDelete}
        onReplace={handleReplace}
      />
    </div>
  );
}
