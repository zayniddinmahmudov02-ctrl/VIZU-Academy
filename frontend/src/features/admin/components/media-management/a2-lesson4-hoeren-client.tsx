"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft, CheckCircle2, CircleDashed, Eye, EyeOff, LoaderCircle, Play, RefreshCw, Trash2, Upload, XCircle } from "lucide-react";

import { AdminButton, AdminPageHeader } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import {
  deleteA2TextAudio,
  getA2Lesson4Hoeren,
  getA2TextAudioBlobUrl,
  setA2TextActive,
  setupA2Lesson4Hoeren,
  uploadA2TextAudio,
  verifyA2TextAudio,
  type A2TextSlot,
  type A2TextSlotNumber,
} from "@/features/admin/services/media-management-service";

const card = "rounded-2xl bg-[var(--admin-card)] p-4 ring-1 ring-[var(--admin-border)] sm:p-5";
const ACCEPT = ".mp3,.m4a,audio/mpeg,audio/mp4,audio/x-m4a";
const MAX_BYTES = 100 * 1024 * 1024; // backend A2_AUDIO_MAX_BYTES
const QUERY = ["a2-lesson4-hoeren"];

type UploadState = "none" | "uploading" | "done" | "error";
const UPLOAD_STATE: Record<UploadState, [string, string]> = {
  none: ["Nicht hochgeladen", "text-[var(--admin-text-muted)]"],
  uploading: ["Wird hochgeladen", "text-[var(--admin-primary)]"],
  done: ["Hochgeladen", "text-[var(--admin-success)]"],
  error: ["Fehler", "text-[var(--admin-danger)]"],
};

function bytes(n: number | null | undefined) {
  if (!n) return "—";
  return n >= 1024 * 1024 ? `${(n / 1024 / 1024).toFixed(2)} MB` : `${Math.max(1, Math.round(n / 1024))} KB`;
}

function seconds(n: number | null | undefined) {
  return n ? `${Math.floor(n / 60)}:${String(n % 60).padStart(2, "0")}` : "—";
}

/** Duration from the file's metadata in the browser (null if it cannot be read). */
function readDuration(file: File): Promise<number | null> {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const audio = new Audio();
    let settled = false;
    const done = (value: number | null) => {
      if (settled) return;
      settled = true;
      URL.revokeObjectURL(url);
      resolve(value);
    };
    audio.preload = "metadata";
    audio.onloadedmetadata = () => done(Number.isFinite(audio.duration) && audio.duration > 0 ? Math.round(audio.duration) : null);
    audio.onerror = () => done(null);
    setTimeout(() => done(null), 5000);
    audio.src = url;
  });
}

function uploadError(err: unknown): string {
  const message = (err as { response?: { data?: { message?: unknown } } })?.response?.data?.message;
  if (message && typeof message === "object") {
    const d = message as { code?: string; message?: string; used_by?: string | null; existing_filename?: string };
    if (d.code === "SAME_FILE") return d.message ?? "Diese Datei ist hier bereits hochgeladen.";
    if (d.code === "DUPLICATE") {
      return `Doppelte Datei: derselbe Inhalt ist schon vorhanden${d.existing_filename ? ` („${d.existing_filename}“)` : ""}`
        + (d.used_by ? ` und wird in „${d.used_by}“ verwendet.` : ".");
    }
  }
  return apiErrorMessage(err, "Upload fehlgeschlagen.");
}

