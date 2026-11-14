"use client";

import { useEffect, useRef, useState, type PointerEvent as ReactPointerEvent } from "react";
import { Check, Loader2, Pause, Play, Scissors, Undo2 } from "lucide-react";

import { AdminButton, AdminInput } from "@/components/admin/admin-ui";
import FormDialog from "@/components/admin/form-dialog";
import {
  audioErrorMessage, getAudioFileBlob, trimAudioFile, uploadAudioOriginal, type AudioFileInfo,
} from "@/features/admin/services/audio-files-service";

import { clampRange, formatMs, MIN_TRIM_MS, parseTime, peaks } from "./audio-trim-time";

const BUCKETS = 160;
const DECODE_MAX_BYTES = 40 * 1024 * 1024; // larger files get a plain timeline (decoding would stall the tab)

function size(bytes: number) {
  const mb = bytes / 1048576;
  return mb >= 1 ? `${mb.toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

interface Props {
  /** the chosen audio file; the dialog is open while it is set (use a `key` per file) */
  file: File;
  title: string;
  /** "Übernehmen" label of the parent flow, e.g. "In Slot speichern" */
  applyLabel?: string;
  onCancel: () => void;
  /** called with the file to use: the trimmed cut, or the original when it is used uncut */
  onDone: (audio: AudioFileInfo) => void | Promise<void>;
  /** the stored ORIGINAL of `file` (re-trimming a slot): nothing is uploaded again */
  existing?: AudioFileInfo;
}

/** Reusable audio upload + trim dialog (Media Management Hören slots and Multilevel Audio). The file is uploaded to
 * the central audio service as an ORIGINAL (kept), the admin picks start / end on the waveform or by time, previews
 * the cut in the browser, the server cuts it with ffmpeg into a NEW file (original untouched), the result is played
 * back and then applied — or the original is used as it is. */
export default function AudioTrimmerDialog({ file, title, applyLabel = "Übernehmen", onCancel, onDone, existing }: Props) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const started = useRef(!!existing);
  const box = useRef<HTMLDivElement>(null);
  const [original, setOriginal] = useState<AudioFileInfo | null>(existing ?? null);
  const [uploadPct, setUploadPct] = useState(0);
  const [duration, setDuration] = useState(0);
  const [range, setRange] = useState<[number, number]>([0, 0]);
  const [bars, setBars] = useState<number[] | null>(null);
  const [drag, setDrag] = useState<"start" | "end" | null>(null);
  const [drafts, setDrafts] = useState<{ start?: string; end?: string }>({});
  const [head, setHead] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [busy, setBusy] = useState<"trim" | "apply" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ info: AudioFileInfo; url: string } | null>(null);

  // the browser plays the local file (instant); the server gets its own copy as the ORIGINAL. The dialog content lives
  // in a Portal, so the <audio> element appears after the first effects: bind its source from a callback ref.
  const objectUrl = useRef<string | null>(null);
  const bindAudio = (el: HTMLAudioElement | null) => {
    audioRef.current = el;
    if (!el) return;
    if (!objectUrl.current) objectUrl.current = URL.createObjectURL(file);
    if (el.getAttribute("src") !== objectUrl.current) el.src = objectUrl.current;
  };
  useEffect(() => () => {
    if (objectUrl.current) URL.revokeObjectURL(objectUrl.current);
    objectUrl.current = null;
  }, []);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    uploadAudioOriginal(file, setUploadPct)
      .then(setOriginal)
      .catch((err) => setError(audioErrorMessage(err, "Upload fehlgeschlagen. Bitte erneut versuchen.")));
  }, [file]);

  useEffect(() => {
    if (file.size > DECODE_MAX_BYTES) return;
    let cancelled = false;
    (async () => {
      try {
        const context = new AudioContext();
        const decoded = await context.decodeAudioData(await file.arrayBuffer());
        void context.close();
        if (!cancelled) setBars(peaks(decoded.getChannelData(0), BUCKETS));
      } catch {
        /* no waveform for this file: the timeline still works */
      }
    })();
    return () => { cancelled = true; };
  }, [file]);

  useEffect(() => () => { if (result) URL.revokeObjectURL(result.url); }, [result]);

  const length = Math.max(0, range[1] - range[0]);
  const toRatio = (ms: number) => (duration ? (ms / duration) * 100 : 0);

  function onMeta() {
    const ms = Math.round((audioRef.current?.duration ?? 0) * 1000);
    if (Number.isFinite(ms) && ms > 0) {
      setDuration(ms);
      setRange([0, ms]);
    }
  }

  function setBoth(start: number, end: number, moved: "start" | "end") {
    setRange(clampRange(start, end, duration, moved));
    setResult(null);
  }

  function moveTo(clientX: number, handle: "start" | "end") {
    const rect = box.current?.getBoundingClientRect();
    if (!rect || !duration) return;
    const ms = Math.round(((clientX - rect.left) / rect.width) * duration);
    if (handle === "start") setBoth(ms, range[1], "start");
    else setBoth(range[0], ms, "end");
  }

  function pointerDown(e: ReactPointerEvent<HTMLDivElement>) {
    const rect = box.current?.getBoundingClientRect();
    if (!rect || !duration) return;
    const ms = ((e.clientX - rect.left) / rect.width) * duration;
    const handle = Math.abs(ms - range[0]) <= Math.abs(ms - range[1]) ? "start" : "end";
    e.currentTarget.setPointerCapture(e.pointerId);
    setDrag(handle);
    moveTo(e.clientX, handle);
  }

  function commitDraft(which: "start" | "end") {
    const text = drafts[which];
    setDrafts((d) => ({ ...d, [which]: undefined }));
    if (text === undefined) return;
    const ms = parseTime(text);
    if (ms === null) return setError("Zeit nicht lesbar. Beispiel: 1:20 oder 80,5");
    setError(null);
    if (which === "start") setBoth(ms, range[1], "start");
    else setBoth(range[0], ms, "end");
  }

  function togglePreview() {
    const el = audioRef.current;
    if (!el) return;
    if (playing) {
      el.pause();
      return;
    }
    el.currentTime = range[0] / 1000;
    void el.play();
  }

  function onTime() {
    const el = audioRef.current;
    if (!el) return;
    setHead(Math.round(el.currentTime * 1000));
    if (playing && el.currentTime * 1000 >= range[1]) el.pause();
  }

  async function trim() {
    if (!original) return;
    setBusy("trim");
    setError(null);
    try {
      const info = await trimAudioFile(original.id, range[0], range[1]);
      const blob = await getAudioFileBlob(info.id);
      setResult({ info, url: URL.createObjectURL(blob) });
    } catch (err) {
      setError(audioErrorMessage(err, "Das Audio konnte nicht gekürzt werden."));
    } finally {
      setBusy(null);
    }
  }

  async function apply(audio: AudioFileInfo) {
    setBusy("apply");
    setError(null);
    try {
      await onDone(audio);
    } catch (err) {
      setError(audioErrorMessage(err, "Speichern fehlgeschlagen."));
      setBusy(null);
    }
  }

  const uploading = !original && !error;
  const ready = !!original && duration > 0;
  const cutTooShort = length < MIN_TRIM_MS;

  return (
    <FormDialog
      open
      onOpenChange={(open) => { if (!open && busy === null) onCancel(); }}
      title={title}
      description={file.name}
      size="xl"
      footer={(
        <div className="flex w-full flex-col-reverse gap-2 sm:flex-row sm:flex-wrap sm:justify-end">
          <AdminButton variant="ghost" onClick={onCancel} disabled={busy !== null} data-testid="trim-cancel">Abbrechen</AdminButton>
          <AdminButton variant="secondary" className="whitespace-normal text-center" onClick={() => original && void apply(original)} disabled={!original || busy !== null}
                       data-testid="trim-use-original">Original ohne Kürzen übernehmen</AdminButton>
          {result ? (
            <AdminButton onClick={() => void apply(result.info)} disabled={busy !== null} data-testid="trim-apply">
              {busy === "apply" ? <Loader2 size={15} className="animate-spin" /> : <Check size={15} />} {applyLabel}
            </AdminButton>
          ) : (
            <AdminButton onClick={() => void trim()} disabled={!ready || cutTooShort || busy !== null} data-testid="trim-save">
              {busy === "trim" ? <Loader2 size={15} className="animate-spin" /> : <Scissors size={15} />} Gekürztes Audio speichern
            </AdminButton>
          )}
        </div>
      )}
    >
      <div className="space-y-4" data-testid="audio-trimmer">
        <audio ref={bindAudio} controls preload="metadata" className="w-full" onLoadedMetadata={onMeta} onTimeUpdate={onTime}
               onPlay={() => setPlaying(true)} onPause={() => setPlaying(false)} onEnded={() => setPlaying(false)} data-testid="trim-player" />

        <div>
          <div
            ref={box}
            className="relative h-28 w-full touch-none select-none overflow-hidden rounded-xl bg-[var(--admin-hover)] ring-1 ring-[var(--admin-border)]"
            onPointerDown={pointerDown}
            onPointerMove={(e) => drag && moveTo(e.clientX, drag)}
            onPointerUp={() => setDrag(null)}
            onPointerCancel={() => setDrag(null)}
            data-testid="trim-waveform"
            role="group"
            aria-label="Audio-Zeitleiste: Start- und Endgriff ziehen"
          >
            <div className="absolute inset-0 flex items-center gap-px px-1">
              {(bars ?? Array.from({ length: BUCKETS }, () => 0.08)).map((v, i) => {
                const at = ((i + 0.5) / BUCKETS) * duration;
                const inside = at >= range[0] && at <= range[1];
                return <span key={i} className={`flex-1 rounded-full ${inside ? "bg-[var(--admin-primary)]" : "bg-[var(--admin-text-muted)]/40"}`}
                             style={{ height: `${Math.max(4, v * 92)}%` }} />;
              })}
            </div>
            {duration > 0 && (
              <>
                <div className="pointer-events-none absolute inset-y-0 w-0.5 bg-white/80" style={{ left: `${toRatio(head)}%` }} />
                {(["start", "end"] as const).map((h) => (
                  <div key={h} className="pointer-events-none absolute inset-y-0 flex w-4 -translate-x-1/2 items-center justify-center"
                       style={{ left: `${toRatio(h === "start" ? range[0] : range[1])}%` }} data-testid={`trim-handle-${h}`}>
                    <span className="h-full w-1 rounded bg-[var(--admin-primary)]" />
                    <span className="absolute h-8 w-3 rounded-md bg-[var(--admin-primary)] ring-2 ring-white/70" />
                  </div>
                ))}
              </>
            )}
          </div>
          <div className="mt-1 flex justify-between text-[11px] text-[var(--admin-text-muted)]">
            <span>00:00.0</span>
            <span>{bars ? "" : "Zeitleiste (keine Wellenform für diese Datei)"}</span>
            <span>{formatMs(duration)}</span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <label className="text-xs font-semibold text-[var(--admin-text-secondary)]">Start
            <AdminInput className="mt-1" inputMode="decimal" value={drafts.start ?? formatMs(range[0])} disabled={!duration}
                        onChange={(e) => setDrafts((d) => ({ ...d, start: e.target.value }))} onBlur={() => commitDraft("start")}
                        onKeyDown={(e) => e.key === "Enter" && commitDraft("start")} data-testid="trim-start" />
          </label>
          <label className="text-xs font-semibold text-[var(--admin-text-secondary)]">Ende
            <AdminInput className="mt-1" inputMode="decimal" value={drafts.end ?? formatMs(range[1])} disabled={!duration}
                        onChange={(e) => setDrafts((d) => ({ ...d, end: e.target.value }))} onBlur={() => commitDraft("end")}
                        onKeyDown={(e) => e.key === "Enter" && commitDraft("end")} data-testid="trim-end" />
          </label>
          <div className="text-xs font-semibold text-[var(--admin-text-secondary)]">Länge
            <p className="mt-1 flex h-10 items-center text-sm text-[var(--admin-text-primary)]" data-testid="trim-length">{formatMs(length)}</p>
          </div>
          <div className="flex items-end">
            <AdminButton variant="secondary" className="w-full" onClick={togglePreview} disabled={!ready || cutTooShort} data-testid="trim-preview">
              {playing ? <Pause size={15} /> : <Play size={15} />} Ausschnitt anhören
            </AdminButton>
          </div>
        </div>

        <div className="text-xs" data-testid="trim-original-status">
          {uploading && (
            <div>
              <div className="mb-1 flex items-center gap-2 text-[var(--admin-text-secondary)]"><Loader2 size={13} className="animate-spin" /> Original wird hochgeladen … {uploadPct}%</div>
              <div className="h-1.5 overflow-hidden rounded bg-[var(--admin-hover)]" data-testid="trim-progress">
                <div className="h-full bg-[var(--admin-primary)] transition-all" style={{ width: `${uploadPct}%` }} />
              </div>
            </div>
          )}
          {original && <p className="text-[var(--admin-text-muted)]">Original gespeichert ({size(original.size_bytes)}, {formatMs(original.duration_ms ?? duration)}) — bleibt immer erhalten.</p>}
        </div>

        {busy === "trim" && <p className="flex items-center gap-2 text-sm text-[var(--admin-text-secondary)]" data-testid="trim-busy"><Loader2 size={14} className="animate-spin" /> Audio wird gekürzt …</p>}

        {result && (
          <div className="rounded-xl bg-[var(--admin-hover)] p-3" data-testid="trim-result">
            <p className="mb-2 flex items-center justify-between text-sm font-semibold text-[var(--admin-text-primary)]">
              Gekürztes Audio · {formatMs(result.info.duration_ms ?? 0)} · {size(result.info.size_bytes)}
              <AdminButton size="sm" variant="ghost" onClick={() => setResult(null)} disabled={busy !== null} data-testid="trim-redo"><Undo2 size={13} /> Neu kürzen</AdminButton>
            </p>
            <audio controls src={result.url} className="w-full" data-testid="trim-result-player" />
          </div>
        )}

        {error && <p role="alert" className="rounded-lg bg-[var(--admin-danger)]/10 px-3 py-2 text-sm text-[var(--admin-danger)]" data-testid="trim-error">{error}</p>}
      </div>
    </FormDialog>
  );
}
