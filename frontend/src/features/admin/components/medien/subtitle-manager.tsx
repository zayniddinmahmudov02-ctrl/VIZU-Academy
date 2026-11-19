"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle, BadgeCheck, Bot, CheckCircle2, Download, Eye, EyeOff, Languages, Loader2, Pencil, Plus, RefreshCw, RotateCcw, ScanSearch, Sparkles, Square,
  Trash2, Upload, X,
} from "lucide-react";

import { AdminButton, AdminSelect } from "@/components/admin/admin-ui";
import {
  approveSubtitle, cancelSubtitleJob, checkSubtitle, deleteSubtitle, downloadSubtitle, getFilm, getSubtitleAiStatus, getSubtitleJobs, getSubtitlePreview,
  medienError, recheckSubtitle, retrySubtitleJob, saveSubtitleCues, startAiSubtitles, translateSubtitle, updateSubtitle, uploadSubtitle,
  type AdminItem, type AdminSubtitle, type PreviewCue, type SubtitleAiStatus, type SubtitleCheck, type SubtitleJob, type SubtitlePreview,
  type SubtitleReport, type SubtitleWarning,
} from "@/features/admin/services/medien-admin-service";
import { activeCues, formatCueTime, parseCueTime, type Cue } from "@/features/medien/lib/subtitles";

import { FILE_DE, fileSize } from "./shared";

const LANGS = [["de", "Deutsch"], ["uz", "O'zbekcha"], ["en", "English"], ["ru", "Русский"]] as const;
const ALL_LANGS: Record<string, string> = { de: "Deutsch", uz: "O'zbekcha", en: "English", ru: "Русский" };
const SOURCE_DE: Record<string, string> = { UPLOAD: "Hochgeladen", AI: "KI-Transkript aus der Tonspur", TRANSLATION: "KI-Übersetzung" };
const JOB_STATUS_DE: Record<string, string> = { PENDING: "Wartet", PROCESSING: "Läuft", COMPLETED: "Fertig", FAILED: "Fehlgeschlagen" };
const JOB_ERROR_DE: Record<string, string> = {
  AI_NOT_CONFIGURED: "Der KI-Dienst ist auf dem Server nicht eingerichtet (API-Schlüssel fehlt).",
  AI_KEY_REJECTED: "Der KI-Dienst hat den API-Schlüssel abgelehnt.",
  AI_NETWORK: "Der KI-Dienst war nicht erreichbar.",
  AI_HTTP_429: "Der KI-Dienst ist ausgelastet (Kontingent) — später wiederholen.",
  AI_BAD_ANSWER: "Die KI-Antwort war unbrauchbar.",
  AI_EMPTY_ANSWER: "Die KI hat keinen Text geliefert.",
  AI_ANSWER_TOO_LONG: "Die KI-Antwort wurde abgeschnitten.",
  AI_TRANSLATION_COUNT: "Die Übersetzung passte nicht Zeile für Zeile.",
  VIDEO_MISSING: "Die Videodatei fehlt.",
  NO_AUDIO: "Das Video hat keine Tonspur.",
  NO_SPEECH: "In der Tonspur wurde keine Sprache gefunden.",
  LANGUAGE_NOT_SUPPORTED: "Die erkannte Sprache wird nicht unterstützt (de, en, uz, ru).",
  SUBTITLE_EXISTS: "Für die erkannte Sprache gibt es schon einen Untertitel — mit „Vorhandene ersetzen“ neu starten.",
  SOURCE_MISSING: "Der Ausgangs-Untertitel wurde gelöscht.",
  FFMPEG_MISSING: "FFmpeg fehlt auf dem Server.",
  FFMPEG_TIMEOUT: "FFmpeg hat zu lange gebraucht.",
  AUDIO_READ_FAILED: "Die Tonspur konnte nicht gelesen werden.",
  AUDIO_CUT_FAILED: "Ein Tonabschnitt konnte nicht vorbereitet werden.",
  CANCELLED: "Abgebrochen.",
  INTERRUPTED: "Der Auftrag wurde zu oft unterbrochen.",
  INTERNAL_ERROR: "Unerwarteter Fehler (Server-Log prüfen).",
};

const WARNING_DE: Record<string, string> = {
  ENCODING_CONVERTED: "Die Datei war nicht UTF-8 (als Windows-1252 gelesen, als UTF-8 gespeichert): Umlaute prüfen.",
  BAD_TIMESTAMP: "Zeitzeilen, die nicht gelesen werden konnten, wurden übersprungen.",
  BAD_RANGE: "Einträge mit Ende vor dem Anfang wurden übersprungen.",
  EMPTY_CUE: "Einträge ohne Text wurden übersprungen.",
  TEXT_CUT: "Zu lange Texte wurden gekürzt.",
  UNSORTED: "Die Einträge waren nicht in Zeitreihenfolge und wurden sortiert.",
  OVERLAP: "Einträge überlappen sich (beide Zeilen werden zusammen gezeigt).",
  VERY_SHORT: "Einträge unter 0,15 Sekunden (kaum lesbar).",
  VERY_LONG: "Einträge über 15 Sekunden.",
  LONG_LINE: "Sehr lange Zeilen.",
  BEYOND_VIDEO: "Der Untertitel reicht über das Ende des Videos hinaus (falsche Datei oder falsche Zeitbasis?).",
  ENDS_EARLY: "Der Untertitel deckt nur einen kleinen Teil des Videos ab.",
};

