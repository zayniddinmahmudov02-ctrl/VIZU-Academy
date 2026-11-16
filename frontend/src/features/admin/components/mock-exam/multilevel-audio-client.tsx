"use client";

import { useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Loader2, Play, Scissors, Trash2, Upload } from "lucide-react";

import { AdminButton, AdminCard, AdminPageHeader } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import AudioTrimmerDialog from "@/features/admin/components/audio/audio-trimmer-dialog";
import { formatMs } from "@/features/admin/components/audio/audio-trim-time";
import {
  audioErrorMessage, deleteMultilevelSharedAudio, deleteMultilevelSlotAudio, getAudioFileBlob, getMultilevelAudio, getMultilevelSharedBlob, getMultilevelSlotBlob,
  setMultilevelSharedAudio, setMultilevelSlotAudio,
  type AudioFileInfo, type MultilevelAudioSlot, type SharedAudioStatus, type SlotStatus,
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

/** What an upload / cut / delete addresses: one Hören Teil ("Aufgabe") — or the ONE shared audio of a whole Modelltest (Modelltest 1). */
type Target = { slot: MultilevelAudioSlot } | { shared: SharedAudioStatus };
const idOf = (t: Target) => ("slot" in t ? t.slot.content_id : `shared:${t.shared.model_test_id}`);
const labelOf = (t: Target) => ("slot" in t ? `Aufgabe ${t.slot.aufgabe_number} · ${t.slot.title}` : `${t.shared.title} · Hören (alle Teile)`);

interface Trimming {
  target: Target;
  file: File;
  existing?: AudioFileInfo;
}

/** Admin → Vorbereitung → Multilevel Audio: one slot per Hören Teil ("Aufgabe") of every Multilevel Modelltest — except Modelltest 1, whose whole Hören section
 * plays ONE shared audio (one upload / replacement / cut for all Teile; the Teile keep their own questions). An upload / replacement / cut plays in the
 * exam at once; a deleted audio leaves the task (or the whole Hören section) without audio (a published test goes back to Entwurf). Questions, scoring and the
 * exam time are never touched — the audio length is shown for orientation only. */
export default function MultilevelAudioClient() {
  const queryClient = useQueryClient();
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["multilevel-audio"], queryFn: getMultilevelAudio });
  const input = useRef<HTMLInputElement>(null);
  const target = useRef<Target | null>(null);
  const [trimming, setTrimming] = useState<Trimming | null>(null);
  const [deleting, setDeleting] = useState<Target | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [playing, setPlaying] = useState<{ id: string; url: string } | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["multilevel-audio"] });

  function pick(t: Target) {
    target.current = t;
    input.current?.click();
  }

  function onFile(file: File | undefined) {
    if (input.current) input.current.value = "";
    const t = target.current;
    if (!file || !t) return;
    if (!/\.(mp3|wav|m4a)$/i.test(file.name)) return setMsg({ ok: false, text: "Nur MP3, WAV oder M4A." });
    if (file.size > AUDIO_MAX) return setMsg({ ok: false, text: "Die Datei ist größer als 100 MB." });
    setMsg(null);
    setTrimming({ target: t, file });
  }

  async function retrim(t: Target) {
    const current = "slot" in t ? t.slot : t.shared;
    const source = current.original ?? current.audio;
    if (!source) return;
    setBusy(idOf(t));
    setMsg(null);
    try {
      const blob = await getAudioFileBlob(source.id);
      setTrimming({ target: t, file: new File([blob], source.original_name ?? "audio", { type: source.content_type }), existing: source });
    } catch (err) {
      setMsg({ ok: false, text: audioErrorMessage(err, "Audio konnte nicht geladen werden.") });
    } finally {
      setBusy(null);
    }
  }

  async function play(t: Target) {
    if (playing) URL.revokeObjectURL(playing.url);
    setPlaying(null);
    try {
      const blob = "slot" in t ? await getMultilevelSlotBlob(t.slot.content_id) : await getMultilevelSharedBlob(t.shared.model_test_id);
      setPlaying({ id: idOf(t), url: URL.createObjectURL(blob) });
    } catch (err) {
      setMsg({ ok: false, text: audioErrorMessage(err, "Audio konnte nicht geladen werden.") });
    }
  }

  async function remove() {
    const t = deleting;
    if (!t) return;
    setBusy(idOf(t));
    try {
      const out = "slot" in t ? await deleteMultilevelSlotAudio(t.slot.content_id) : await deleteMultilevelSharedAudio(t.shared.model_test_id);
      setMsg({ ok: true, text: out.test_unpublished ? "Audio entfernt. Der Modelltest war veröffentlicht und ist wieder ein Entwurf." : "Audio entfernt." });
      if (playing?.id === idOf(t)) setPlaying(null);
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
        description="Hören-Audio der Multilevel Modelltests: pro Aufgabe hochladen, kürzen, anhören, ersetzen oder löschen — Modelltest 1 hat ein gemeinsames Audio für alle Hören-Teile. Das Audio wird sofort in der Prüfung abgespielt; Fragen, Lösungen, Prüfungszeit und Bewertung bleiben unverändert."
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
          {test.shared && <SharedRow shared={test.shared} t={{ shared: test.shared }} busy={busy} playing={playing} onPlay={play} onUpload={pick} onTrim={retrim} onDelete={setDeleting} />}
          {test.slots.length === 0 ? (
            <p className="text-sm text-[var(--admin-text-muted)]" data-testid="ml-audio-no-slots">Noch keine Hören-Aufgaben in diesem Modelltest.</p>
          ) : test.shared ? null : (
            <div className="space-y-2">
              {test.slots.map((s) => {
                const st = STATUS[s.status];
                const has = s.status === "ok" || s.status === "file_missing";
                const t: Target = { slot: s };
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
                        <AdminButton size="sm" variant="secondary" disabled={s.status !== "ok"} onClick={() => void play(t)} title="Anhören" aria-label={`Aufgabe ${s.aufgabe_number} anhören`} data-testid="ml-audio-play"><Play size={13} /></AdminButton>
                        <AdminButton size="sm" variant="secondary" disabled={busy !== null} onClick={() => pick(t)} title={has ? "Audio ersetzen" : "Audio hochladen"}
                                     aria-label={`Aufgabe ${s.aufgabe_number} ${has ? "ersetzen" : "hochladen"}`} data-testid="ml-audio-upload"><Upload size={13} /></AdminButton>
                        <AdminButton size="sm" variant="secondary" disabled={busy !== null || s.status !== "ok"} onClick={() => void retrim(t)} title="Audio kürzen"
                                     aria-label={`Aufgabe ${s.aufgabe_number} kürzen`} data-testid="ml-audio-trim">
                          {busy === s.content_id ? <Loader2 size={13} className="animate-spin" /> : <Scissors size={13} />}
                        </AdminButton>
                        <AdminButton size="sm" variant="danger" disabled={busy !== null || s.status === "missing"} onClick={() => setDeleting(t)} title="Audio löschen"
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
          key={`${idOf(trimming.target)}-${trimming.file.name}-${trimming.file.size}`}
          file={trimming.file}
          existing={trimming.existing}
          title={labelOf(trimming.target)}
          applyLabel={"slot" in trimming.target ? "In Aufgabe speichern" : "Für alle Teile speichern"}
          onCancel={() => setTrimming(null)}
          onDone={async (audio) => {
            const t = trimming.target;
            if ("slot" in t) {
              await setMultilevelSlotAudio(t.slot.content_id, audio.id);
              setMsg({ ok: true, text: `Aufgabe ${t.slot.aufgabe_number}: Audio gespeichert — es wird jetzt im Modelltest abgespielt.` });
            } else {
              await setMultilevelSharedAudio(t.shared.model_test_id, audio.id);
              setMsg({ ok: true, text: `${t.shared.title}: Audio gespeichert — alle Hören-Teile spielen es jetzt ab.` });
            }
            setTrimming(null);
            if (playing?.id === idOf(t)) setPlaying(null);
            await refresh();
          }}
        />
      )}

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(open) => !open && setDeleting(null)}
        title={deleting ? ("slot" in deleting ? `Aufgabe ${deleting.slot.aufgabe_number}: Audio löschen` : `${deleting.shared.title}: gemeinsames Audio löschen`) : ""}
        description={deleting && "shared" in deleting
          ? "Alle Hören-Teile dieses Modelltests haben danach kein Audio mehr. Ein veröffentlichter Modelltest wird wieder zum Entwurf, weil er ohne Audio nicht bestanden werden kann. Fragen, Lösungen, Prüfungszeit und Bewertung bleiben. Die hochgeladene Originaldatei bleibt gespeichert."
          : "Die Aufgabe hat danach kein Audio mehr. Ein veröffentlichter Modelltest wird wieder zum Entwurf, weil er ohne Audio nicht bestanden werden kann. Fragen, Lösungen und Bewertung bleiben. Die hochgeladene Originaldatei bleibt gespeichert."}
        isPending={!!deleting && busy === idOf(deleting)}
        onConfirm={remove}
      />
    </div>
  );
}

/** Modelltest 1: ONE audio for the whole Hören section — upload, replace, cut, listen, delete in one place; the Teile are listed with their question counts. */
function SharedRow({ shared, t, busy, playing, onPlay, onUpload, onTrim, onDelete }: {
  shared: SharedAudioStatus; t: Target; busy: string | null; playing: { id: string; url: string } | null;
  onPlay: (t: Target) => void; onUpload: (t: Target) => void; onTrim: (t: Target) => void; onDelete: (t: Target) => void;
}) {
  const st = STATUS[shared.status];
  const has = shared.status === "ok" || shared.status === "file_missing";
  const id = idOf(t);
  return (
    <div className="mb-3 space-y-2 rounded-xl bg-[var(--admin-hover)] p-3" data-testid="ml-shared" data-status={shared.status}>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
        <span className="font-semibold text-[var(--admin-text-primary)]">Gemeinsames Audio <span className="font-normal text-[var(--admin-text-muted)]">· Hören, alle Teile</span></span>
        <span className={`text-xs ${st.tone}`} data-testid="ml-shared-status">
          {shared.status === "file_missing" && <AlertTriangle size={11} className="mr-1 inline" />}{st.text}
        </span>
        {shared.audio && <span className="text-xs text-[var(--admin-text-secondary)]" data-testid="ml-shared-meta">
          Audiolänge {shared.duration_ms ? formatMs(shared.duration_ms) : "—"} · {size(shared.audio.size_bytes)}{shared.audio.kind === "TRIMMED" ? " · gekürzt" : ""}
        </span>}
        <span className="text-xs text-[var(--admin-text-muted)]" data-testid="ml-shared-minutes">Prüfungszeit Hören: {shared.exam_minutes} Min. (unabhängig von der Audiolänge)</span>
        <span className="ml-auto flex flex-wrap gap-1">
          <AdminButton size="sm" variant="secondary" disabled={shared.status !== "ok"} onClick={() => onPlay(t)} title="Anhören" aria-label="Gemeinsames Audio anhören" data-testid="ml-shared-play"><Play size={13} /></AdminButton>
          <AdminButton size="sm" variant="secondary" disabled={busy !== null} onClick={() => onUpload(t)} title={has ? "Audio ersetzen" : "Audio hochladen"}
                       aria-label={`Gemeinsames Audio ${has ? "ersetzen" : "hochladen"}`} data-testid="ml-shared-upload"><Upload size={13} /></AdminButton>
          <AdminButton size="sm" variant="secondary" disabled={busy !== null || shared.status !== "ok"} onClick={() => onTrim(t)} title="Audio kürzen" aria-label="Gemeinsames Audio kürzen" data-testid="ml-shared-trim">
            {busy === id ? <Loader2 size={13} className="animate-spin" /> : <Scissors size={13} />}
          </AdminButton>
          <AdminButton size="sm" variant="danger" disabled={busy !== null || shared.status === "missing"} onClick={() => onDelete(t)} title="Audio löschen" aria-label="Gemeinsames Audio löschen" data-testid="ml-shared-delete"><Trash2 size={13} /></AdminButton>
        </span>
      </div>
      {playing?.id === id && <audio src={playing.url} controls autoPlay className="w-full" data-testid="ml-shared-player" />}
      <ul className="grid gap-1 text-xs text-[var(--admin-text-muted)] sm:grid-cols-2" data-testid="ml-shared-teile">
        {shared.teile.map((x) => (
          <li key={x.teil_id} data-testid="ml-audio-slot" data-shared="1" data-aufgabe={x.aufgabe_number}>Aufgabe {x.aufgabe_number} · {x.title} — {x.questions} Fragen, nutzt das gemeinsame Audio</li>
        ))}
      </ul>
    </div>
  );
}
