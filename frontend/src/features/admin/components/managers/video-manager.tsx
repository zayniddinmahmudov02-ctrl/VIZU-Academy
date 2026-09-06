"use client";

import { useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Eye, Loader2, Plus, RefreshCw, Trash2, XCircle } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminInput } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import FileUploadField from "@/components/admin/file-upload-field";
import FormDialog from "@/components/admin/form-dialog";
import UploadProgressPanel from "@/components/admin/upload-progress-panel";
import { useChunkedVideoUpload } from "@/features/admin/hooks/use-chunked-video-upload";
import {
  deleteVideo,
  listVideosByLesson,
  updateVideo,
} from "@/features/admin/services/video-service";
import type { Video } from "@/features/admin/types/content.types";

import LessonPicker from "./lesson-picker";

function readVideoDuration(file: File): Promise<number> {
  return new Promise((resolve) => {
    const video = document.createElement("video");
    video.preload = "metadata";
    video.onloadedmetadata = () => {
      URL.revokeObjectURL(video.src);
      resolve(Math.round(video.duration) || 0);
    };
    video.onerror = () => resolve(0);
    video.src = URL.createObjectURL(file);
  });
}

export default function VideoManager({ lessonId: fixedLessonId }: { lessonId?: string }) {
  const queryClient = useQueryClient();
  const [pickedLessonId, setPickedLessonId] = useState("");
  const lessonId = fixedLessonId ?? pickedLessonId;

  const { data, isLoading } = useQuery({
    queryKey: ["videos-by-lesson", lessonId],
    queryFn: () => listVideosByLesson(lessonId),
    enabled: !!lessonId,
  });

  const [uploadOpen, setUploadOpen] = useState(false);
  const [form, setForm] = useState({ title: "", description: "", is_preview: false, is_published: false });
  const [file, setFile] = useState<File | null>(null);
  const [thumbnailUrl, setThumbnailUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadProgress = useChunkedVideoUpload();

  const [replacing, setReplacing] = useState<Video | null>(null);
  const [replaceFile, setReplaceFile] = useState<File | null>(null);
  const replaceProgress = useChunkedVideoUpload();
  const [deleting, setDeleting] = useState<Video | null>(null);
  const [deletePending, setDeletePending] = useState(false);

  const uploading = uploadProgress.progress.state === "UPLOAD_STARTED" || uploadProgress.progress.state === "UPLOADING";
  const replacingUpload =
    replaceProgress.progress.state === "UPLOAD_STARTED" || replaceProgress.progress.state === "UPLOADING";

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["videos-by-lesson", lessonId] });
    queryClient.invalidateQueries({ queryKey: ["course-lessons-content-status"] });
  }

  function openUpload() {
    setForm({ title: "", description: "", is_preview: false, is_published: false });
    setFile(null);
    setThumbnailUrl(null);
    uploadProgress.reset();
    setUploadOpen(true);
  }

  async function handleUpload() {
    if (!file || !lessonId) return;
    try {
      const durationSeconds = await readVideoDuration(file);
      await uploadProgress.upload(file, {
        lessonId,
        title: form.title,
        description: form.description || undefined,
        durationSeconds,
        isPreview: form.is_preview,
        isPublished: form.is_published,
      });
      invalidate();
      setUploadOpen(false);
    } catch {
      // Progress panel already shows ERROR/CANCELLED with a Retry action —
      // retrying resumes from the last chunk that made it, it doesn't
      // restart the whole file.
    }
  }

  async function handleReplace() {
    if (!replacing || !replaceFile) return;
    try {
      const durationSeconds = await readVideoDuration(replaceFile);
      await replaceProgress.upload(replaceFile, {
        lessonId: replacing.lesson_id,
        title: replacing.title,
        durationSeconds,
        replaceVideoId: replacing.id,
      });
      invalidate();
      setReplacing(null);
      setReplaceFile(null);
    } catch {
      // Progress panel already shows ERROR/CANCELLED with a Retry action —
      // retrying resumes from the last chunk that made it, it doesn't
      // restart the whole file.
    }
  }

  async function togglePublish(video: Video) {
    await updateVideo(video.id, { is_published: !video.is_published });
    invalidate();
  }

  return (
    <div>
      {!fixedLessonId && (
        <div className="mb-4 max-w-sm">
          <LessonPicker value={pickedLessonId} onChange={setPickedLessonId} />
        </div>
      )}

      {lessonId && (
        <div className="mb-4 flex justify-end">
          <AdminButton onClick={openUpload}>
            <Plus size={16} />
            Video hochladen
          </AdminButton>
        </div>
      )}

      {!lessonId && (
        <p className="rounded-2xl bg-[var(--admin-card)] p-6 text-center text-sm text-[var(--admin-text-muted)] ring-1 ring-[var(--admin-border)]">
          Wähle eine Lektion, um Videos zu verwalten.
        </p>
      )}

      {lessonId && isLoading && (
        <div className="flex justify-center py-10">
          <Loader2 size={22} className="animate-spin text-[var(--admin-primary)]" />
        </div>
      )}

      {lessonId && !isLoading && (
        <div className="space-y-3">
          {(data ?? []).length === 0 && (
            <p className="rounded-2xl bg-[var(--admin-card)] p-6 text-center text-sm text-[var(--admin-text-muted)] ring-1 ring-[var(--admin-border)]">
              Noch kein Video für diese Lektion.
            </p>
          )}

          {(data ?? []).map((video) => (
            <div
              key={video.id}
              className="flex flex-col gap-3 rounded-2xl bg-[var(--admin-card)] p-4 ring-1 ring-[var(--admin-border)] sm:flex-row sm:items-center"
            >
              <div className="flex h-16 w-28 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-black/30">
                {video.thumbnail_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={video.thumbnail_url} alt="" loading="lazy" className="h-full w-full object-cover" />
                ) : (
                  <Eye size={18} className="text-[var(--admin-text-muted)]" />
                )}
              </div>

              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-[var(--admin-text-primary)]">
                  {video.title}
                </p>
                <p className="text-xs text-[var(--admin-text-muted)]">
                  {Math.floor(video.duration_seconds / 60)}:{String(video.duration_seconds % 60).padStart(2, "0")}
                  {video.is_preview && " · Vorschau"}
                </p>
              </div>

              <button
                onClick={() => togglePublish(video)}
                className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold transition ${
                  video.is_published
                    ? "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]"
                    : "bg-white/5 text-[var(--admin-text-muted)]"
                }`}
              >
                {video.is_published ? <CheckCircle2 size={13} /> : <XCircle size={13} />}
                {video.is_published ? "Veröffentlicht" : "Entwurf"}
              </button>

              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => {
                    setReplaceFile(null);
                    replaceProgress.reset();
                    setReplacing(video);
                  }}
                  aria-label="Video ersetzen"
                  className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--admin-text-secondary)] hover:bg-white/5 hover:text-[var(--admin-primary)]"
                >
                  <RefreshCw size={15} />
                </button>
                <button
                  onClick={() => setDeleting(video)}
                  aria-label="Video löschen"
                  className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--admin-text-secondary)] hover:bg-[var(--admin-danger)]/10 hover:text-[var(--admin-danger)]"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <FormDialog
        open={uploadOpen}
        onOpenChange={(open) => !uploading && setUploadOpen(open)}
        title="Video hochladen"
        size="lg"
        footer={
          !uploading && (
            <>
              <AdminButton variant="ghost" onClick={() => setUploadOpen(false)}>
                Abbrechen
              </AdminButton>
              <AdminButton onClick={handleUpload} disabled={!file || !form.title}>
                Hochladen
              </AdminButton>
            </>
          )
        }
      >
        <div className="space-y-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
              Titel
            </label>
            <AdminInput
              value={form.title}
              disabled={uploading}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
              Beschreibung (optional)
            </label>
            <AdminInput
              value={form.description}
              disabled={uploading}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
              Videodatei
            </label>
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*"
              disabled={uploading}
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="block w-full text-sm text-[var(--admin-text-secondary)] file:mr-3 file:rounded-lg file:border-0 file:bg-[var(--admin-primary)] file:px-3.5 file:py-2 file:text-sm file:font-semibold file:text-white"
            />
          </div>

          {uploadProgress.progress.state !== "IDLE" && (
            <UploadProgressPanel
              progress={uploadProgress.progress}
              label="Video wird hochgeladen..."
              onCancel={uploading ? uploadProgress.cancel : undefined}
              onRetry={uploadProgress.progress.state === "ERROR" ? handleUpload : undefined}
            />
          )}

          {!uploading && (
            <FileUploadField
              label="Thumbnail"
              folder="thumbnails"
              accept="image/*"
              value={thumbnailUrl}
              onChange={setThumbnailUrl}
            />
          )}

          <div className="flex items-center gap-6">
            <label className="flex cursor-pointer items-center gap-2.5">
              <AdminCheckbox
                checked={form.is_preview}
                onCheckedChange={(checked) => setForm({ ...form, is_preview: checked })}
              />
              <span className="text-sm text-[var(--admin-text-secondary)]">Kostenlose Vorschau</span>
            </label>
            <label className="flex cursor-pointer items-center gap-2.5">
              <AdminCheckbox
                checked={form.is_published}
                onCheckedChange={(checked) => setForm({ ...form, is_published: checked })}
              />
              <span className="text-sm text-[var(--admin-text-secondary)]">Veröffentlicht</span>
            </label>
          </div>
        </div>
      </FormDialog>

      <FormDialog
        open={!!replacing}
        onOpenChange={(open) => !replacingUpload && !open && setReplacing(null)}
        title="Video ersetzen"
        description="Behält Titel, Statistiken und Fortschritt der Lernenden bei."
        footer={
          !replacingUpload && (
            <>
              <AdminButton variant="ghost" onClick={() => setReplacing(null)}>
                Abbrechen
              </AdminButton>
              <AdminButton onClick={handleReplace} disabled={!replaceFile}>
                Ersetzen
              </AdminButton>
            </>
          )
        }
      >
        <div className="space-y-4">
          <input
            type="file"
            accept="video/*"
            disabled={replacingUpload}
            onChange={(e) => setReplaceFile(e.target.files?.[0] ?? null)}
            className="block w-full text-sm text-[var(--admin-text-secondary)] file:mr-3 file:rounded-lg file:border-0 file:bg-[var(--admin-primary)] file:px-3.5 file:py-2 file:text-sm file:font-semibold file:text-white"
          />

          {replaceProgress.progress.state !== "IDLE" && (
            <UploadProgressPanel
              progress={replaceProgress.progress}
              label="Video wird hochgeladen..."
              onCancel={replacingUpload ? replaceProgress.cancel : undefined}
              onRetry={replaceProgress.progress.state === "ERROR" ? handleReplace : undefined}
            />
          )}
        </div>
      </FormDialog>

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(open) => !open && setDeleting(null)}
        title="Video löschen"
        description={`"${deleting?.title}" wird dauerhaft gelöscht.`}
        isPending={deletePending}
        onConfirm={async () => {
          if (!deleting) return;
          setDeletePending(true);
          try {
            await deleteVideo(deleting.id);
            invalidate();
          } finally {
            setDeletePending(false);
            setDeleting(null);
          }
        }}
      />
    </div>
  );
}
