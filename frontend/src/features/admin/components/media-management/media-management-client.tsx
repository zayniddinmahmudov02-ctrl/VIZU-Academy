"use client";

import { Fragment, useMemo, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { AlertTriangle, Eye, EyeOff, FileText, Film, ListMusic, Music, Play, RefreshCw, Search, Trash2, Upload, X } from "lucide-react";

import AudioSlotsPanel from "./audio-slots-panel";
import A2ListeningSlots from "./a2-listening-slots";

import { AdminButton, AdminCheckbox, AdminInput, AdminPageHeader, AdminSelect } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import UploadProgressPanel from "@/components/admin/upload-progress-panel";
import { useChunkedVideoUpload } from "@/features/admin/hooks/use-chunked-video-upload";
import { apiErrorMessage, deleteListeningAudio, getListeningAudioBlobUrl, uploadListeningAudio } from "@/features/admin/services/lesson-skills-admin-service";
import { listeningApi } from "@/features/admin/services/listening-service";
import { getMediaItems, getMediaTree, getVideoPreviewUrl, type MediaItem } from "@/features/admin/services/media-management-service";
import { deleteVideo, updateVideo } from "@/features/admin/services/video-service";
import { resolveMediaUrl } from "@/lib/media";

const VIDEO_ACCEPT = ".mp4,.webm,.mov,.m4v,video/mp4,video/webm,video/quicktime";
const AUDIO_ACCEPT = ".mp3,.wav,.m4a,audio/mpeg,audio/wav,audio/x-wav,audio/mp4,audio/x-m4a";
const AUDIO_MAX = 100 * 1024 * 1024; // backend MAX_AUDIO_BYTES
const card = "rounded-2xl bg-[var(--admin-card)] p-4 ring-1 ring-[var(--admin-border)] sm:p-5";

function size(bytes: number | null) {
  if (!bytes) return "—";
  const mb = bytes / 1048576;
  return mb >= 1 ? `${mb.toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

function readDuration(file: File, kind: "video" | "audio"): Promise<number | null> {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const el = document.createElement(kind);
    const done = (v: number | null) => { URL.revokeObjectURL(url); resolve(v); };
    el.preload = "metadata";
    el.onloadedmetadata = () => done(Number.isFinite(el.duration) ? Math.round(el.duration) : null);
    el.onerror = () => done(null);
    el.src = url;
  });
}

const STATUS_LABEL: Record<MediaItem["file_status"], string> = { ok: "Datei vorhanden", missing: "Datei fehlt", external: "Externer Link", none: "Keine Datei" };

/** Media Management: videos and Hören audio of every lesson (A1–C1) in one
 * place. Uses the existing upload / replace / publish / delete endpoints;
 * the overview comes from GET /admin/media-management/items. */
export default function MediaManagementClient() {
  const queryClient = useQueryClient();
  const tree = useQuery({ queryKey: ["media-mgmt", "tree"], queryFn: getMediaTree });
  const items = useQuery({ queryKey: ["media-mgmt", "items"], queryFn: getMediaItems });
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["media-mgmt", "items"] });

  // ---- selection: level -> module -> lesson
  const [level, setLevel] = useState("");
  const [moduleId, setModuleId] = useState("");
  const [lessonId, setLessonId] = useState("");
  const levelNode = tree.data?.find((l) => l.level === level);
  const moduleNode = levelNode?.modules.find((m) => m.id === moduleId) ?? (levelNode?.modules.length === 1 ? levelNode.modules[0] : undefined);
  const lessonNode = moduleNode?.lessons.find((l) => l.id === lessonId);
  const lessonTasks = (items.data ?? []).filter((i) => i.kind === "AUDIO" && i.lesson_id === lessonId);
  const audioTaskCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const item of items.data ?? []) {
      if (item.kind === "AUDIO") counts.set(item.lesson_id, (counts.get(item.lesson_id) ?? 0) + 1);
    }
    return counts;
  }, [items.data]);

  // ---- filters
  const [fKind, setFKind] = useState("");
  const [fStatus, setFStatus] = useState("");
  const [query, setQuery] = useState("");
  const [onlyLesson, setOnlyLesson] = useState(false);
  const rows = useMemo(() => (items.data ?? []).filter((i) =>
    (!level || i.level === level) && (!onlyLesson || !lessonId || i.lesson_id === lessonId) && (!fKind || i.kind === fKind)
    && (!fStatus || (fStatus === "published" ? i.is_published : fStatus === "draft" ? !i.is_published : i.file_status === fStatus))
    && (!query || `${i.title} ${i.lesson_title} ${i.file_name ?? ""} ${i.level} ${i.lesson_number}`.toLowerCase().includes(query.toLowerCase())),
  ), [items.data, level, onlyLesson, lessonId, fKind, fStatus, query]);

  // ---- messages / busy
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  async function run(id: string, action: () => Promise<unknown>, ok: string, fallback: string) {
    setBusyId(id);
    setMessage(null);
    try {
      await action();
      setMessage({ ok: true, text: ok });
      await refresh();
    } catch (err) {
      setMessage({ ok: false, text: apiErrorMessage(err, fallback) });
    } finally {
      setBusyId(null);
    }
  }

  // ---- video upload (new or replace), chunked with progress
  const video = useChunkedVideoUpload();
  const [videoTitle, setVideoTitle] = useState("");
  const [videoPublish, setVideoPublish] = useState(false);
  const videoInput = useRef<HTMLInputElement>(null);
  const replaceVideoId = useRef<string | null>(null);
  const replaceVideoLesson = useRef<string | null>(null);

  async function onVideoFile(file: File | undefined) {
    if (videoInput.current) videoInput.current.value = "";
    const replacing = replaceVideoId.current;
    const target = replacing ? replaceVideoLesson.current : lessonId;
    replaceVideoId.current = null;
    if (!file || !target) return;
    setMessage(null);
    const duration = await readDuration(file, "video");
    try {
      await video.upload(file, {
        lessonId: target, title: (videoTitle.trim() || file.name.replace(/\.[^.]+$/, "")).slice(0, 255),
        durationSeconds: duration ?? undefined, isPublished: replacing ? undefined : videoPublish, replaceVideoId: replacing,
      });
      setMessage({ ok: true, text: replacing ? "Videodatei ersetzt." : "Video hochgeladen und der Lektion zugeordnet." });
      setVideoTitle("");
      await refresh();
    } catch (err) {
      setMessage({ ok: false, text: apiErrorMessage(err, "Video-Upload fehlgeschlagen.") });
    }
  }

  // ---- audio upload (to one Hören task)
  const [audioTask, setAudioTask] = useState("");
  const [audioPercent, setAudioPercent] = useState<number | null>(null);
  const audioInput = useRef<HTMLInputElement>(null);
  const audioTarget = useRef<string | null>(null);

  function pickAudio(listeningId: string) {
    audioTarget.current = listeningId;
    audioInput.current?.click();
  }

  async function onAudioFile(file: File | undefined) {
    if (audioInput.current) audioInput.current.value = "";
    const id = audioTarget.current;
    if (!file || !id) return;
    if (!/\.(mp3|wav|m4a)$/i.test(file.name)) return setMessage({ ok: false, text: "Nur MP3, WAV oder M4A." });
    if (file.size > AUDIO_MAX) return setMessage({ ok: false, text: "Die Datei ist größer als 100 MB." });
    const duration = await readDuration(file, "audio");
    setAudioPercent(0);
    await run(id, () => uploadListeningAudio(id, file, duration, setAudioPercent), "Audio hochgeladen.", "Audio-Upload fehlgeschlagen.");
    setAudioPercent(null);
  }

  // ---- preview / delete
  const [preview, setPreview] = useState<{ item: MediaItem; url: string } | null>(null);
  async function openPreview(item: MediaItem) {
    setMessage(null);
    try {
      const url = item.kind === "VIDEO" ? resolveMediaUrl(await getVideoPreviewUrl(item.id)) ?? "" : await getListeningAudioBlobUrl(item.id);
      setPreview({ item, url });
    } catch (err) {
      setMessage({ ok: false, text: apiErrorMessage(err, "Datei konnte nicht geladen werden.") });
    }
  }
  function closePreview() {
    if (preview?.item.kind === "AUDIO") URL.revokeObjectURL(preview.url);
    setPreview(null);
  }
  const [deleting, setDeleting] = useState<MediaItem | null>(null);

  // ---- audio slots (main audio + labelled tracks): open by default for tasks with several files
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  function toggleSlots(id: string, open: boolean, multi: boolean) {
    const without = (s: Set<string>) => { const n = new Set(s); n.delete(id); return n; };
    if (open) {
      setExpanded(without);
      if (multi) setCollapsed((s) => new Set(s).add(id));
    } else {
      setCollapsed(without);
      setExpanded((s) => new Set(s).add(id));
    }
  }

  function togglePublish(item: MediaItem) {
    const next = !item.is_published;
    return run(item.id, () => (item.kind === "VIDEO" ? updateVideo(item.id, { is_published: next }) : listeningApi.update(item.id, { is_published: next })),
      next ? "Veröffentlicht." : "Auf Entwurf gesetzt.", "Status konnte nicht geändert werden.");
  }

  const busyUpload = video.progress.state === "UPLOAD_STARTED" || video.progress.state === "UPLOADING" || audioPercent !== null;

  return (
    <div className="space-y-6" data-testid="media-management">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <AdminPageHeader title="Media Management" description="Videos und Hören-Audio aller Lektionen (A1–C1) hochladen, zuordnen und verwalten." />
        <Link href="/admin/media-management/hoeren-a1" data-testid="mm-hoeren-a1-link"
              className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-[var(--admin-primary)] ring-1 ring-[var(--admin-border-strong)] hover:bg-[var(--admin-hover)]">
          <FileText size={15} /> A1 Hören: Antwort-PDF & Veröffentlichung
        </Link>
      </div>
      <input ref={videoInput} type="file" accept={VIDEO_ACCEPT} className="hidden" onChange={(e) => onVideoFile(e.target.files?.[0])} data-testid="mm-video-file" />
      <input ref={audioInput} type="file" accept={AUDIO_ACCEPT} className="hidden" onChange={(e) => onAudioFile(e.target.files?.[0])} data-testid="mm-audio-file" />

      {/* 1. lesson */}
      <section className={card}>
        <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">1. Lektion wählen</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <AdminSelect value="de" disabled aria-label="Sprache"><option value="de">Deutsch</option></AdminSelect>
          <AdminSelect value={level} onChange={(e) => { setLevel(e.target.value); setModuleId(""); setLessonId(""); }} aria-label="Niveau" data-testid="mm-level">
            <option value="">Niveau wählen</option>
            {tree.data?.map((l) => <option key={l.level} value={l.level}>{l.level}</option>)}
          </AdminSelect>
          <AdminSelect value={moduleNode?.id ?? ""} onChange={(e) => { setModuleId(e.target.value); setLessonId(""); }} disabled={!levelNode} aria-label="Modul">
            <option value="">Modul wählen</option>
            {levelNode?.modules.map((m) => <option key={m.id} value={m.id}>Modul {m.number}{m.title ? ` — ${m.title}` : ""}</option>)}
          </AdminSelect>
          <AdminSelect value={lessonId} onChange={(e) => setLessonId(e.target.value)} disabled={!moduleNode} aria-label="Lektion" data-testid="mm-lesson">
            <option value="">Lektion wählen</option>
            {moduleNode?.lessons.map((l) => (
              <option key={l.id} value={l.id}>
                {l.number}. {l.title}
                {level === "A2" && items.isSuccess ? ` · ${audioTaskCounts.get(l.id) ?? 0} Aufgabe(n)` : ""}
              </option>
            ))}
          </AdminSelect>
        </div>
      </section>

      {/* 2. upload */}
      <section className={`${card} space-y-5`}>
        <h2 className="text-sm font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">
          2. Hochladen {lessonNode && <>— {level} · Lektion {lessonNode.number}: {lessonNode.title}{level === "A2" && items.isSuccess ? ` · ${lessonTasks.length} Hören-Aufgaben` : ""}</>}
        </h2>
        {!lessonNode ? (
          <p className="text-sm text-[var(--admin-text-muted)]">Zuerst eine Lektion wählen.</p>
        ) : (
          <div className="grid gap-5 lg:grid-cols-2">
            <div className="space-y-3" data-testid="mm-video-upload">
              <p className="flex items-center gap-2 font-semibold text-[var(--admin-text-primary)]"><Film size={16} /> Video (Video-Unterricht)</p>
              <AdminInput placeholder="Titel (optional — sonst Dateiname)" value={videoTitle} onChange={(e) => setVideoTitle(e.target.value)} maxLength={255} />
              <label className="flex items-center gap-2 text-sm text-[var(--admin-text-secondary)]">
                <AdminCheckbox checked={videoPublish} onCheckedChange={(v) => setVideoPublish(Boolean(v))} /> Sofort veröffentlichen
              </label>
              <AdminButton disabled={busyUpload} onClick={() => { replaceVideoId.current = null; videoInput.current?.click(); }} data-testid="mm-video-upload-btn">
                <Upload size={15} /> Video auswählen und hochladen
              </AdminButton>
              <p className="text-xs text-[var(--admin-text-muted)]">MP4, WebM, MOV · in Teilen hochgeladen, Fortsetzung nach Abbruch möglich.</p>
            </div>
            <div className="space-y-3" data-testid="mm-audio-upload">
              <p className="flex items-center gap-2 font-semibold text-[var(--admin-text-primary)]"><Music size={16} /> Audio (Hören-Aufgabe)</p>
              {lessonTasks.length === 0 ? (
                <p className="text-sm text-[var(--admin-text-muted)]">Diese Lektion hat keine Hören-Aufgabe — Audio wird immer einer Aufgabe zugeordnet.</p>
              ) : (
                <>
                  <AdminSelect value={audioTask} onChange={(e) => setAudioTask(e.target.value)} aria-label="Hören-Aufgabe" data-testid="mm-audio-task">
                    <option value="">Hören-Aufgabe wählen</option>
                    {lessonTasks.map((t) => <option key={t.id} value={t.id}>{t.title}{t.file_status === "ok" ? " (hat Audio)" : ""}</option>)}
                  </AdminSelect>
                  <AdminButton disabled={!audioTask || busyUpload} onClick={() => pickAudio(audioTask)} data-testid="mm-audio-upload-btn">
                    <Upload size={15} /> Audio auswählen und hochladen
                  </AdminButton>
                </>
              )}
              <p className="text-xs text-[var(--admin-text-muted)]">MP3, WAV, M4A · max. 100 MB · Inhalt wird serverseitig geprüft.</p>
            </div>
          </div>
        )}
        <UploadProgressPanel progress={video.progress} label="Video wird hochgeladen" onCancel={video.cancel} onRetry={video.reset} />
        {audioPercent !== null && (
          <div className="space-y-1" data-testid="mm-audio-progress">
            <p className="text-xs text-[var(--admin-text-secondary)]">Audio wird hochgeladen … {audioPercent}%</p>
            <div className="h-1.5 overflow-hidden rounded-full bg-[var(--admin-border)]"><div className="h-full bg-[var(--admin-primary)]" style={{ width: `${audioPercent}%` }} /></div>
          </div>
        )}
      </section>

      {level === "A2" && lessonNode && (
        <A2ListeningSlots
          lessonNumber={lessonNode.number}
          lessonTasks={lessonTasks}
          onTaskSelected={setAudioTask}
        />
      )}

      {message && (
        <p role="status" data-testid="mm-message"
           className={`rounded-xl px-4 py-3 text-sm ${message.ok ? "bg-[var(--admin-success)]/10 text-[var(--admin-success)]" : "bg-[var(--admin-danger)]/10 text-[var(--admin-danger)]"}`}>
          {message.text}
        </p>
      )}

      {/* 3. library */}
      <section className={`${card} space-y-4`}>
        <div className="flex flex-wrap items-end gap-3">
          <h2 className="mr-auto text-sm font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">3. Medienbibliothek ({rows.length})</h2>
          <div className="relative">
            <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--admin-text-muted)]" />
            <AdminInput className="w-56 pl-8" placeholder="Suchen …" value={query} onChange={(e) => setQuery(e.target.value)} data-testid="mm-search" />
          </div>
          <AdminSelect className="w-36" value={fKind} onChange={(e) => setFKind(e.target.value)} aria-label="Typ" data-testid="mm-filter-kind">
            <option value="">Alle Typen</option><option value="VIDEO">Video</option><option value="AUDIO">Audio</option>
          </AdminSelect>
          <AdminSelect className="w-44" value={fStatus} onChange={(e) => setFStatus(e.target.value)} aria-label="Status" data-testid="mm-filter-status">
            <option value="">Alle Status</option><option value="published">Veröffentlicht</option><option value="draft">Entwurf</option>
            <option value="ok">Datei vorhanden</option><option value="missing">Datei fehlt</option><option value="none">Keine Datei</option>
          </AdminSelect>
          {lessonId && (
            <label className="flex items-center gap-2 text-sm text-[var(--admin-text-secondary)]">
              <AdminCheckbox checked={onlyLesson} onCheckedChange={(v) => setOnlyLesson(Boolean(v))} /> nur gewählte Lektion
            </label>
          )}
          <AdminButton variant="ghost" size="sm" onClick={refresh} aria-label="Aktualisieren"><RefreshCw size={14} /></AdminButton>
        </div>

        {items.isLoading ? (
          <p className="py-10 text-center text-sm text-[var(--admin-text-muted)]">Lädt …</p>
        ) : rows.length === 0 ? (
          <p className="py-10 text-center text-sm text-[var(--admin-text-muted)]">Keine Medien gefunden.</p>
        ) : (
          <div className="-mx-4 overflow-x-auto sm:mx-0">
            <table className="w-full min-w-[960px] text-left text-sm" data-testid="mm-table">
              <thead className="text-xs uppercase tracking-wide text-[var(--admin-text-muted)]">
                <tr>{["Niveau", "Lektion", "Typ", "Titel / Aufgabe", "Datei", "Größe", "Geändert", "Status", "Aktionen"].map((h) => <th key={h} className="px-3 py-2 font-semibold">{h}</th>)}</tr>
              </thead>
              <tbody>
                {rows.map((i) => {
                  const hasFile = i.file_status === "ok";
                  const slots = i.audio_slots ?? [];
                  const multi = slots.length > 1;
                  const open = i.kind === "AUDIO" && (expanded.has(i.id) || (multi && !collapsed.has(i.id)));
                  return (
                    <Fragment key={`${i.kind}-${i.id}`}>
                    <tr className="border-t border-[var(--admin-border)] align-top" data-testid="mm-row" data-kind={i.kind} data-file={i.file_status}>
                      <td className="px-3 py-2.5 font-semibold text-[var(--admin-text-primary)]">{i.level}</td>
                      <td className="px-3 py-2.5 text-[var(--admin-text-secondary)]">{i.lesson_number}. {i.lesson_title}</td>
                      <td className="px-3 py-2.5">{i.kind === "VIDEO" ? <span className="inline-flex items-center gap-1"><Film size={14} /> Video</span> : <span className="inline-flex items-center gap-1"><Music size={14} /> Audio</span>}</td>
                      <td className="px-3 py-2.5 text-[var(--admin-text-primary)]">
                        {i.title}
                        <span className="block text-xs text-[var(--admin-text-muted)]">{i.kind === "VIDEO" ? `Bereich: ${i.task === "EINFUEHRUNG" ? "Video-Unterricht" : i.task}` : `${i.questions ?? 0} Fragen · ${i.has_key ? "Lösungen vollständig" : "Lösungen fehlen"}`}</span>
                        {multi && <span className="block text-xs font-semibold text-[var(--admin-primary)]">{slots.length} Audiodateien: {slots.map((s) => s.label ?? "Audio").join(" · ")}</span>}
                      </td>
                      <td className="px-3 py-2.5 text-xs">
                        {multi ? (
                          // several independent audio files: one status line per slot, no combined file
                          slots.map((s) => (
                            <span key={s.id} className="block max-w-[16rem] truncate" title={s.file_name ?? ""} data-testid="mm-slot-status">
                              <span className="text-[var(--admin-text-secondary)]">{s.label ?? "Audio"}: </span>
                              <span className={s.file_status === "ok" ? "text-[var(--admin-success)]" : "text-[var(--admin-warning)]"}>
                                {s.file_status === "ok" ? s.file_name ?? "Datei vorhanden" : STATUS_LABEL[s.file_status] ?? "Keine Datei"}
                              </span>
                            </span>
                          ))
                        ) : (
                          <>
                            <span className="block max-w-[14rem] truncate text-[var(--admin-text-secondary)]" title={i.file_name ?? ""}>{i.file_name ?? "—"}</span>
                            <span className={hasFile ? "text-[var(--admin-success)]" : "text-[var(--admin-warning)]"}>
                              {!hasFile && <AlertTriangle size={11} className="mr-1 inline" />}{STATUS_LABEL[i.file_status]}
                            </span>
                          </>
                        )}
                      </td>
                      <td className="px-3 py-2.5 text-[var(--admin-text-secondary)]">{size(i.size_bytes)}</td>
                      <td className="px-3 py-2.5 text-xs text-[var(--admin-text-secondary)]">{new Date(i.updated_at).toLocaleDateString("de-DE")}</td>
                      <td className="px-3 py-2.5">
                        <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${i.is_published ? "bg-[var(--admin-success)]/15 text-[var(--admin-success)]" : "bg-[var(--admin-hover)] text-[var(--admin-text-secondary)]"}`}>
                          {i.is_published ? "Veröffentlicht" : "Entwurf"}
                        </span>
                      </td>
                      <td className="px-3 py-2.5">
                        <div className="flex flex-wrap gap-1.5">
                          {/* several audio files: upload / listen / remove per slot in the panel below — the row buttons would only reach the first one */}
                          {!multi && (<>
                          <AdminButton size="sm" variant="secondary" disabled={!hasFile} onClick={() => openPreview(i)} title={i.kind === "VIDEO" ? "Ansehen" : "Anhören"} data-testid="mm-preview"><Play size={13} /></AdminButton>
                          <AdminButton size="sm" variant="secondary" disabled={busyUpload || busyId === i.id} title={hasFile ? "Datei ersetzen" : "Datei hochladen"} data-testid="mm-replace"
                                       onClick={() => { if (i.kind === "VIDEO") { replaceVideoId.current = i.id; replaceVideoLesson.current = i.lesson_id; videoInput.current?.click(); } else pickAudio(i.id); }}>
                            <Upload size={13} />
                          </AdminButton>
                          </>)}
                          <AdminButton size="sm" variant="secondary" disabled={busyId === i.id} onClick={() => togglePublish(i)} title={i.is_published ? "Auf Entwurf setzen" : "Veröffentlichen"} data-testid="mm-publish">
                            {i.is_published ? <EyeOff size={13} /> : <Eye size={13} />}
                          </AdminButton>
                          {!multi && (
                          <AdminButton size="sm" variant="danger" disabled={busyId === i.id || (i.kind === "AUDIO" && !hasFile && i.file_status !== "missing")} onClick={() => setDeleting(i)}
                                       title={i.kind === "VIDEO" ? "Video löschen" : "Audio entfernen"} data-testid="mm-delete"><Trash2 size={13} /></AdminButton>
                          )}
                          {i.kind === "AUDIO" && (
                            <AdminButton size="sm" variant={open ? "primary" : "secondary"} onClick={() => toggleSlots(i.id, open, multi)} title="Audiodateien (Spuren) verwalten"
                                         aria-expanded={open} data-testid="mm-slots"><ListMusic size={13} /></AdminButton>
                          )}
                        </div>
                      </td>
                    </tr>
                    {open && (
                      <tr className="bg-[var(--admin-card)]" data-testid="mm-slots-row">
                        <td colSpan={9} className="px-3 pb-3">
                          <AudioSlotsPanel listeningId={i.id} slots={slots} onChanged={refresh} />
                        </td>
                      </tr>
                    )}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {preview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" role="dialog" aria-modal="true" onClick={closePreview}>
          <div className={`${card} w-full max-w-3xl space-y-3`} onClick={(e) => e.stopPropagation()} data-testid="mm-preview-dialog">
            <div className="flex items-center justify-between gap-3">
              <p className="font-semibold text-[var(--admin-text-primary)]">{preview.item.level} · Lektion {preview.item.lesson_number} · {preview.item.title}</p>
              <AdminButton size="sm" variant="ghost" onClick={closePreview} aria-label="Schließen"><X size={15} /></AdminButton>
            </div>
            {preview.item.kind === "VIDEO" ? (
              <video src={preview.url} controls playsInline controlsList="nodownload" className="aspect-video w-full rounded-xl bg-black" />
            ) : (
              <audio src={preview.url} controls className="w-full" />
            )}
          </div>
        </div>
      )}

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(open) => !open && setDeleting(null)}
        title={deleting?.kind === "VIDEO" ? "Video löschen" : "Audio entfernen"}
        description={deleting?.kind === "VIDEO"
          ? `„${deleting?.title}“ wird mit Datei gelöscht und verschwindet aus Video-Unterricht. Der Sehfortschritt der Lernenden für dieses Video geht verloren.`
          : `Die Audiodatei von „${deleting?.title}“ wird entfernt. Die Hören-Aufgabe und ihre Fragen bleiben, sie ist für Lernende erst nach einem neuen Upload wieder sichtbar.`}
        isPending={!!deleting && busyId === deleting.id}
        onConfirm={async () => {
          const d = deleting;
          if (!d) return;
          await run(d.id, () => (d.kind === "VIDEO" ? deleteVideo(d.id) : deleteListeningAudio(d.id)),
            d.kind === "VIDEO" ? "Video gelöscht." : "Audio entfernt.", "Löschen fehlgeschlagen.");
          setDeleting(null);
        }}
      />
    </div>
  );
}
