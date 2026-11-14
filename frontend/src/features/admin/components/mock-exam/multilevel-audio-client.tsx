"use client";

import { useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Loader2, Play, Scissors, Trash2, Upload } from "lucide-react";

import { AdminButton, AdminCard, AdminPageHeader } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import AudioTrimmerDialog from "@/features/admin/components/audio/audio-trimmer-dialog";
import { formatMs } from "@/features/admin/components/audio/audio-trim-time";
import {
  audioErrorMessage, deleteMultilevelSlotAudio, getAudioFileBlob, getMultilevelAudio, getMultilevelSlotBlob, setMultilevelSlotAudio,
  type AudioFileInfo, type MultilevelAudioSlot, type SlotStatus,
} from "@/features/admin/services/audio-files-service";

const ACCEPT = ".mp3,.wav,.m4a,audio/mpeg,audio/wav,audio/x-wav,audio/mp4,audio/x-m4a";
const AUDIO_MAX = 100 * 1024 * 1024;
const STATUS: Record<SlotStatus, { text: string; tone: string }> = {
  ok: { text: "Audio vorhanden", tone: "text-[var(--admin-success)]" },
  missing: { text: "Kein Audio", tone: "text-[var(--admin-text-muted)]" },
  file_missing: { text: "Datei fehlt auf dem Server", tone: "text-[var(--admin-warning)]" },
  external: { text: "Externer Link (alt)", tone: "text-[var(--admin-text-secondary)]" },
};

