"use client";

import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Play, RefreshCw, Trash2, Upload } from "lucide-react";

import { AdminButton, AdminCard, AdminLabel, AdminSelect } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import {
  deleteVizuMultilevelHoerenAudio,
  getVizuMultilevelHoerenAudioPreviewUrl,
  listVizuMultilevelHoerenAudio,
  replaceVizuMultilevelHoerenAudio,
  uploadVizuMultilevelHoerenAudio,
} from "@/features/admin/vizu-multilevel/services/vizu-multilevel-admin-service";
import type { VizuMultilevelHoerenAudioSlot } from "@/features/admin/vizu-multilevel/types/vizu-multilevel-admin.types";

const QUERY_KEY = ["vizu-multilevel-admin-hoeren-audio"];
const AUFGABEN = [1, 2, 3, 4, 5];

function errorMessage(error: unknown): string {
  const data = (error as { response?: { data?: { message?: unknown } } }).response?.data;
  return typeof data?.message === "string" ? data.message : "Upload fehlgeschlagen. Bitte Datei prüfen.";
}

function formatDuration(seconds: number | null): string {
  if (seconds === null) return "—";
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

/** Reads the duration from the file itself (best effort — null if the
 * browser cannot decode it). */
function readDuration(file: File): Promise<number | null> {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const audio = new Audio();
    const done = (value: number | null) => {
      URL.revokeObjectURL(url);
      resolve(value);
    };
    audio.preload = "metadata";
    audio.onloadedmetadata = () => done(Number.isFinite(audio.duration) ? Math.round(audio.duration) : null);
    audio.onerror = () => done(null);
    audio.src = url;
  });
}

function AudioSlotRow({ slot }: { slot: VizuMultilevelHoerenAudioSlot }) {
  const queryClient = useQueryClient();
  const replaceInput = useRef<HTMLInputElement>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: QUERY_KEY });

  const previewMutation = useMutation({
    mutationFn: () => getVizuMultilevelHoerenAudioPreviewUrl(slot.audio_id!),
    onSuccess: (url) => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(url);
    },
    onError: () => setError("Vorschau konnte nicht geladen werden."),
  });

  const replaceMutation = useMutation({
    mutationFn: async (file: File) => replaceVizuMultilevelHoerenAudio(slot.audio_id!, file, await readDuration(file)),
    onSuccess: () => {
      setError(null);
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
      invalidate();
    },
    onError: (e) => setError(errorMessage(e)),
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteVizuMultilevelHoerenAudio(slot.audio_id!),
    onSuccess: () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
      setConfirmDelete(false);
      invalidate();
    },
  });

  return (
    <AdminCard>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-[var(--admin-text-primary)]">Aufgabe {slot.aufgabe_number}</p>
          {slot.has_audio ? (
            <p className="mt-0.5 text-xs text-[var(--admin-text-muted)]">
              Audio: <span className="font-medium text-[var(--admin-text-secondary)]">{slot.file_name}</span> · Dauer{" "}
              {formatDuration(slot.duration_seconds)}
            </p>
          ) : (
            <p className="mt-0.5 text-xs text-[var(--admin-warning,#f59e0b)]">Noch kein Audio hochgeladen</p>
          )}
        </div>
        <span
          className={
            slot.has_audio
              ? "rounded-full bg-[var(--admin-success,#22c55e)]/15 px-2 py-0.5 text-[10px] font-semibold text-[var(--admin-success,#22c55e)]"
              : "rounded-full bg-[var(--admin-text-muted)]/15 px-2 py-0.5 text-[10px] font-semibold text-[var(--admin-text-muted)]"
          }
        >
          {slot.has_audio ? "Aktiv" : "Kein Audio vorhanden"}
        </span>
      </div>

      {slot.has_audio && (
        <div className="mt-3 space-y-3">
          <div className="flex flex-wrap gap-1.5">
            <AdminButton size="sm" variant="secondary" onClick={() => previewMutation.mutate()} disabled={previewMutation.isPending}>
              <Play size={13} />
              {previewMutation.isPending ? "Wird geladen..." : "Preview"}
            </AdminButton>
            <AdminButton size="sm" variant="secondary" onClick={() => replaceInput.current?.click()} disabled={replaceMutation.isPending}>
              <RefreshCw size={13} />
              {replaceMutation.isPending ? "Wird ersetzt..." : "Ersetzen"}
            </AdminButton>
            <AdminButton size="sm" variant="ghost" onClick={() => setConfirmDelete(true)}>
              <Trash2 size={13} />
              Löschen
            </AdminButton>
            <input
              ref={replaceInput}
              type="file"
              accept="audio/*"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) replaceMutation.mutate(file);
                e.target.value = "";
              }}
            />
          </div>
          {previewUrl && <audio controls autoPlay src={previewUrl} className="h-9 w-full" />}
        </div>
      )}

      {error && <p className="mt-2 text-xs text-[var(--admin-danger)]">{error}</p>}

      <ConfirmDialog
        open={confirmDelete}
        onOpenChange={setConfirmDelete}
        title="Audio löschen"
        description={`Möchten Sie das Audio für Aufgabe ${slot.aufgabe_number} wirklich löschen? Die Tests bleiben erhalten.`}
        onConfirm={() => deleteMutation.mutate()}
        isPending={deleteMutation.isPending}
      />
    </AdminCard>
  );
}

