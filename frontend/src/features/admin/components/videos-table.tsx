"use client";

import { useRef } from "react";
import { Eye, RefreshCw, Trash2 } from "lucide-react";

import Popover from "@/components/ui/popover";
import { detectVideoDuration } from "../utils/detect-video-duration";
import DataTable, { type DataTableColumn } from "./data-table";
import { Badge } from "./badges";
import type { AdminVideoItem } from "../types/video";

const ACCEPTED_TYPES = ["video/mp4", "video/webm", "video/quicktime"];

interface Props {
  videos: AdminVideoItem[];
  loading: boolean;
  lessonTitleById: Record<string, string>;
  replacing: boolean;
  onTogglePublished: (video: AdminVideoItem) => void;
  onDelete: (videoId: string) => void;
  onReplace: (videoId: string, file: File, durationSeconds: number) => void;
}

function formatDuration(seconds: number): string {
  if (!seconds) return "—";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export default function VideosTable({
  videos,
  loading,
  lessonTitleById,
  replacing,
  onTogglePublished,
  onDelete,
  onReplace,
}: Props) {
  const replaceInputRef = useRef<HTMLInputElement>(null);
  const replaceTargetRef = useRef<string | null>(null);

  function requestReplace(videoId: string) {
    replaceTargetRef.current = videoId;
    replaceInputRef.current?.click();
  }

  async function handleReplaceFileSelected(file: File | null) {
    const videoId = replaceTargetRef.current;
    if (!file || !videoId) return;

    if (!ACCEPTED_TYPES.includes(file.type)) {
      window.alert("Unsupported file type. Allowed: MP4, WebM, MOV.");
      return;
    }

    const durationSeconds = await detectVideoDuration(file);
    onReplace(videoId, file, durationSeconds);
  }

  const columns: DataTableColumn<AdminVideoItem>[] = [
    {
      key: "title",
      label: "Title",
      render: (video) => (
        <div>
          <p className="font-medium text-white">{video.title}</p>
          <p className="text-xs text-[var(--admin-text-muted)]">
            {lessonTitleById[video.lessonId] ?? video.lessonId}
          </p>
        </div>
      ),
    },
    {
      key: "duration",
      label: "Duration",
      render: (video) => (
        <span className="text-[var(--admin-text-secondary)]">{formatDuration(video.durationSeconds)}</span>
      ),
    },
    {
      key: "order",
      label: "Order",
      render: (video) => <span className="text-[var(--admin-text-secondary)]">{video.orderIndex}</span>,
    },
    {
      key: "status",
      label: "Status",
      render: (video) => (
        <div className="flex flex-wrap gap-1.5">
          {video.isPreview && <Badge label="Preview" tone="primary" />}
          <Badge label={video.isPublished ? "Published" : "Draft"} tone={video.isPublished ? "success" : "neutral"} />
          {!video.hasStorageKey && <Badge label="No file" tone="danger" />}
        </div>
      ),
    },
    {
      key: "actions",
      label: "Actions",
      render: (video) => (
        <div className="flex items-center gap-2">
          {video.videoUrl && (
            <Popover
              align="end"
              trigger={
                <span
                  aria-label="Preview video"
                  className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--admin-border)] text-[var(--admin-text-secondary)] transition-colors hover:bg-white/5 hover:text-white"
                >
                  <Eye size={14} />
                </span>
              }
            >
              <video src={video.videoUrl} controls className="aspect-video w-full rounded-xl bg-black" />
            </Popover>
          )}

          <button
            type="button"
            onClick={() => requestReplace(video.id)}
            disabled={replacing}
            aria-label="Replace video file"
            className="rounded-lg border border-[var(--admin-border)] p-1.5 text-[var(--admin-text-secondary)] transition-colors hover:bg-white/5 hover:text-white disabled:opacity-40"
          >
            <RefreshCw size={14} />
          </button>

          <button
            type="button"
            onClick={() => onTogglePublished(video)}
            className="rounded-lg border border-[var(--admin-border)] px-2.5 py-1.5 text-xs font-semibold text-[var(--admin-text-secondary)] transition-colors hover:bg-white/5 hover:text-white"
          >
            {video.isPublished ? "Unpublish" : "Publish"}
          </button>
          <button
            type="button"
            onClick={() => onDelete(video.id)}
            aria-label="Delete video"
            className="rounded-lg border border-[var(--admin-border)] p-1.5 text-[var(--admin-text-secondary)] transition-colors hover:border-[var(--admin-danger)]/40 hover:text-[var(--admin-danger)]"
          >
            <Trash2 size={14} />
          </button>
        </div>
      ),
    },
  ];

  return (
    <>
      <input
        ref={replaceInputRef}
        type="file"
        accept={ACCEPTED_TYPES.join(",")}
        className="hidden"
        onChange={(event) => {
          handleReplaceFileSelected(event.target.files?.[0] ?? null);
          event.target.value = "";
        }}
      />
      <DataTable
        columns={columns}
        rows={videos}
        getRowKey={(video) => video.id}
        loading={loading}
        emptyLabel="No videos uploaded yet."
        minWidth="720px"
      />
    </>
  );
}