function size(bytes: number) {
  const mb = bytes / 1048576;
  return mb >= 1 ? `${mb.toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

interface Trimming {
  slot: MultilevelAudioSlot;
  file: File;
  existing?: AudioFileInfo;
}

/** Admin → Vorbereitung → Multilevel Audio: one slot per Hören Teil ("Aufgabe") of every Multilevel Modelltest. An
 * upload / replacement / cut plays in exactly that exam task at once (the exam reads the slot's file); a deleted audio
 * leaves the task without audio (a published test goes back to Entwurf). Questions and scoring are never touched. */
export default function MultilevelAudioClient() {
  const queryClient = useQueryClient();
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["multilevel-audio"], queryFn: getMultilevelAudio });
  const input = useRef<HTMLInputElement>(null);
  const target = useRef<MultilevelAudioSlot | null>(null);
  const [trimming, setTrimming] = useState<Trimming | null>(null);
  const [deleting, setDeleting] = useState<MultilevelAudioSlot | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [playing, setPlaying] = useState<{ id: string; url: string } | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["multilevel-audio"] });

  function pick(slot: MultilevelAudioSlot) {
    target.current = slot;
    input.current?.click();
  }

  function onFile(file: File | undefined) {
    if (input.current) input.current.value = "";
    const slot = target.current;
    if (!file || !slot) return;
    if (!/\.(mp3|wav|m4a)$/i.test(file.name)) return setMsg({ ok: false, text: "Nur MP3, WAV oder M4A." });
    if (file.size > AUDIO_MAX) return setMsg({ ok: false, text: "Die Datei ist größer als 100 MB." });
    setMsg(null);
    setTrimming({ slot, file });
  }

  async function retrim(slot: MultilevelAudioSlot) {
    const source = slot.original ?? slot.audio;
    if (!source) return;
    setBusy(slot.content_id);
    setMsg(null);
    try {
      const blob = await getAudioFileBlob(source.id);
      setTrimming({ slot, file: new File([blob], source.original_name ?? "audio", { type: source.content_type }), existing: source });
    } catch (err) {
      setMsg({ ok: false, text: audioErrorMessage(err, "Audio konnte nicht geladen werden.") });
    } finally {
      setBusy(null);
    }
  }

  async function play(slot: MultilevelAudioSlot) {
    if (playing) URL.revokeObjectURL(playing.url);
    setPlaying(null);
    try {
      setPlaying({ id: slot.content_id, url: URL.createObjectURL(await getMultilevelSlotBlob(slot.content_id)) });
    } catch (err) {
      setMsg({ ok: false, text: audioErrorMessage(err, "Audio konnte nicht geladen werden.") });
    }
  }

  async function remove() {
    const slot = deleting;
    if (!slot) return;
    setBusy(slot.content_id);
    try {
      const out = await deleteMultilevelSlotAudio(slot.content_id);
      setMsg({ ok: true, text: out.test_unpublished ? "Audio entfernt. Der Modelltest war veröffentlicht und ist wieder ein Entwurf." : "Audio entfernt." });
      if (playing?.id === slot.content_id) setPlaying(null);
      await refresh();
    } catch (err) {
      setMsg({ ok: false, text: audioErrorMessage(err, "Löschen fehlgeschlagen.") });
    } finally {
      setBusy(null);
      setDeleting(null);
    }
  }

  return (
    <div className="space-y-6" data-testid="multilevel-audio">
      <AdminPageHeader
        title="Multilevel Audio"
        description="Hören-Audio der Multilevel Modelltests: pro Aufgabe hochladen, kürzen, anhören, ersetzen oder löschen. Das Audio wird sofort in der jeweiligen Prüfungsaufgabe abgespielt; Fragen, Lösungen und Bewertung bleiben unverändert."
        action={data ? <span className="text-sm font-semibold text-[var(--admin-text-secondary)]" data-testid="ml-audio-summary">{data.with_audio} / {data.total} Aufgaben mit Audio</span> : undefined}
      />
      <input ref={input} type="file" accept={ACCEPT} className="hidden" onChange={(e) => onFile(e.target.files?.[0])} data-testid="ml-audio-file" />

      {msg && <p role="status" className={`rounded-lg px-3 py-2 text-sm ${msg.ok ? "bg-[var(--admin-success)]/10 text-[var(--admin-success)]" : "bg-[var(--admin-danger)]/10 text-[var(--admin-danger)]"}`} data-testid="ml-audio-msg">{msg.text}</p>}
      {isLoading && <div className="flex justify-center py-10"><Loader2 className="animate-spin text-[var(--admin-primary)]" /></div>}
      {error && (
        <AdminCard><p className="text-sm text-[var(--admin-danger)]">Multilevel Audio konnte nicht geladen werden. <button className="underline" onClick={() => void refetch()}>Erneut versuchen</button></p></AdminCard>
      )}
      {data && data.tests.length === 0 && <AdminCard><p className="text-sm text-[var(--admin-text-muted)]">Level „{data.level}“ hat noch keine Modelltests.</p></AdminCard>}

      {data?.tests.map((test) => (
        <AdminCard key={test.model_test_id}>
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-sm font-semibold text-[var(--admin-text-primary)]">{test.title}</h2>
            <span className={`text-xs font-semibold ${test.status === "PUBLISHED" ? "text-[var(--admin-accent)]" : "text-[var(--admin-text-muted)]"}`}>
              {test.status === "PUBLISHED" ? "Veröffentlicht" : "Entwurf"}
            </span>
          </div>
          {test.slots.length === 0 ? (
            <p className="text-sm text-[var(--admin-text-muted)]" data-testid="ml-audio-no-slots">Noch keine Hören-Aufgaben in diesem Modelltest.</p>
          ) : (
            <div className="space-y-2">
              {test.slots.map((s) => {
                const st = STATUS[s.status];
                const has = s.status === "ok" || s.status === "file_missing";
                return (
                  <div key={s.content_id} className="rounded-xl bg-[var(--admin-hover)] p-2.5" data-testid="ml-audio-slot" data-slot={s.content_id} data-status={s.status} data-aufgabe={s.aufgabe_number}>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
                      <span className="min-w-[9rem] font-semibold text-[var(--admin-text-primary)]">Aufgabe {s.aufgabe_number} <span className="font-normal text-[var(--admin-text-muted)]">· {s.title}</span></span>
                      <span className={`text-xs ${st.tone}`} data-testid="ml-audio-status">
                        {s.status === "file_missing" && <AlertTriangle size={11} className="mr-1 inline" />}{st.text}
                      </span>
                      {s.audio && <span className="text-xs text-[var(--admin-text-secondary)]" data-testid="ml-audio-meta">
                        {s.duration_ms ? formatMs(s.duration_ms) : "—"} · {size(s.audio.size_bytes)}{s.audio.kind === "TRIMMED" ? " · gekürzt" : ""}
                      </span>}
                      <span className="ml-auto flex flex-wrap gap-1">
                        <AdminButton size="sm" variant="secondary" disabled={s.status !== "ok"} onClick={() => void play(s)} title="Anhören" aria-label={`Aufgabe ${s.aufgabe_number} anhören`} data-testid="ml-audio-play"><Play size={13} /></AdminButton>
                        <AdminButton size="sm" variant="secondary" disabled={busy !== null} onClick={() => pick(s)} title={has ? "Audio ersetzen" : "Audio hochladen"}
                                     aria-label={`Aufgabe ${s.aufgabe_number} ${has ? "ersetzen" : "hochladen"}`} data-testid="ml-audio-upload"><Upload size={13} /></AdminButton>
                        <AdminButton size="sm" variant="secondary" disabled={busy !== null || s.status !== "ok"} onClick={() => void retrim(s)} title="Audio kürzen"
                                     aria-label={`Aufgabe ${s.aufgabe_number} kürzen`} data-testid="ml-audio-trim">
                          {busy === s.content_id ? <Loader2 size={13} className="animate-spin" /> : <Scissors size={13} />}
                        </AdminButton>
                        <AdminButton size="sm" variant="danger" disabled={busy !== null || s.status === "missing"} onClick={() => setDeleting(s)} title="Audio löschen"
                                     aria-label={`Aufgabe ${s.aufgabe_number} Audio löschen`} data-testid="ml-audio-delete"><Trash2 size={13} /></AdminButton>
                      </span>
                    </div>
                    {playing?.id === s.content_id && <audio src={playing.url} controls autoPlay className="mt-2 w-full" data-testid="ml-audio-player" />}
                  </div>
                );
              })}
            </div>
          )}
        </AdminCard>
      ))}

      {trimming && (
        <AudioTrimmerDialog
          key={`${trimming.slot.content_id}-${trimming.file.name}-${trimming.file.size}`}
          file={trimming.file}
          existing={trimming.existing}
          title={`Aufgabe ${trimming.slot.aufgabe_number} · ${trimming.slot.title}`}
          applyLabel="In Aufgabe speichern"
          onCancel={() => setTrimming(null)}
          onDone={async (audio) => {
            const slot = trimming.slot;
            await setMultilevelSlotAudio(slot.content_id, audio.id);
            setTrimming(null);
            setMsg({ ok: true, text: `Aufgabe ${slot.aufgabe_number}: Audio gespeichert — es wird jetzt im Modelltest abgespielt.` });
            if (playing?.id === slot.content_id) setPlaying(null);
            await refresh();
          }}
        />
      )}

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(open) => !open && setDeleting(null)}
        title={`Aufgabe ${deleting?.aufgabe_number ?? ""}: Audio löschen`}
        description="Die Aufgabe hat danach kein Audio mehr. Ein veröffentlichter Modelltest wird wieder zum Entwurf, weil er ohne Audio nicht bestanden werden kann. Fragen, Lösungen und Bewertung bleiben. Die hochgeladene Originaldatei bleibt gespeichert."
        isPending={!!deleting && busy === deleting.content_id}
        onConfirm={remove}
      />
    </div>
  );
}