/** One Text: upload / replace, listen, verify, show to students, delete — independent of the other two. */
function TextSlotCard({ slot, onChanged }: { slot: A2TextSlot; onChanged: () => Promise<unknown> }) {
  const input = useRef<HTMLInputElement>(null);
  const [percent, setPercent] = useState<number | null>(null);
  const [failed, setFailed] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [playing, setPlaying] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const n = slot.slot as A2TextSlotNumber;
  const audio = slot.audio;
  const hasFile = audio?.status === "ok";
  const state: UploadState = percent !== null ? "uploading" : failed ? "error" : audio && audio.status !== "none" ? (hasFile ? "done" : "error") : "none";
  const verification = slot.asset?.verification;

  async function run(key: string, action: () => Promise<unknown>, ok: string, fallback: string) {
    setBusy(key);
    setMsg(null);
    try {
      await action();
      setMsg({ ok: true, text: ok });
      await onChanged();
    } catch (err) {
      setMsg({ ok: false, text: apiErrorMessage(err, fallback) });
    } finally {
      setBusy(null);
    }
  }

  async function onFile(file: File | undefined) {
    if (input.current) input.current.value = "";
    if (!file) return;
    setMsg(null);
    setFailed(false);
    if (!/\.(mp3|m4a)$/i.test(file.name)) {
      setFailed(true);
      return setMsg({ ok: false, text: "Nur MP3 oder M4A." });
    }
    if (file.size > MAX_BYTES) {
      setFailed(true);
      return setMsg({ ok: false, text: "Die Datei ist größer als 100 MB." });
    }
    const replacing = hasFile;
    setPercent(0);
    try {
      const duration = await readDuration(file);
      const result = await uploadA2TextAudio(n, file, duration, setPercent);
      if (playing) URL.revokeObjectURL(playing);
      setPlaying(null);
      setMsg({ ok: true, text: `${result.reused ? "Vorhandene Datei aus der A2-Audio-Bibliothek verknüpft" : replacing ? "Audio ersetzt" : "Audio hochgeladen"}. `
        + "Bitte anhören und als geprüft markieren, dann aktivieren." + (replacing ? " Die vorherige Datei bleibt unverknüpft in der A2-Audio-Bibliothek." : "") });
      await onChanged();
    } catch (err) {
      setFailed(true);
      setMsg({ ok: false, text: uploadError(err) });
    } finally {
      setPercent(null);
    }
  }

  async function play() {
    if (playing) {
      URL.revokeObjectURL(playing);
      setPlaying(null);
      return;
    }
    try {
      setPlaying(await getA2TextAudioBlobUrl(n));
    } catch (err) {
      setMsg({ ok: false, text: apiErrorMessage(err, "Audio konnte nicht geladen werden.") });
    }
  }

  function verify(next: "verified" | "problem" | "pending") {
    const note = next === "problem" ? window.prompt("Was stimmt nicht mit dem Audio?") : null;
    if (next === "problem" && !note?.trim()) return;
    return run("verify", () => verifyA2TextAudio(n, next, note ?? undefined),
      next === "verified" ? "Als geprüft markiert." : next === "problem" ? "Problem gespeichert — der Text ist für Lernende ausgeblendet." : "Prüfung zurückgesetzt.",
      "Speichern fehlgeschlagen.");
  }

  if (!slot.exists) {
    return (
      <section className={card} data-testid="a2l4-slot" data-slot={n} data-exists="false">
        <h2 className="text-lg font-bold text-[var(--admin-text-primary)]">{slot.label}</h2>
        <p className="mt-2 text-sm text-[var(--admin-warning)]">Aufgabe noch nicht angelegt.</p>
      </section>
    );
  }

  return (
    <section className={`${card} flex min-w-0 flex-col gap-3`} data-testid="a2l4-slot" data-slot={n} data-state={state} data-active={slot.is_published}>
      <input ref={input} type="file" accept={ACCEPT} className="hidden" onChange={(e) => onFile(e.target.files?.[0])} data-testid="a2l4-file" />
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="mr-auto text-lg font-bold text-[var(--admin-text-primary)]">{slot.label}</h2>
        <span className={`text-xs font-semibold ${UPLOAD_STATE[state][1]}`} data-testid="a2l4-upload-state">{UPLOAD_STATE[state][0]}</span>
        <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${slot.is_published ? "bg-[var(--admin-success)]/15 text-[var(--admin-success)]" : "bg-[var(--admin-hover)] text-[var(--admin-text-secondary)]"}`}
              data-testid="a2l4-active-badge">
          {slot.is_published ? "Aktiv" : "Inaktiv"}
        </span>
      </div>

      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm">
        <dt className="text-[var(--admin-text-muted)]">Datei</dt>
        <dd className="truncate text-[var(--admin-text-primary)]" title={audio?.file_name ?? ""} data-testid="a2l4-file-name">{audio?.file_name ?? "—"}</dd>
        <dt className="text-[var(--admin-text-muted)]">Größe</dt>
        <dd className="text-[var(--admin-text-secondary)]" data-testid="a2l4-size">{bytes(audio?.size_bytes)}{audio?.format ? ` · ${audio.format}` : ""}</dd>
        <dt className="text-[var(--admin-text-muted)]">Dauer</dt>
        <dd className="text-[var(--admin-text-secondary)]" data-testid="a2l4-duration">{seconds(audio?.duration_seconds)}</dd>
        <dt className="text-[var(--admin-text-muted)]">Geprüft</dt>
        <dd data-testid="a2l4-verification">
          {!slot.asset ? <span className="text-[var(--admin-text-muted)]">—</span>
            : verification === "verified" ? <span className="inline-flex items-center gap-1 text-[var(--admin-success)]"><CheckCircle2 size={14} /> geprüft</span>
              : verification === "problem" ? <span className="inline-flex items-center gap-1 text-[var(--admin-danger)]"><XCircle size={14} /> Problem{slot.asset.verification_note ? `: ${slot.asset.verification_note}` : ""}</span>
                : <span className="inline-flex items-center gap-1 text-[var(--admin-warning)]"><CircleDashed size={14} /> noch nicht angehört</span>}
        </dd>
      </dl>
      {audio?.status === "missing" && (
        <p className="flex items-center gap-1.5 text-xs text-[var(--admin-danger)]"><AlertTriangle size={13} /> Die Audiodatei fehlt auf dem Server — bitte neu hochladen.</p>
      )}

      {percent !== null && (
        <div className="space-y-1" data-testid="a2l4-progress">
          <div className="h-2 overflow-hidden rounded-full bg-[var(--admin-hover)]">
            <div className="h-full bg-[var(--admin-primary)] transition-all" style={{ width: `${percent}%` }} />
          </div>
          <p className="text-xs text-[var(--admin-text-secondary)]">Wird hochgeladen … {percent}%</p>
        </div>
      )}

      {playing && <audio src={playing} controls autoPlay className="w-full" data-testid="a2l4-player" />}

      <div className="mt-auto flex flex-wrap gap-2">
        <AdminButton size="sm" disabled={percent !== null || busy !== null} onClick={() => input.current?.click()} data-testid="a2l4-upload">
          {percent !== null ? <LoaderCircle size={14} className="animate-spin" /> : <Upload size={14} />} {hasFile ? "Ersetzen" : "Hochladen"}
        </AdminButton>
        <AdminButton size="sm" variant="secondary" disabled={!hasFile} onClick={play} data-testid="a2l4-play" aria-label={`${slot.label} anhören`}>
          <Play size={14} /> {playing ? "Schließen" : "Anhören"}
        </AdminButton>
        {slot.asset && verification !== "verified" && (
          <AdminButton size="sm" variant="secondary" disabled={!hasFile || busy !== null} onClick={() => verify("verified")} data-testid="a2l4-verify">
            <CheckCircle2 size={14} /> Geprüft
          </AdminButton>
        )}
        {slot.asset && verification !== "problem" && (
          <AdminButton size="sm" variant="ghost" disabled={busy !== null} onClick={() => verify("problem")} data-testid="a2l4-problem">
            <XCircle size={14} /> Problem
          </AdminButton>
        )}
        {slot.is_published ? (
          <AdminButton size="sm" variant="secondary" disabled={busy !== null} data-testid="a2l4-deactivate"
                       onClick={() => run("active", () => setA2TextActive(n, false), "Deaktiviert — für Lernende ausgeblendet.", "Konnte nicht geändert werden.")}>
            <EyeOff size={14} /> Deaktivieren
          </AdminButton>
        ) : (
          <AdminButton size="sm" variant="secondary" disabled={busy !== null || !slot.can_activate} title={slot.activate_blocker ?? undefined} data-testid="a2l4-activate"
                       onClick={() => run("active", () => setA2TextActive(n, true), "Aktiviert — für Lernende sichtbar.", "Konnte nicht aktiviert werden.")}>
            <Eye size={14} /> Aktivieren
          </AdminButton>
        )}
        <AdminButton size="sm" variant="danger" disabled={busy !== null || percent !== null || !audio || audio.status === "none"} onClick={() => setDeleting(true)}
                     data-testid="a2l4-delete" aria-label={`${slot.label}: Audio löschen`}>
          <Trash2 size={14} />
        </AdminButton>
      </div>
      {!slot.is_published && slot.activate_blocker && <p className="text-xs text-[var(--admin-text-muted)]" data-testid="a2l4-blocker">Aktivieren: {slot.activate_blocker}.</p>}
      {msg && <p role="status" className={`text-xs ${msg.ok ? "text-[var(--admin-success)]" : "text-[var(--admin-danger)]"}`} data-testid="a2l4-msg">{msg.text}</p>}

      <ConfirmDialog
        open={deleting}
        onOpenChange={(open) => !open && setDeleting(false)}
        title={`Audio von „${slot.label}“ löschen`}
        description={`Das Audio von ${slot.label} wird entfernt und die Datei gelöscht, sofern sie nirgends sonst verwendet wird. ${slot.label} wird deaktiviert; die anderen Texte bleiben unverändert.`}
        isPending={busy === "delete"}
        onConfirm={async () => {
          if (playing) URL.revokeObjectURL(playing);
          setPlaying(null);
          await run("delete", () => deleteA2TextAudio(n), "Audio gelöscht.", "Löschen fehlgeschlagen.");
          setFailed(false);
          setDeleting(false);
        }}
      />
    </section>
  );
}

/** Admin → Media Management → A2 → 4. Unterricht → Hören: three independent
 * tasks Text 1 / 2 / 3, each with its own audio (A2 Audio Manager checks:
 * MP3 / M4A by name, MIME type and content, SHA-256 duplicates). Questions
 * can be added to each Text later in the lesson's Hören editor. */
export default function A2Lesson4HoerenClient() {
  const queryClient = useQueryClient();
  const data = useQuery({ queryKey: QUERY, queryFn: getA2Lesson4Hoeren });
  const [setupError, setSetupError] = useState<string | null>(null);
  const [settingUp, setSettingUp] = useState(false);
  const refresh = () => Promise.all([queryClient.invalidateQueries({ queryKey: QUERY }), queryClient.invalidateQueries({ queryKey: ["media-mgmt"] })]);

  async function setup() {
    setSettingUp(true);
    setSetupError(null);
    try {
      queryClient.setQueryData(QUERY, await setupA2Lesson4Hoeren());
    } catch (err) {
      setSetupError(apiErrorMessage(err, "Konnte nicht angelegt werden."));
    } finally {
      setSettingUp(false);
    }
  }

  return (
    <div className="space-y-6" data-testid="a2l4-hoeren">
      <Link href="/admin/media-management" className="inline-flex items-center gap-1.5 text-sm text-[var(--admin-text-secondary)] hover:text-[var(--admin-primary)]">
        <ArrowLeft size={15} /> Media Management
      </Link>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <AdminPageHeader title="A2 · 4. Unterricht · Hören"
                         description={`Text 1, Text 2 und Text 3 — jeder Text hat sein eigenes Audio (MP3 oder M4A).${data.data ? ` Lektion: ${data.data.lesson_title}` : ""}`} />
        <AdminButton variant="ghost" size="sm" onClick={() => data.refetch()} aria-label="Aktualisieren"><RefreshCw size={14} /></AdminButton>
      </div>

      {data.isLoading && <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen …</p>}
      {data.isError && <p className="rounded-xl bg-[var(--admin-danger)]/10 p-3 text-sm text-[var(--admin-danger)]" role="alert">{apiErrorMessage(data.error, "Konnte nicht geladen werden.")}</p>}

      {data.data && !data.data.set_up && (
        <section className={`${card} flex flex-wrap items-center gap-3`}>
          <p className="mr-auto text-sm text-[var(--admin-text-secondary)]">Die Aufgaben Text 1–3 sind noch nicht (vollständig) angelegt.</p>
          <AdminButton onClick={setup} disabled={settingUp} data-testid="a2l4-setup">
            {settingUp && <LoaderCircle size={14} className="animate-spin" />} Text 1–3 anlegen
          </AdminButton>
          {setupError && <p className="w-full text-sm text-[var(--admin-danger)]">{setupError}</p>}
        </section>
      )}

      {data.data && data.data.legacy_tasks.length > 0 && (
        <p className="rounded-xl bg-[var(--admin-warning)]/10 p-3 text-sm text-[var(--admin-warning)]" data-testid="a2l4-legacy">
          Alte Aufgabe noch vorhanden: {data.data.legacy_tasks.map((t) => `„${t.title}“`).join(", ")} — wird mit dem Skript app.scripts.a2_lesson4_hoeren entfernt.
        </p>
      )}

      {data.data && (
        <div className="grid gap-4 lg:grid-cols-3">
          {data.data.slots.map((slot) => <TextSlotCard key={slot.slot} slot={slot} onChanged={refresh} />)}
        </div>
      )}

      <p className="text-xs text-[var(--admin-text-muted)]">
        Neues Audio ist zunächst „noch nicht angehört“ und der Text inaktiv. Aktivieren geht erst, wenn das Audio auf dem Server liegt und als geprüft markiert ist.
        Lernende sehen nur aktive Texte, und nur mit Zugang zur Lektion. Fragen und Lösungen zu einem Text können später im Hören-Editor der Lektion ergänzt werden.
      </p>
    </div>
  );
}
