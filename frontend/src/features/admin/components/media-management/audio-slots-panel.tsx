"use client";

import { useRef, useState } from "react";
import { AlertTriangle, Pencil, Play, Plus, Trash2, Upload, X } from "lucide-react";

import { AdminButton, AdminInput } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import {
  addAudioTrack, apiErrorMessage, clearAudioTrackFile, deleteAudioTrack, deleteListeningAudio, getAudioTrackBlobUrl, setMainAudioLabel, updateAudioTrack,
  uploadListeningAudio, type AudioSlot,
} from "@/features/admin/services/lesson-skills-admin-service";

const AUDIO_ACCEPT = ".mp3,.wav,.m4a,audio/mpeg,audio/wav,audio/x-wav,audio/mp4,audio/x-m4a";
const AUDIO_MAX = 100 * 1024 * 1024; // backend MAX_AUDIO_BYTES
const STATUS: Record<AudioSlot["file_status"], string> = { ok: "Datei vorhanden", missing: "Datei fehlt auf dem Server", external: "Externer Link", none: "Keine Datei" };

function size(bytes: number | null) {
  if (!bytes) return "—";
  const mb = bytes / 1048576;
  return mb >= 1 ? `${mb.toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

function readDuration(file: File): Promise<number | null> {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const el = document.createElement("audio");
    const done = (v: number | null) => { URL.revokeObjectURL(url); resolve(v); };
    el.preload = "metadata";
    el.onloadedmetadata = () => done(Number.isFinite(el.duration) ? Math.round(el.duration) : null);
    el.onerror = () => done(null);
    el.src = url;
  });
}

/** Every audio file of one Hören task as its own slot: the task's main audio
 * and labelled extra tracks (e.g. A1 Lektion 14 „Text von Alisa“ /
 * „Text von Alex“). Upload, replace, listen and rename per slot; the trash
 * button removes only the FILE — the slot stays for a new upload. An empty
 * extra slot can be removed with ✕. */
export default function AudioSlotsPanel({ listeningId, slots, onChanged }: { listeningId: string; slots: AudioSlot[]; onChanged: () => void | Promise<unknown> }) {
  const input = useRef<HTMLInputElement>(null);
  const pending = useRef<{ slot: string | null; label: string | null }>({ slot: null, label: null });
  const [busy, setBusy] = useState<string | null>(null);
  const [percent, setPercent] = useState<number | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [playing, setPlaying] = useState<{ id: string; url: string } | null>(null);
  const [editing, setEditing] = useState<{ id: string; label: string } | null>(null);
  const [adding, setAdding] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<{ slot: AudioSlot; mode: "file" | "slot" } | null>(null);

  async function run(id: string, action: () => Promise<unknown>, ok: string, fallback: string) {
    setBusy(id);
    setMsg(null);
    try {
      await action();
      setMsg({ ok: true, text: ok });
      await onChanged();
    } catch (err) {
      setMsg({ ok: false, text: apiErrorMessage(err, fallback) });
    } finally {
      setBusy(null);
      setPercent(null);
    }
  }

  function pick(slot: string | null, label: string | null = null) {
    pending.current = { slot, label };
    input.current?.click();
  }

  async function onFile(file: File | undefined) {
    if (input.current) input.current.value = "";
    const { slot, label } = pending.current;
    if (!file) return;
    if (!/\.(mp3|wav|m4a)$/i.test(file.name)) return setMsg({ ok: false, text: "Nur MP3, WAV oder M4A." });
    if (file.size > AUDIO_MAX) return setMsg({ ok: false, text: "Die Datei ist größer als 100 MB." });
    const duration = await readDuration(file);
    setPercent(0);
    if (slot === null) {
      await run("new", () => addAudioTrack(listeningId, label ?? "", file, duration, setPercent), `„${label}“ hochgeladen.`, "Upload fehlgeschlagen.");
      setAdding(null);
    } else if (slot === "main") {
      await run("main", () => uploadListeningAudio(listeningId, file, duration, setPercent), "Audio ersetzt.", "Upload fehlgeschlagen.");
    } else {
      await run(slot, () => updateAudioTrack(listeningId, slot, { file, durationSeconds: duration }, setPercent), "Audio ersetzt.", "Upload fehlgeschlagen.");
    }
  }

  async function play(slot: AudioSlot) {
    if (playing) URL.revokeObjectURL(playing.url);
    setPlaying(null);
    try {
      setPlaying({ id: slot.id, url: await getAudioTrackBlobUrl(listeningId, slot.id) });
    } catch (err) {
      setMsg({ ok: false, text: apiErrorMessage(err, "Audio konnte nicht geladen werden.") });
    }
  }

  async function saveLabel() {
    if (!editing) return;
    const { id, label } = editing;
    await run(id, () => (id === "main" ? setMainAudioLabel(listeningId, label.trim() || null) : updateAudioTrack(listeningId, id, { label: label.trim() })),
      "Bezeichnung gespeichert.", "Speichern fehlgeschlagen.");
    setEditing(null);
  }

  return (
    <div className="space-y-2" data-testid="audio-slots">
      <input ref={input} type="file" accept={AUDIO_ACCEPT} className="hidden" onChange={(e) => onFile(e.target.files?.[0])} data-testid="audio-slot-file" />
      {slots.map((s) => {
        const ok = s.file_status === "ok";
        return (
          <div key={s.id} className="rounded-xl bg-[var(--admin-hover)] p-2.5" data-testid="audio-slot" data-slot={s.id} data-file={s.file_status}>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
              {editing?.id === s.id ? (
                <span className="flex items-center gap-1.5">
                  <AdminInput className="h-8 w-48" value={editing.label} maxLength={120} placeholder="z. B. Audio von Alisa" autoFocus
                              onChange={(e) => setEditing({ id: s.id, label: e.target.value })} onKeyDown={(e) => e.key === "Enter" && saveLabel()} />
                  <AdminButton size="sm" onClick={saveLabel} disabled={busy === s.id}>OK</AdminButton>
                  <AdminButton size="sm" variant="ghost" onClick={() => setEditing(null)}>✕</AdminButton>
                </span>
              ) : (
                <span className="min-w-[8rem] font-semibold text-[var(--admin-text-primary)]">{s.label ?? (s.id === "main" ? "Audio" : "Audio-Spur")}</span>
              )}
              <span className="max-w-[14rem] truncate text-xs text-[var(--admin-text-secondary)]" title={s.file_name ?? ""}>{s.file_name ?? "—"}</span>
              <span className="text-xs text-[var(--admin-text-secondary)]">{size(s.size_bytes)}</span>
              {s.uploaded_at && <span className="text-xs text-[var(--admin-text-muted)]">{new Date(s.uploaded_at).toLocaleDateString("de-DE")}</span>}
              <span className={`text-xs ${ok ? "text-[var(--admin-success)]" : "text-[var(--admin-warning)]"}`}>
                {!ok && <AlertTriangle size={11} className="mr-1 inline" />}{STATUS[s.file_status]}
              </span>
              <span className="ml-auto flex flex-wrap gap-1">
                <AdminButton size="sm" variant="secondary" disabled={!ok} onClick={() => play(s)} title="Anhören" aria-label={`${s.label ?? "Audio"} anhören`}><Play size={13} /></AdminButton>
                <AdminButton size="sm" variant="secondary" disabled={busy !== null || percent !== null} onClick={() => pick(s.id)} title={ok ? "Datei ersetzen" : "Datei hochladen"}
                             aria-label={`${s.label ?? "Audio"} ${ok ? "ersetzen" : "hochladen"}`} data-testid="audio-slot-replace"><Upload size={13} /></AdminButton>
                <AdminButton size="sm" variant="secondary" disabled={busy !== null} onClick={() => setEditing({ id: s.id, label: s.label ?? "" })} title="Bezeichnung ändern"
                             aria-label="Bezeichnung ändern"><Pencil size={13} /></AdminButton>
                <AdminButton size="sm" variant="danger" disabled={busy !== null || s.file_status === "none" || s.file_status === "external"}
                             onClick={() => setDeleting({ slot: s, mode: "file" })} title="Datei entfernen (Slot bleibt)" aria-label={`${s.label ?? "Audio"}: Datei entfernen`}
                             data-testid="audio-slot-delete"><Trash2 size={13} /></AdminButton>
                {s.id !== "main" && s.file_status === "none" && (
                  <AdminButton size="sm" variant="ghost" disabled={busy !== null} onClick={() => setDeleting({ slot: s, mode: "slot" })} title="Leeren Slot entfernen"
                               aria-label={`Slot ${s.label ?? ""} entfernen`} data-testid="audio-slot-remove"><X size={13} /></AdminButton>
                )}
              </span>
            </div>
            {playing?.id === s.id && <audio src={playing.url} controls autoPlay className="mt-2 w-full" />}
          </div>
        );
      })}
      {adding !== null ? (
        <div className="flex flex-wrap items-center gap-2">
          <AdminInput className="h-8 w-56" value={adding} maxLength={120} placeholder="Bezeichnung, z. B. Audio von Alex" autoFocus onChange={(e) => setAdding(e.target.value)} />
          <AdminButton size="sm" disabled={!adding.trim() || percent !== null} onClick={() => pick(null, adding.trim())} data-testid="audio-slot-add-file"><Upload size={13} /> Datei wählen</AdminButton>
          <AdminButton size="sm" variant="ghost" onClick={() => setAdding(null)}>Abbrechen</AdminButton>
        </div>
      ) : (
        <AdminButton size="sm" variant="ghost" onClick={() => setAdding("")} disabled={busy !== null} data-testid="audio-slot-add"><Plus size={13} /> Weitere Audiodatei (Spur) hinzufügen</AdminButton>
      )}
      {percent !== null && <p className="text-xs text-[var(--admin-text-secondary)]">Wird hochgeladen … {percent}%</p>}
      {msg && <p role="status" className={`text-xs ${msg.ok ? "text-[var(--admin-success)]" : "text-[var(--admin-danger)]"}`}>{msg.text}</p>}
      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(open) => !open && setDeleting(null)}
        title={deleting?.mode === "slot" ? "Leeren Slot entfernen" : `Datei aus „${deleting?.slot.label ?? "Audio"}“ entfernen`}
        description={deleting?.mode === "slot"
          ? `Der leere Slot „${deleting?.slot.label}“ wird entfernt. Die übrigen Audiodateien und die Fragen bleiben.`
          : `Die Datei von „${deleting?.slot.label ?? "Audio"}“ wird entfernt; der Slot bleibt für eine neue Datei. Fragen und Lösungen bleiben. `
            + "Solange ein Slot leer ist, ist die Aufgabe für Lernende nicht sichtbar."}
        isPending={!!deleting && busy === deleting.slot.id}
        onConfirm={async () => {
          const d = deleting;
          if (!d) return;
          const id = d.slot.id;
          const action = d.mode === "slot" ? () => deleteAudioTrack(listeningId, id)
            : id === "main" ? () => deleteListeningAudio(listeningId) : () => clearAudioTrackFile(listeningId, id);
          await run(id, action, d.mode === "slot" ? "Slot entfernt." : "Datei entfernt — Slot bleibt.", "Löschen fehlgeschlagen.");
          setDeleting(null);
        }}
      />
    </div>
  );
}
