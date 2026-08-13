"use client";

import { AlertCircle, CheckCircle2, Loader2, XCircle } from "lucide-react";

import type { UploadProgress } from "@/features/admin/hooks/use-upload-progress";
import { formatFileSize, formatRemainingTime, formatUploadSpeed } from "@/lib/upload-format";

import { AdminButton } from "./admin-ui";

interface Props {
  progress: UploadProgress;
  /** Shown while active, e.g. "Video wird hochgeladen" / "Audio wird hochgeladen". */
  label?: string;
  onCancel?: () => void;
  onRetry?: () => void;
}

const STATUS_COPY: Partial<Record<UploadProgress["state"], string>> = {
  SUCCESS: "Upload complete",
  ERROR: "Upload failed",
  CANCELLED: "Upload cancelled",
};

/** Real upload-progress display, driven entirely by `useUploadProgress`'s
 * state — no synthetic/fake progress. Shared by every admin file upload
 * (video, audio, thumbnails) instead of each one building its own. */
export default function UploadProgressPanel({ progress, label = "Uploading...", onCancel, onRetry }: Props) {
  const { state, loaded, total, speed, remainingSeconds, error } = progress;

  if (state === "IDLE") return null;

  const isActive = state === "UPLOAD_STARTED" || state === "UPLOADING";
  const percent = total ? Math.min(100, Math.round((loaded / total) * 100)) : null;

  return (
    <div className="rounded-xl bg-[var(--admin-card)] p-4 ring-1 ring-[var(--admin-border-strong)]">
      <div className="mb-2.5 flex items-center justify-between gap-3">
        <span className="flex items-center gap-1.5 text-sm font-semibold text-[var(--admin-text-primary)]">
          {isActive && <Loader2 size={14} className="animate-spin text-[var(--admin-primary)]" />}
          {state === "SUCCESS" && <CheckCircle2 size={14} className="text-[var(--admin-accent)]" />}
          {state === "ERROR" && <XCircle size={14} className="text-[var(--admin-danger)]" />}
          {state === "CANCELLED" && <AlertCircle size={14} className="text-[var(--admin-text-muted)]" />}
          {isActive ? label : STATUS_COPY[state]}
        </span>
        {percent !== null && isActive && (
          <span className="text-sm font-bold text-[var(--admin-primary)]">{percent}%</span>
        )}
      </div>

      {percent !== null ? (
        <div className="h-2 w-full overflow-hidden rounded-full bg-white/5">
          <div
            className={`h-full rounded-full transition-all duration-200 ${
              state === "ERROR"
                ? "bg-[var(--admin-danger)]"
                : state === "SUCCESS"
                  ? "bg-[var(--admin-accent)]"
                  : "bg-[var(--admin-primary)]"
            }`}
            style={{ width: `${percent}%` }}
          />
        </div>
      ) : (
        isActive && <p className="text-xs text-[var(--admin-text-muted)]">{formatFileSize(loaded)} uploaded</p>
      )}

      <div className="mt-2 flex flex-wrap items-center justify-between gap-x-3 gap-y-1 text-xs text-[var(--admin-text-muted)]">
        <span>{total !== null ? `${formatFileSize(loaded)} / ${formatFileSize(total)}` : formatFileSize(loaded)}</span>
        {isActive && speed !== null && (
          <span>
            {formatUploadSpeed(speed)}
            {total !== null && remainingSeconds !== null && ` · ${formatRemainingTime(remainingSeconds)} remaining`}
          </span>
        )}
      </div>

      {state === "ERROR" && error && <p className="mt-2 text-xs text-[var(--admin-danger)]">{error}</p>}

      {(isActive && onCancel) || (state === "ERROR" && (onRetry || onCancel)) ? (
        <div className="mt-3 flex justify-end gap-2">
          {state === "ERROR" && onRetry && (
            <AdminButton type="button" variant="secondary" size="sm" onClick={onRetry}>
              Retry
            </AdminButton>
          )}
          {onCancel && (
            <AdminButton type="button" variant="ghost" size="sm" onClick={onCancel}>
              Abbrechen
            </AdminButton>
          )}
        </div>
      ) : null}
    </div>
  );
}
