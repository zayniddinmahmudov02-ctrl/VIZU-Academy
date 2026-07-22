"use client";

import { useRef, useState } from "react";
import type { DragEvent } from "react";
import { UploadCloud, Video as VideoIcon } from "lucide-react";

import { useLessons } from "@/features/lessons/hooks/use-lessons";
import type { UploadVideoInput } from "../types/video";

const ACCEPTED_TYPES = ["video/mp4", "video/webm", "video/quicktime"];

interface Props {
  uploading: boolean;
  uploadProgress: number;
  uploadError: string | null;
  onUpload: (input: UploadVideoInput) => Promise<unknown>;
}

export default function VideoUploadForm({ uploading, uploadProgress, uploadError, onUpload }: Props) {
  const { lessons, loading: lessonsLoading } = useLessons();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [lessonId, setLessonId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [thumbnailUrl, setThumbnailUrl] = useState("");
  const [orderIndex, setOrderIndex] = useState("1");
  const [isPreview, setIsPreview] = useState(false);
  const [isPublished, setIsPublished] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);

  function pickFile(candidate: File | null) {
    if (!candidate) return;
    if (!ACCEPTED_TYPES.includes(candidate.type)) {
      setFileError("Unsupported file type. Allowed: MP4, WebM, MOV.");
      return;
    }
    setFileError(null);
    setFile(candidate);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragActive(false);
    pickFile(event.dataTransfer.files?.[0] ?? null);
  }

  function resetForm() {
    setFile(null);
    setLessonId("");
    setTitle("");
    setDescription("");
    setThumbnailUrl("");
    setOrderIndex("1");
    setIsPreview(false);
    setIsPublished(false);
    setFileError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  async function handleSubmit() {
    if (!file || !lessonId || !title.trim()) return;

    await onUpload({
      lessonId,
      title: title.trim(),
      description: description.trim() || undefined,
      thumbnailUrl: thumbnailUrl.trim() || undefined,
      orderIndex: Number(orderIndex) || 1,
      isPreview,
      isPublished,
      file,
    });

    resetForm();
  }

  const canSubmit = Boolean(file && lessonId && title.trim()) && !uploading;

  return (
    <div className="admin-glass space-y-4 rounded-2xl p-6">
      <div className="flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--admin-primary)] to-[var(--admin-secondary)] text-white">
          <VideoIcon size={20} />
        </div>
        <div>
          <h2 className="text-sm font-bold text-white">Upload Video</h2>
          <p className="text-xs text-[var(--admin-text-muted)]">Streamed directly to Cloudflare R2</p>
        </div>
      </div>

      {/* Drag & drop zone */}
      <div
        onDragOver={(event) => {
          event.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed p-8 text-center transition-colors ${
          dragActive
            ? "border-[var(--admin-primary)] bg-[var(--admin-primary)]/10"
            : "border-[var(--admin-border-strong)] hover:border-[var(--admin-primary)]/50"
        }`}
      >
        <UploadCloud size={28} className="text-[var(--admin-text-muted)]" />
        <p className="text-sm font-medium text-white">
          {file ? file.name : "Drag & drop a video file, or click to browse"}
        </p>
        <p className="text-xs text-[var(--admin-text-muted)]">MP4, WebM or MOV</p>
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_TYPES.join(",")}
          className="hidden"
          onChange={(event) => pickFile(event.target.files?.[0] ?? null)}
        />
      </div>
      {fileError && <p className="text-xs text-[var(--admin-danger)]">{fileError}</p>}

      {/* Metadata */}
      <div className="grid gap-3 sm:grid-cols-2">
        <select
          value={lessonId}
          onChange={(event) => setLessonId(event.target.value)}
          disabled={lessonsLoading}
          className="rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
        >
          <option value="" className="bg-[#111827]">
            {lessonsLoading ? "Loading lessons…" : "Select lesson"}
          </option>
          {lessons.map((lesson) => (
            <option key={lesson.id} value={lesson.id} className="bg-[#111827]">
              {lesson.title}
            </option>
          ))}
        </select>

        <input
          type="number"
          min={1}
          value={orderIndex}
          onChange={(event) => setOrderIndex(event.target.value)}
          placeholder="Order"
          className="rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
        />

        <input
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="Title"
          className="rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50 sm:col-span-2"
        />

        <textarea
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="Description (optional)"
          rows={3}
          className="rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50 sm:col-span-2"
        />

        <input
          value={thumbnailUrl}
          onChange={(event) => setThumbnailUrl(event.target.value)}
          placeholder="Thumbnail URL (optional)"
          className="rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50 sm:col-span-2"
        />
      </div>

      <div className="flex flex-wrap items-center gap-5">
        <label className="flex items-center gap-2 text-sm text-[var(--admin-text-secondary)]">
          <input
            type="checkbox"
            checked={isPreview}
            onChange={(event) => setIsPreview(event.target.checked)}
            className="h-4 w-4 rounded border-[var(--admin-border)] accent-[var(--admin-primary)]"
          />
          Free preview
        </label>

        <label className="flex items-center gap-2 text-sm text-[var(--admin-text-secondary)]">
          <input
            type="checkbox"
            checked={isPublished}
            onChange={(event) => setIsPublished(event.target.checked)}
            className="h-4 w-4 rounded border-[var(--admin-border)] accent-[var(--admin-primary)]"
          />
          Publish immediately
        </label>
      </div>

      {uploading && (
        <div className="space-y-1.5">
          <div className="h-2 w-full overflow-hidden rounded-full bg-white/[0.06]">
            <div
              className="h-full rounded-full bg-[var(--admin-primary)] transition-all duration-200"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <p className="text-right text-xs text-[var(--admin-text-muted)]">{uploadProgress}%</p>
        </div>
      )}

      {uploadError && <p className="text-xs text-[var(--admin-danger)]">{uploadError}</p>}

      <button
        type="button"
        onClick={handleSubmit}
        disabled={!canSubmit}
        className="w-full rounded-xl bg-[var(--admin-primary)] py-2.5 text-sm font-semibold text-white transition-opacity disabled:opacity-40"
      >
        {uploading ? "Uploading…" : "Upload Video"}
      </button>
    </div>
  );
}