export const clock = (ms: number | null | undefined) => {
  if (ms == null) return "—";
  const s = Math.floor(ms / 1000);
  return s >= 3600 ? `${Math.floor(s / 3600)}:${String(Math.floor((s % 3600) / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}` : `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
};

function Warnings({ warnings, testId }: { warnings: SubtitleWarning[]; testId: string }) {
  if (!warnings.length) return <p className="flex items-center gap-1.5 text-xs text-[var(--admin-success)]" data-testid={`${testId}-ok`}><CheckCircle2 size={13} /> Keine Auffälligkeiten.</p>;
  return (
    <ul className="space-y-1 text-xs text-[var(--admin-warning)]" data-testid={testId}>
      {warnings.map((w) => <li key={w.code} className="flex items-start gap-1.5" data-code={w.code} title={w.detail}><AlertTriangle size={13} className="mt-0.5 shrink-0" /><span>{WARNING_DE[w.code] ?? w.detail}{w.count > 1 ? ` (${w.count}×)` : ""}</span></li>)}
    </ul>
  );
}

function ReportBox({ report, videoMs, testId }: { report: SubtitleReport; videoMs: number | null; testId: string }) {
  return (
    <div className="space-y-1.5 rounded-lg bg-[var(--admin-hover)] p-3 text-xs text-[var(--admin-text-secondary)]" data-testid={testId}>
      <p><b className="text-[var(--admin-text-primary)]">{report.cue_count}</b> Zeilen · {report.format.toUpperCase()} · {report.encoding} · {clock(report.first_ms)} – {clock(report.last_ms)}{videoMs ? ` · Video ${clock(videoMs)}` : " · Videolänge unbekannt"}</p>
      <Warnings warnings={report.warnings} testId={`${testId}-warnings`} />
    </div>
  );
}

type Run = (label: string, job: () => Promise<AdminItem | void>, ok: string) => Promise<boolean>;

function saveBlob(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Admin → Film → Untertitel.
 * - KI-Untertitel: the film's audio → timed text (language detected or chosen) → translations; a background job with live status
 *   (wartet / läuft x von y / fertig / fehlgeschlagen + wiederholen / abbrechen). The result is a DRAFT: students see it only after "Freigeben".
 * - One card per language (Deutsch, Usbekisch, Englisch, Russisch): status (Entwurf / Freigegeben) and source, check a file before saving, upload /
 *   replace (an upload is visible at once), preview, edit the lines, approve / withdraw, translate into another language, SRT / VTT download,
 *   re-check, re-assign the language, delete. */
export default function SubtitleManager({ film, busy, run, onFilm }: { film: AdminItem; busy: string | null; run: Run; onFilm?: (item: AdminItem) => void }) {
  const [preview, setPreview] = useState<SubtitlePreview | null>(null);
  const [editing, setEditing] = useState<SubtitlePreview | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const tracks = film.subtitles ?? [];
  const extra = tracks.filter((s) => !LANGS.some(([c]) => c === s.language));

  async function openPreview(track: AdminSubtitle, edit = false) {
    setPreviewError(null);
    try {
      const data = await getSubtitlePreview(film.id, track.id);
      if (edit) { setEditing(data); setPreview(null); } else { setPreview(data); setEditing(null); }
    } catch (err) { setPreview(null); setEditing(null); setPreviewError(medienError(err)); }
  }

  return (
    <div className="space-y-3" data-testid="film-subtitles">
      <AiPanel film={film} busy={busy} onFilm={onFilm} />
      {LANGS.map(([code, name]) => (
        <LangCard key={code} film={film} code={code} name={name} track={tracks.find((s) => s.language === code) ?? null} tracks={tracks} busy={busy} run={run}
                  onPreview={(t) => void openPreview(t)} onEdit={(t) => void openPreview(t, true)} />
      ))}
      {extra.map((s) => (
        <div key={s.id} className="flex items-center gap-2 rounded-xl p-3 text-sm ring-1 ring-[var(--admin-border)]" data-testid="film-subtitle" data-language={s.language}>
          <span className="flex-1">{s.label} <span className="text-xs text-[var(--admin-text-muted)]">({s.language}) · {s.cue_count} Zeilen</span></span>
          <AdminButton size="sm" variant="secondary" onClick={() => void openPreview(s)}><Eye size={13} /></AdminButton>
          <AdminButton size="sm" variant="danger" disabled={!!busy} onClick={() => void run("Untertitel löschen …", () => deleteSubtitle(film.id, s.id), "Untertitel gelöscht.")} aria-label={`${s.label} löschen`}><Trash2 size={12} /></AdminButton>
        </div>
      ))}
      {previewError && <p role="alert" className="text-sm text-[var(--admin-danger)]" data-testid="sub-preview-error">{previewError}</p>}
      {preview && <PreviewPanel preview={preview} onClose={() => setPreview(null)} />}
      {editing && <CueEditor film={film} preview={editing} run={run} onClose={() => setEditing(null)} />}
    </div>
  );
}

// ---------------- AI panel ----------------

function jobTitle(job: SubtitleJob): string {
  if (job.kind === "TRANSCRIBE") {
    const spoken = job.detected_language ? ALL_LANGS[job.detected_language] : job.language === "auto" ? "Sprache wird erkannt" : ALL_LANGS[job.language];
    return `Transkription der Tonspur → ${spoken ?? job.language}`;
  }
  return `Übersetzung ${ALL_LANGS[job.detected_language ?? ""] ?? "Original"} → ${ALL_LANGS[job.language] ?? job.language}`;
}

function AiPanel({ film, busy, onFilm }: { film: AdminItem; busy: string | null; onFilm?: (item: AdminItem) => void }) {
  const [language, setLanguage] = useState("auto");
  const [targets, setTargets] = useState<string[]>(["uz"]);
  const [replace, setReplace] = useState(false);
  const [working, setWorking] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const status = useQuery<SubtitleAiStatus>({ queryKey: ["admin-subtitle-ai-status"], queryFn: getSubtitleAiStatus, staleTime: 60_000 });
  const jobs = useQuery<SubtitleJob[]>({
    queryKey: ["admin-subtitle-jobs", film.id], queryFn: () => getSubtitleJobs(film.id),
    refetchInterval: (q) => ((q.state.data ?? []).some((j) => j.status === "PENDING" || j.status === "PROCESSING") ? 2500 : false),
  });
  const list = useMemo(() => jobs.data ?? [], [jobs.data]);
  const active = list.some((j) => j.status === "PENDING" || j.status === "PROCESSING");
  const transcribing = list.some((j) => j.kind === "TRANSCRIBE" && (j.status === "PENDING" || j.status === "PROCESSING"));

  // a job that finished since the last look: reload the film so the language cards show the new draft
  const seen = useRef<Record<string, string>>({});
  useEffect(() => {
    let changed = false;
    for (const j of list) {
      const before = seen.current[j.id];
      if (before && before !== j.status && (j.status === "COMPLETED" || j.status === "FAILED")) changed = true;
      seen.current[j.id] = j.status;
    }
    if (changed && onFilm) void getFilm(film.id).then(onFilm).catch(() => undefined);
  }, [list, film.id, onFilm]);

  const stt = status.data?.speech_to_text;
  const tr = status.data?.translation;
  const hasVideo = film.file_status === "ok" && !!film.video_size;
  const canStart = !!stt?.configured && !!status.data?.ffmpeg && hasVideo && !transcribing && !working && !busy;
  const toggleTarget = (code: string) => setTargets((t) => (t.includes(code) ? t.filter((x) => x !== code) : [...t, code]));

  async function act(fn: () => Promise<unknown>, ok: string) {
    setWorking(true); setMessage(null);
    try { await fn(); setMessage({ ok: true, text: ok }); await jobs.refetch(); } catch (err) { setMessage({ ok: false, text: medienError(err) }); } finally { setWorking(false); }
  }

  const service = (label: string, s: SubtitleAiStatus["speech_to_text"] | undefined, testId: string) => (
    <p className={`flex items-center gap-1.5 text-xs ${s?.configured ? "text-[var(--admin-success)]" : "text-[var(--admin-danger)]"}`} data-testid={testId} data-configured={s?.configured ? "1" : "0"}>
      {s?.configured ? <CheckCircle2 size={13} /> : <AlertTriangle size={13} />}
      <span>{label}: {s ? (s.configured ? `${s.provider}${s.model ? ` (${s.model})` : ""} eingerichtet` : `nicht eingerichtet — ${s.message ?? ""}`) : "…"}</span>
    </p>
  );

  return (
    <div className="space-y-3 rounded-xl bg-[var(--admin-hover)]/60 p-3 ring-1 ring-[var(--admin-border)]" data-testid="sub-ai">
      <div className="flex items-center gap-2">
        <Sparkles size={16} className="text-[var(--admin-primary)]" />
        <h4 className="text-sm font-semibold text-[var(--admin-text-primary)]">KI-Untertitel aus der Tonspur</h4>
      </div>
      <div className="space-y-1">
        {service("Spracherkennung", stt, "sub-ai-stt")}
        {service("Übersetzung", tr, "sub-ai-translation")}
        {status.data && !status.data.ffmpeg && <p className="text-xs text-[var(--admin-danger)]">FFmpeg fehlt auf dem Server — die Tonspur kann nicht gelesen werden.</p>}
        {!hasVideo && <p className="text-xs text-[var(--admin-warning)]" data-testid="sub-ai-no-video">Zuerst eine Videodatei hochladen (ein externer Link kann nicht transkribiert werden).</p>}
      </div>
      <div className="grid gap-3 sm:grid-cols-[minmax(10rem,14rem)_1fr]">
        <label className="block text-xs text-[var(--admin-text-secondary)]">Sprache im Film
          <AdminSelect className="mt-1 h-9 text-sm" value={language} onChange={(e) => setLanguage(e.target.value)} data-testid="sub-ai-language" aria-label="Sprache im Film">
            <option value="auto">Automatisch erkennen</option>
            {LANGS.map(([c, n]) => <option key={c} value={c}>{n}</option>)}
          </AdminSelect>
        </label>
        <fieldset className="text-xs text-[var(--admin-text-secondary)]">
          <legend>Danach übersetzen in</legend>
          <div className="mt-1.5 flex flex-wrap gap-3">
            {LANGS.filter(([c]) => c !== language).map(([c, n]) => (
              <label key={c} className="flex min-h-[32px] items-center gap-1.5 text-sm text-[var(--admin-text-primary)]">
                <input type="checkbox" checked={targets.includes(c)} onChange={() => toggleTarget(c)} disabled={!tr?.configured} data-testid={`sub-ai-target-${c}`} className="h-4 w-4 accent-[var(--admin-primary)]" /> {n}
              </label>
            ))}
          </div>
        </fieldset>
      </div>
      <label className="flex items-center gap-2 text-xs text-[var(--admin-text-secondary)]">
        <input type="checkbox" checked={replace} onChange={(e) => setReplace(e.target.checked)} data-testid="sub-ai-replace" className="h-4 w-4 accent-[var(--admin-primary)]" />
        Vorhandene Untertitel dieser Sprachen ersetzen (sie werden dann wieder zum Entwurf)
      </label>
      <div className="flex flex-wrap items-center gap-2">
        <AdminButton size="sm" disabled={!canStart} data-testid="sub-ai-start"
                     onClick={() => void act(() => startAiSubtitles(film.id, { language, translate_to: targets.filter((t) => t !== language), replace }), "KI-Auftrag gestartet.")}>
          {working ? <Loader2 size={14} className="animate-spin" /> : <Bot size={14} />} KI-Untertitel erzeugen
        </AdminButton>
        <span className="text-xs text-[var(--admin-text-muted)]">Ergebnis = Entwurf: Studierende sehen ihn erst nach Prüfung und „Freigeben“. Ein Spielfilm braucht einige Minuten.</span>
      </div>
      {message && <p role="status" className={`text-xs ${message.ok ? "text-[var(--admin-success)]" : "text-[var(--admin-danger)]"}`} data-testid="sub-ai-message">{message.text}</p>}

      {!!list.length && (
        <ul className="space-y-1.5" data-testid="sub-jobs">
          {list.map((j) => {
            const pct = j.progress_total ? Math.round((j.progress_done / j.progress_total) * 100) : 0;
            const running = j.status === "PENDING" || j.status === "PROCESSING";
            return (
              <li key={j.id} className="space-y-1 rounded-lg bg-[var(--admin-card)] p-2.5 text-xs ring-1 ring-[var(--admin-border)]" data-testid="sub-job" data-kind={j.kind} data-status={j.status} data-language={j.language}>
                <div className="flex flex-wrap items-center gap-2">
                  {running ? <Loader2 size={13} className="animate-spin text-[var(--admin-primary)]" /> : j.status === "COMPLETED" ? <CheckCircle2 size={13} className="text-[var(--admin-success)]" /> : <AlertTriangle size={13} className="text-[var(--admin-danger)]" />}
                  <span className="flex-1 font-semibold text-[var(--admin-text-primary)]">{jobTitle(j)}</span>
                  <span className="rounded-full bg-[var(--admin-hover)] px-2 py-0.5 font-semibold" data-testid="sub-job-status">
                    {JOB_STATUS_DE[j.status]}{j.status === "PROCESSING" && j.progress_total ? ` · ${j.progress_done} / ${j.progress_total}` : ""}
                  </span>
                  {j.status === "FAILED" && <AdminButton size="sm" variant="secondary" disabled={working} onClick={() => void act(() => retrySubtitleJob(film.id, j.id), "Auftrag läuft wieder (fertige Abschnitte bleiben).")} data-testid="sub-job-retry"><RotateCcw size={12} /> Wiederholen</AdminButton>}
                  {running && <AdminButton size="sm" variant="ghost" disabled={working} onClick={() => void act(() => cancelSubtitleJob(film.id, j.id), "Auftrag abgebrochen.")} data-testid="sub-job-cancel"><Square size={12} /> Abbrechen</AdminButton>}
                </div>
                {running && j.progress_total > 0 && <div className="h-1.5 overflow-hidden rounded-full bg-[var(--admin-hover)]"><div className="h-full bg-[var(--admin-primary)] transition-[width]" style={{ width: `${pct}%` }} /></div>}
                {j.status === "COMPLETED" && <p className="text-[var(--admin-text-muted)]">{j.stats.cues ?? 0} Zeilen{j.stats.speakers_max_per_piece ? ` · bis zu ${j.stats.speakers_max_per_piece} Sprecher je Abschnitt` : ""}{j.model ? ` · ${j.provider}: ${j.model}` : ""} — als Entwurf gespeichert, bitte prüfen und freigeben.</p>}
                {j.status === "FAILED" && <p className="text-[var(--admin-danger)]" data-testid="sub-job-error">{JOB_ERROR_DE[j.error_code ?? ""] ?? j.error_message ?? j.error_code}{j.error_message && JOB_ERROR_DE[j.error_code ?? ""] && j.error_code !== "CANCELLED" ? <span className="text-[var(--admin-text-muted)]"> ({j.error_message})</span> : null}</p>}
              </li>
            );
          })}
        </ul>
      )}
      {active && <p className="text-xs text-[var(--admin-text-muted)]">Der Auftrag läuft auf dem Server weiter, auch wenn dieses Fenster geschlossen wird.</p>}
    </div>
  );
}

// ---------------- one language ----------------

function LangCard({ film, code, name, track, tracks, busy, run, onPreview, onEdit }: {
  film: AdminItem; code: string; name: string; track: AdminSubtitle | null; tracks: AdminSubtitle[]; busy: string | null; run: Run;
  onPreview: (t: AdminSubtitle) => void; onEdit: (t: AdminSubtitle) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [check, setCheck] = useState<SubtitleCheck | null>(null);
  const [checkError, setCheckError] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const free = Object.keys(ALL_LANGS).filter((l) => l !== code && !tracks.some((s) => s.language === l));
  const draft = track?.status === "DRAFT";

  const pick = (f: File | null) => { setFile(f); setCheck(null); setCheckError(null); };
  async function runCheck() {
    if (!file) return;
    setChecking(true); setCheck(null); setCheckError(null);
    try { setCheck(await checkSubtitle(film.id, file)); } catch (err) { setCheckError(medienError(err)); } finally { setChecking(false); }
  }
  const reset = () => { setFile(null); setCheck(null); setCheckError(null); if (input.current) input.current.value = ""; };
  async function download(format: "srt" | "vtt") {
    if (!track) return;
    await run(`${format.toUpperCase()} wird geladen …`, async () => { const { blob, name: fileName } = await downloadSubtitle(film.id, track.id, format); saveBlob(blob, fileName); }, "Datei heruntergeladen.");
  }

  return (
    <div className="space-y-2 rounded-xl p-3 ring-1 ring-[var(--admin-border)]" data-testid="film-subtitle" data-language={code} data-present={track ? "1" : "0"} data-status={track?.status ?? ""}>
      <div className="flex flex-wrap items-center gap-2">
        <h4 className="text-sm font-semibold text-[var(--admin-text-primary)]">{name} <span className="text-xs font-normal text-[var(--admin-text-muted)]">({code})</span></h4>
        {track ? (
          <span className="rounded-full bg-[var(--admin-success)]/10 px-2 py-0.5 text-xs font-semibold text-[var(--admin-success)]" data-testid={`sub-status-${code}`}>
            Vorhanden · {track.cue_count ? `${track.cue_count} Zeilen · ${track.format?.toUpperCase() ?? ""} · bis ${clock(track.last_ms)}` : "noch nicht geprüft"}
          </span>
        ) : <span className="rounded-full bg-[var(--admin-hover)] px-2 py-0.5 text-xs text-[var(--admin-text-muted)]" data-testid={`sub-status-${code}`}>Nicht vorhanden</span>}
        {track && (
          <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${draft ? "bg-[var(--admin-warning)]/15 text-[var(--admin-warning)]" : "bg-[var(--admin-primary)]/10 text-[var(--admin-primary)]"}`} data-testid={`sub-state-${code}`}>
            {draft ? "Entwurf — für Studierende unsichtbar" : "Freigegeben"}
          </span>
        )}
        {track?.source && <span className="text-xs text-[var(--admin-text-muted)]" data-testid={`sub-source-${code}`}>{SOURCE_DE[track.source]}{track.source === "TRANSLATION" && track.source_language ? ` aus ${ALL_LANGS[track.source_language] ?? track.source_language}` : ""}{track.edited_at ? " · bearbeitet" : ""}</span>}
        {track && track.file_status !== "ok" && <span className="text-xs text-[var(--admin-danger)]">{FILE_DE[track.file_status]}</span>}
        {track?.warnings.length ? <span className="rounded-full bg-[var(--admin-warning)]/10 px-2 py-0.5 text-xs font-semibold text-[var(--admin-warning)]" data-testid={`sub-warn-count-${code}`}>{track.warnings.length} Hinweis{track.warnings.length > 1 ? "e" : ""}</span> : null}
      </div>
      {track?.warnings.length ? <Warnings warnings={track.warnings} testId={`sub-warnings-${code}`} /> : null}
      {track?.original_name && <p className="text-xs text-[var(--admin-text-muted)]">Quelle: {track.original_name}{track.file_size ? ` · gespeichert als WebVTT (${fileSize(track.file_size)})` : ""}</p>}

      <div className="flex flex-wrap items-end gap-2">
        <input ref={input} type="file" accept=".vtt,.srt,text/vtt,text/plain" onChange={(e) => pick(e.target.files?.[0] ?? null)} data-testid={`sub-file-${code}`} aria-label={`${name}: Datei (.srt oder .vtt)`}
               className="block min-w-[12rem] flex-1 text-sm text-[var(--admin-text-secondary)] file:mr-3 file:rounded-lg file:border-0 file:bg-[var(--admin-hover)] file:px-3 file:py-2 file:text-sm file:font-semibold" />
        <AdminButton size="sm" variant="secondary" disabled={!file || checking || !!busy} onClick={() => void runCheck()} data-testid={`sub-check-${code}`}><ScanSearch size={14} /> Prüfen</AdminButton>
        <AdminButton size="sm" disabled={!file || !!busy} data-testid={`sub-upload-${code}`}
                     onClick={() => void run("Untertitel hochladen …", async () => { const out = await uploadSubtitle(film.id, code, file!); reset(); return out; }, track ? "Untertitel ersetzt." : "Untertitel gespeichert.")}>
          <Upload size={14} /> {track ? "Ersetzen" : "Hochladen"}</AdminButton>
        {file && <AdminButton size="sm" variant="ghost" onClick={reset} aria-label="Auswahl verwerfen"><X size={14} /></AdminButton>}
      </div>
      {checking && <p className="text-xs text-[var(--admin-text-muted)]">Datei wird geprüft …</p>}
      {checkError && <p role="alert" className="text-xs text-[var(--admin-danger)]" data-testid={`sub-check-error-${code}`}>{checkError}</p>}
      {check && <ReportBox report={check.report} videoMs={check.video_ms} testId={`sub-report-${code}`} />}

      {track && (
        <div className="flex flex-wrap items-center gap-2 border-t border-[var(--admin-border)] pt-2">
          {draft
            ? <AdminButton size="sm" disabled={!!busy} onClick={() => void run("Freigeben …", () => approveSubtitle(film.id, track.id, true), `${name}: freigegeben — Studierende sehen ihn jetzt.`)} data-testid={`sub-approve-${code}`}><BadgeCheck size={13} /> Freigeben</AdminButton>
            : <AdminButton size="sm" variant="secondary" disabled={!!busy} onClick={() => void run("Zurückziehen …", () => approveSubtitle(film.id, track.id, false), `${name}: zurückgezogen (Entwurf).`)} data-testid={`sub-withdraw-${code}`}><EyeOff size={13} /> Zurückziehen</AdminButton>}
          <AdminButton size="sm" variant="secondary" disabled={!!busy} onClick={() => onPreview(track)} data-testid={`sub-preview-${code}`}><Eye size={13} /> Vorschau</AdminButton>
          <AdminButton size="sm" variant="secondary" disabled={!!busy} onClick={() => onEdit(track)} data-testid={`sub-edit-${code}`}><Pencil size={13} /> Bearbeiten</AdminButton>
          <AdminButton size="sm" variant="secondary" disabled={!!busy} onClick={() => void run("Untertitel prüfen …", () => recheckSubtitle(film.id, track.id), "Untertitel geprüft.")} data-testid={`sub-recheck-${code}`}><RefreshCw size={13} /> Neu prüfen</AdminButton>
          <AdminButton size="sm" variant="ghost" disabled={!!busy} onClick={() => void download("srt")} data-testid={`sub-download-srt-${code}`}><Download size={13} /> SRT</AdminButton>
          <AdminButton size="sm" variant="ghost" disabled={!!busy} onClick={() => void download("vtt")} data-testid={`sub-download-vtt-${code}`}><Download size={13} /> VTT</AdminButton>
          <label className="flex items-center gap-1.5 text-xs text-[var(--admin-text-muted)]"><Languages size={13} /> Übersetzen nach
            <AdminSelect className="h-8 w-32 text-xs" value="" disabled={!!busy} aria-label={`${name}: übersetzen nach`} data-testid={`sub-translate-${code}`}
                         onChange={(e) => {
                           const target = e.target.value;
                           if (!target) return;
                           const exists = tracks.some((s) => s.language === target);
                           if (exists && !window.confirm(`${ALL_LANGS[target]} gibt es schon. Durch eine neue KI-Übersetzung (Entwurf) ersetzen?`)) return;
                           void run("Übersetzung wird gestartet …", async () => {
                             await translateSubtitle(film.id, track.id, target, exists);
                             void queryClient.invalidateQueries({ queryKey: ["admin-subtitle-jobs", film.id] });
                           }, `Übersetzung nach ${ALL_LANGS[target]} gestartet (siehe KI-Aufträge).`);
                         }}>
              <option value="">—</option>{Object.keys(ALL_LANGS).filter((l) => l !== code).map((l) => <option key={l} value={l}>{ALL_LANGS[l]}</option>)}
            </AdminSelect></label>
          {free.length > 0 && (
            <label className="flex items-center gap-1.5 text-xs text-[var(--admin-text-muted)]">Sprache zuweisen
              <AdminSelect className="h-8 w-32 text-xs" value="" disabled={!!busy} aria-label={`${name}: Sprache zuweisen`} data-testid={`sub-lang-${code}`}
                           onChange={(e) => { const next = e.target.value; if (next) void run("Sprache ändern …", () => updateSubtitle(film.id, track.id, { language: next }), `Sprache geändert: ${ALL_LANGS[next]}.`); }}>
                <option value="">—</option>{free.map((l) => <option key={l} value={l}>{ALL_LANGS[l]}</option>)}
              </AdminSelect></label>
          )}
          <span className="flex-1" />
          <AdminButton size="sm" variant="danger" disabled={!!busy} onClick={() => void run("Untertitel löschen …", () => deleteSubtitle(film.id, track.id), "Untertitel gelöscht.")} aria-label={`${name} löschen`} data-testid={`sub-delete-${code}`}><Trash2 size={13} /></AdminButton>
        </div>
      )}
    </div>
  );
}