/** VIZU-Multilevel → Hören → Audio: the admin explicitly picks the Aufgabe
 * (1-5) and uploads its audio; each Aufgabe holds exactly one audio, which
 * is stored in protected storage and streamed only to authorised users. */
export default function VizuMultilevelHoerenAudioManager() {
  const queryClient = useQueryClient();
  const fileInput = useRef<HTMLInputElement>(null);
  const [aufgabe, setAufgabe] = useState(1);
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  const { data: slots, isLoading } = useQuery({ queryKey: QUERY_KEY, queryFn: listVizuMultilevelHoerenAudio });

  const uploadMutation = useMutation({
    mutationFn: async () => uploadVizuMultilevelHoerenAudio(aufgabe, file!, await readDuration(file!)),
    onSuccess: () => {
      setMessage({ ok: true, text: `Audio für Aufgabe ${aufgabe} wurde hochgeladen.` });
      setFile(null);
      if (fileInput.current) fileInput.current.value = "";
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
    onError: (e) => setMessage({ ok: false, text: errorMessage(e) }),
  });

  return (
    <div className="space-y-4">
      <AdminCard>
        <h3 className="text-sm font-semibold text-[var(--admin-text-primary)]">HÖREN AUDIO</h3>
        <p className="mt-1 text-xs text-[var(--admin-text-secondary)]">
          Wähle die Aufgabe und lade die passende Audio-Datei hoch (MP3, WAV, M4A, WebM, OGG). Ein erneuter Upload für dieselbe
          Aufgabe ersetzt das vorhandene Audio.
        </p>
        <div className="mt-4 grid gap-4 sm:grid-cols-[160px_1fr_auto] sm:items-end">
          <div>
            <AdminLabel>Aufgabe auswählen</AdminLabel>
            <AdminSelect value={aufgabe} onChange={(e) => setAufgabe(Number(e.target.value))}>
              {AUFGABEN.map((n) => (
                <option key={n} value={n}>
                  Aufgabe {n}
                </option>
              ))}
            </AdminSelect>
          </div>
          <div>
            <AdminLabel>Audio-Datei</AdminLabel>
            <input
              ref={fileInput}
              type="file"
              accept="audio/*"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="w-full text-sm text-[var(--admin-text-secondary)]"
            />
          </div>
          <AdminButton onClick={() => uploadMutation.mutate()} disabled={!file || uploadMutation.isPending}>
            <Upload size={15} />
            {uploadMutation.isPending ? "Wird hochgeladen..." : "Audio hochladen"}
          </AdminButton>
        </div>
        {message && (
          <p className={`mt-3 text-sm ${message.ok ? "text-[var(--admin-success,#22c55e)]" : "text-[var(--admin-danger)]"}`}>{message.text}</p>
        )}
      </AdminCard>

      {isLoading && (
        <div className="flex h-24 items-center justify-center">
          <Loader2 size={20} className="animate-spin text-[var(--admin-primary)]" />
        </div>
      )}
      <div className="grid gap-4 lg:grid-cols-2">
        {slots?.map((slot) => <AudioSlotRow key={slot.aufgabe_number} slot={slot} />)}
      </div>
    </div>
  );
}
