"use client";

import { useRef, useState } from "react";
import { Music, Pause, Play, Trash2, Upload } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminSelect } from "@/components/admin/admin-ui";
import {
  deleteTaskAudio,
  getAudioBlobUrl,
  uploadTaskAudio,
} from "@/features/admin/services/assessment-service";
import type { AssessmentTask, AudioPolicy } from "@/features/admin/types/assessment.types";

const ALLOWED_AUDIO_TYPES = ["audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav", "audio/mp4", "audio/x-m4a"];
const MAX_AUDIO_SIZE_BYTES = 50 * 1024 * 1024;

interface Props {
  task: AssessmentTask;
  onPolicyChange: (policy: Partial<AudioPolicy>) => void;
  onChanged: () => void;
}

function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDuration(seconds: number | null): string {
  if (seconds == null) return "—";
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

/** Audio upload/replace/delete/preview + play & control policy — the
 * "Har bir Hören task audio bilan bog'lanishi mumkin" panel. Shown inside
 * the same generic task detail editor every other task type uses; it just
 * doesn't render for task types without an audio-relevant skill. */
export default function AudioPanel({ task, onPolicyChange, onChanged }: Props) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  async function handleFileSelected(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;

    if (!ALLOWED_AUDIO_TYPES.includes(file.type)) {
      setError("Bitte wähle eine MP3-, WAV- oder M4A-Datei.");
      return;
    }
    if (file.size > MAX_AUDIO_SIZE_BYTES) {
      setError("Die Audiodatei darf maximal 50 MB groß sein.");
      return;
    }
    setError(null);

    // The browser reads the real duration client-side (no server-side
    // audio-decoding dependency in this environment) and sends it along;
    // it's informational metadata for display, not something scoring or
    // the play-limit policy depends on.
    const duration = await new Promise<number | undefined>((resolve) => {
      const probe = document.createElement("audio");
      probe.preload = "metadata";
      probe.onloadedmetadata = () => resolve(probe.duration || undefined);
      probe.onerror = () => resolve(undefined);
      probe.src = URL.createObjectURL(file);
    });

    setUploading(true);
    try {
      await uploadTaskAudio(task.id, file, duration);
      // A replace invalidates any cached preview of the old file.
      setPreviewUrl(null);
      setPlaying(false);
      onChanged();
    } catch {
      setError("Hochladen fehlgeschlagen.");
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete() {
    setUploading(true);
    try {
      await deleteTaskAudio(task.id);
      setPreviewUrl(null);
      setPlaying(false);
      onChanged();
    } finally {
      setUploading(false);
    }
  }

  async function togglePreview() {
    if (playing) {
      audioRef.current?.pause();
      setPlaying(false);
      return;
    }
    if (!previewUrl) {
      const url = await getAudioBlobUrl(task.id);
      setPreviewUrl(url);
      requestAnimationFrame(() => audioRef.current?.play());
    } else {
      audioRef.current?.play();
    }
    setPlaying(true);
  }

  return (
    <div className="space-y-3 rounded-xl bg-white/[0.02] p-4 ring-1 ring-[var(--admin-border)]">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase text-[var(--admin-text-muted)]">
        <Music size={13} />
        Audio
      </div>

      {error && <p className="text-xs text-[var(--admin-danger)]">{error}</p>}

      <input
        ref={fileInputRef}
        type="file"
        accept={ALLOWED_AUDIO_TYPES.join(",")}
        className="hidden"
        onChange={handleFileSelected}
      />

      {task.audio ? (
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={togglePreview}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--admin-primary)] text-white"
            aria-label={playing ? "Pause" : "Vorschau abspielen"}
          >
            {playing ? <Pause size={14} /> : <Play size={14} />}
          </button>
          <div className="text-xs text-[var(--admin-text-secondary)]">
            <p className="font-medium text-[var(--admin-text-primary)]">{task.audio.filename}</p>
            <p className="text-[var(--admin-text-muted)]">
              {task.audio.format.toUpperCase()} · {formatDuration(task.audio.duration_seconds)} ·{" "}
              {formatSize(task.audio.file_size_bytes)}
            </p>
          </div>
          {previewUrl && (
            <audio
              ref={audioRef}
              src={previewUrl}
              onEnded={() => setPlaying(false)}
              className="hidden"
            />
          )}
          <div className="ml-auto flex gap-2">
            <AdminButton size="sm" variant="secondary" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
              <Upload size={13} />
              Ersetzen
            </AdminButton>
            <AdminButton size="sm" variant="ghost" onClick={handleDelete} disabled={uploading}>
              <Trash2 size={13} />
            </AdminButton>
          </div>
        </div>
      ) : (
        <AdminButton size="sm" variant="secondary" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
          <Upload size={13} />
          {uploading ? "Wird hochgeladen..." : "Audio hochladen (MP3, WAV, M4A)"}
        </AdminButton>
      )}

      <div className="grid grid-cols-2 gap-3 border-t border-[var(--admin-border)] pt-3 sm:grid-cols-4">
        <div>
          <label className="mb-1 block text-[10px] font-medium uppercase text-[var(--admin-text-muted)]">
            Abspielrichtlinie
          </label>
          <AdminSelect
            value={task.audio_play_limit ?? "unlimited"}
            onChange={(e) =>
              onPolicyChange({ audio_play_limit: e.target.value === "unlimited" ? null : Number(e.target.value) })
            }
            className="h-8 text-xs"
          >
            <option value="1">Einmal hören</option>
            <option value="2">Zweimal hören</option>
            <option value="unlimited">Unbegrenzt hören</option>
          </AdminSelect>
        </div>

        <PolicyToggle
          label="Pause erlauben"
          checked={task.allow_pause}
          onChange={(v) => onPolicyChange({ allow_pause: v })}
        />
        <PolicyToggle
          label="Spulen erlauben"
          checked={task.allow_seek}
          onChange={(v) => onPolicyChange({ allow_seek: v })}
        />
        <PolicyToggle
          label="Wiederholen erlauben"
          checked={task.allow_replay}
          onChange={(v) => onPolicyChange({ allow_replay: v })}
        />
        <PolicyToggle
          label="Geschwindigkeit ändern"
          checked={task.allow_speed_change}
          onChange={(v) => onPolicyChange({ allow_speed_change: v })}
        />
      </div>
    </div>
  );
}

function PolicyToggle({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="flex cursor-pointer items-center gap-2 pt-4">
      <AdminCheckbox checked={checked} onCheckedChange={onChange} />
      <span className="text-xs text-[var(--admin-text-secondary)]">{label}</span>
    </label>
  );
}