// ---------------- preview ----------------

/** The stored track as plain text: report, a time slider that shows what the student would see at that second, and the whole cue list. */
function PreviewPanel({ preview, onClose }: { preview: SubtitlePreview; onClose: () => void }) {
  const end = Math.max(preview.report.last_ms ?? 0, 1000);
  const [ms, setMs] = useState(preview.report.first_ms ?? 0);
  const cues = preview.cues as Cue[];
  const now = activeCues(cues, ms);
  return (
    <div className="space-y-3 rounded-xl bg-[var(--admin-hover)] p-4" data-testid="sub-preview-panel" data-language={preview.language}>
      <div className="flex items-center gap-2">
        <h4 className="flex-1 text-sm font-semibold text-[var(--admin-text-primary)]">Vorschau: {preview.label} ({preview.language}){preview.status === "DRAFT" ? " · Entwurf" : ""}</h4>
        <AdminButton size="sm" variant="ghost" onClick={onClose} aria-label="Vorschau schließen" data-testid="sub-preview-close"><X size={14} /></AdminButton>
      </div>
      <ReportBox report={preview.report} videoMs={preview.video_ms} testId="sub-preview-report" />
      <div>
        <input type="range" min={0} max={end} step={250} value={ms} onChange={(e) => setMs(Number(e.target.value))} aria-label="Zeit" data-testid="sub-preview-time" className="w-full accent-[var(--admin-primary)]" />
        <div className="flex justify-between text-xs tabular-nums text-[var(--admin-text-muted)]"><span>{clock(ms)}</span><span>{clock(end)}</span></div>
        <div className="mt-2 flex min-h-[4.5rem] items-end justify-center rounded-lg bg-gradient-to-b from-slate-700 to-slate-900 p-3" data-testid="sub-preview-now">
          {now.length ? <p className="whitespace-pre-line rounded-md bg-black/75 px-3 py-1.5 text-center text-sm font-medium text-white">{now.map((c) => c[2]).join("\n")}</p> : <span className="text-xs text-white/50">— kein Untertitel zu dieser Zeit —</span>}
        </div>
      </div>
      <div className="max-h-64 overflow-y-auto rounded-lg bg-[var(--admin-card,transparent)] ring-1 ring-[var(--admin-border)]">
        <table className="w-full text-left text-xs" data-testid="sub-preview-cues">
          <thead className="sticky top-0 bg-[var(--admin-hover)] text-[var(--admin-text-muted)]"><tr><th className="px-3 py-1.5">Von</th><th>Bis</th><th>Text</th></tr></thead>
          <tbody>
            {cues.map((c, i) => (
              <tr key={i} className="cursor-pointer border-t border-[var(--admin-border)] hover:bg-[var(--admin-hover)]" onClick={() => setMs(c[0])} data-testid="sub-preview-cue">
                <td className="whitespace-nowrap px-3 py-1 tabular-nums">{clock(c[0])}</td><td className="whitespace-nowrap tabular-nums">{clock(c[1])}</td><td className="whitespace-pre-line pr-3">{c[2]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------- editor ----------------

interface Row { key: number; start: string; end: string; text: string }
const PAGE = 40;

/** The admin corrects a track line by line: times (m:ss.mmm) and text, delete a line, add one after it. Saved as a whole (the server
 * cleans and checks it like an upload); the track keeps its status. Long films are paged (40 lines a page) with a text search. */
function CueEditor({ film, preview, run, onClose }: { film: AdminItem; preview: SubtitlePreview; run: Run; onClose: () => void }) {
  const nextKey = useRef(preview.cues.length); // keys of added lines (only read in event handlers)
  const [rows, setRows] = useState<Row[]>(() => preview.cues.map((c, i) => ({ key: i, start: formatCueTime(c[0]), end: formatCueTime(c[1]), text: c[2] })));
  const [page, setPage] = useState(0);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);

  const filtered = useMemo(() => (query.trim() ? rows.filter((r) => r.text.toLowerCase().includes(query.trim().toLowerCase())) : rows), [rows, query]);
  const pages = Math.max(1, Math.ceil(filtered.length / PAGE));
  const shown = filtered.slice(page * PAGE, page * PAGE + PAGE);
  const set = (key: number, patch: Partial<Row>) => { setRows((all) => all.map((r) => (r.key === key ? { ...r, ...patch } : r))); setDirty(true); };
  const remove = (key: number) => { setRows((all) => all.filter((r) => r.key !== key)); setDirty(true); };
  const addAfter = (key: number) => {
    setRows((all) => {
      const i = all.findIndex((r) => r.key === key);
      const from = parseCueTime(all[i]?.end ?? "0") ?? 0;
      const row: Row = { key: nextKey.current++, start: formatCueTime(from + 100), end: formatCueTime(from + 2100), text: "" };
      return [...all.slice(0, i + 1), row, ...all.slice(i + 1)];
    });
    setDirty(true);
  };

  async function save() {
    setError(null);
    const out: PreviewCue[] = [];
    for (const [i, r] of rows.entries()) {
      const start = parseCueTime(r.start);
      const end = parseCueTime(r.end);
      if (start == null || end == null || end <= start) { setError(`Zeile ${i + 1}: ungültige Zeit (Format m:ss.mmm, Ende nach dem Anfang).`); setPage(Math.floor(i / PAGE)); setQuery(""); return; }
      out.push([start, end, r.text]);
    }
    const ok = await run("Untertitel wird gespeichert …", async () => { await saveSubtitleCues(film.id, preview.id, out); return getFilm(film.id); }, "Änderungen gespeichert.");
    if (ok) onClose();
  }

  return (
    <div className="space-y-3 rounded-xl bg-[var(--admin-hover)] p-4" data-testid="sub-editor" data-language={preview.language}>
      <div className="flex flex-wrap items-center gap-2">
        <h4 className="flex-1 text-sm font-semibold text-[var(--admin-text-primary)]">Bearbeiten: {preview.label} ({preview.language}) · {rows.length} Zeilen{preview.status === "DRAFT" ? " · Entwurf" : ""}</h4>
        <input value={query} onChange={(e) => { setQuery(e.target.value); setPage(0); }} placeholder="Text suchen …" aria-label="Text suchen" data-testid="sub-editor-search"
               className="h-8 w-44 rounded-lg bg-[var(--admin-card)] px-2 text-xs text-[var(--admin-text-primary)] outline-none ring-1 ring-[var(--admin-border-strong)]" />
        <AdminButton size="sm" variant="ghost" onClick={() => { if (!dirty || window.confirm("Änderungen verwerfen?")) onClose(); }} aria-label="Editor schließen" data-testid="sub-editor-close"><X size={14} /></AdminButton>
      </div>
      <p className="text-xs text-[var(--admin-text-muted)]">Zeiten als m:ss.mmm (z. B. 1:02.500). Leere Zeilen werden beim Speichern entfernt; Text wird wie ein Upload bereinigt (kein HTML).</p>
      <ol className="space-y-1.5">
        {shown.map((r) => (
          <li key={r.key} className="grid grid-cols-[5.5rem_5.5rem_1fr_auto] items-start gap-1.5" data-testid="sub-editor-row">
            <input value={r.start} onChange={(e) => set(r.key, { start: e.target.value })} aria-label="Von" data-testid="sub-editor-start"
                   className={`h-9 rounded-lg bg-[var(--admin-card)] px-2 text-xs tabular-nums text-[var(--admin-text-primary)] outline-none ring-1 ${parseCueTime(r.start) == null ? "ring-[var(--admin-danger)]" : "ring-[var(--admin-border-strong)]"}`} />
            <input value={r.end} onChange={(e) => set(r.key, { end: e.target.value })} aria-label="Bis" data-testid="sub-editor-end"
                   className={`h-9 rounded-lg bg-[var(--admin-card)] px-2 text-xs tabular-nums text-[var(--admin-text-primary)] outline-none ring-1 ${parseCueTime(r.end) == null ? "ring-[var(--admin-danger)]" : "ring-[var(--admin-border-strong)]"}`} />
            <textarea value={r.text} onChange={(e) => set(r.key, { text: e.target.value })} rows={Math.min(3, Math.max(1, r.text.split("\n").length))} aria-label="Text" data-testid="sub-editor-text"
                      className="min-h-9 w-full resize-y rounded-lg bg-[var(--admin-card)] px-2 py-1.5 text-sm text-[var(--admin-text-primary)] outline-none ring-1 ring-[var(--admin-border-strong)]" />
            <span className="flex gap-1">
              <AdminButton size="sm" variant="ghost" onClick={() => addAfter(r.key)} aria-label="Zeile danach einfügen" data-testid="sub-editor-add"><Plus size={13} /></AdminButton>
              <AdminButton size="sm" variant="ghost" onClick={() => remove(r.key)} aria-label="Zeile löschen" data-testid="sub-editor-remove"><Trash2 size={13} /></AdminButton>
            </span>
          </li>
        ))}
        {!shown.length && <li className="text-xs text-[var(--admin-text-muted)]">Keine Zeile gefunden.</li>}
      </ol>
      <div className="flex flex-wrap items-center gap-2">
        <AdminButton size="sm" variant="secondary" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>Zurück</AdminButton>
        <span className="text-xs tabular-nums text-[var(--admin-text-muted)]">Seite {page + 1} / {pages}</span>
        <AdminButton size="sm" variant="secondary" disabled={page + 1 >= pages} onClick={() => setPage((p) => p + 1)}>Weiter</AdminButton>
        <span className="flex-1" />
        {error && <p role="alert" className="text-xs text-[var(--admin-danger)]" data-testid="sub-editor-error">{error}</p>}
        <AdminButton size="sm" disabled={!dirty} onClick={() => void save()} data-testid="sub-editor-save"><CheckCircle2 size={13} /> Speichern</AdminButton>
      </div>
    </div>
  );
}
