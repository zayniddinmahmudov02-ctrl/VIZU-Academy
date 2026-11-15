"use client";

import { useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, Eye, RefreshCw, ScanSearch, Trash2, Upload, X } from "lucide-react";

import { AdminButton, AdminSelect } from "@/components/admin/admin-ui";
import {
  checkSubtitle, deleteSubtitle, getSubtitlePreview, medienError, recheckSubtitle, updateSubtitle, uploadSubtitle,
  type AdminItem, type AdminSubtitle, type SubtitleCheck, type SubtitlePreview, type SubtitleReport, type SubtitleWarning,
} from "@/features/admin/services/medien-admin-service";
import { activeCues, type Cue } from "@/features/medien/lib/subtitles";

import { FILE_DE, fileSize } from "./shared";

const LANGS = [["de", "Deutsch"], ["uz", "O'zbekcha"], ["en", "English"]] as const;
const ALL_LANGS: Record<string, string> = { de: "Deutsch", uz: "O'zbekcha", en: "English", ru: "Русский" };

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

/** Admin → Film → Untertitel: one card each for Deutsch, Usbekisch and Englisch. Per language: check a file before saving (format, time stamps,
 * cleaning, fit to the video length), upload / replace, preview (cue list + scrubbing), re-check, re-assign the language, delete. */
export default function SubtitleManager({ film, busy, run }: { film: AdminItem; busy: string | null; run: Run }) {
  const [preview, setPreview] = useState<SubtitlePreview | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const tracks = film.subtitles ?? [];
  const extra = tracks.filter((s) => !LANGS.some(([c]) => c === s.language));

  async function openPreview(track: AdminSubtitle) {
    setPreviewError(null);
    try { setPreview(await getSubtitlePreview(film.id, track.id)); } catch (err) { setPreview(null); setPreviewError(medienError(err)); }
  }

  return (
    <div className="space-y-3" data-testid="film-subtitles">
      {LANGS.map(([code, name]) => (
        <LangCard key={code} film={film} code={code} name={name} track={tracks.find((s) => s.language === code) ?? null} tracks={tracks} busy={busy} run={run} onPreview={openPreview} />
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
    </div>
  );
}

function LangCard({ film, code, name, track, tracks, busy, run, onPreview }: {
  film: AdminItem; code: string; name: string; track: AdminSubtitle | null; tracks: AdminSubtitle[]; busy: string | null; run: Run; onPreview: (t: AdminSubtitle) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [check, setCheck] = useState<SubtitleCheck | null>(null);
  const [checkError, setCheckError] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const free = Object.keys(ALL_LANGS).filter((l) => l !== code && !tracks.some((s) => s.language === l));

  const pick = (f: File | null) => { setFile(f); setCheck(null); setCheckError(null); };
  async function runCheck() {
    if (!file) return;
    setChecking(true); setCheck(null); setCheckError(null);
    try { setCheck(await checkSubtitle(film.id, file)); } catch (err) { setCheckError(medienError(err)); } finally { setChecking(false); }
  }
  const reset = () => { setFile(null); setCheck(null); setCheckError(null); if (input.current) input.current.value = ""; };

  return (
    <div className="space-y-2 rounded-xl p-3 ring-1 ring-[var(--admin-border)]" data-testid="film-subtitle" data-language={code} data-present={track ? "1" : "0"}>
      <div className="flex flex-wrap items-center gap-2">
        <h4 className="text-sm font-semibold text-[var(--admin-text-primary)]">{name} <span className="text-xs font-normal text-[var(--admin-text-muted)]">({code})</span></h4>
        {track ? (
          <span className="rounded-full bg-[var(--admin-success)]/10 px-2 py-0.5 text-xs font-semibold text-[var(--admin-success)]" data-testid={`sub-status-${code}`}>
            Vorhanden · {track.cue_count ? `${track.cue_count} Zeilen · ${track.format?.toUpperCase() ?? ""} · bis ${clock(track.last_ms)}` : "noch nicht geprüft"}
          </span>
        ) : <span className="rounded-full bg-[var(--admin-hover)] px-2 py-0.5 text-xs text-[var(--admin-text-muted)]" data-testid={`sub-status-${code}`}>Nicht vorhanden</span>}
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
          <AdminButton size="sm" variant="secondary" disabled={!!busy} onClick={() => onPreview(track)} data-testid={`sub-preview-${code}`}><Eye size={13} /> Vorschau</AdminButton>
          <AdminButton size="sm" variant="secondary" disabled={!!busy} onClick={() => void run("Untertitel prüfen …", () => recheckSubtitle(film.id, track.id), "Untertitel geprüft.")} data-testid={`sub-recheck-${code}`}><RefreshCw size={13} /> Neu prüfen</AdminButton>
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

/** The stored track as plain text: report, a time slider that shows what the student would see at that second, and the whole cue list. */
function PreviewPanel({ preview, onClose }: { preview: SubtitlePreview; onClose: () => void }) {
  const end = Math.max(preview.report.last_ms ?? 0, 1000);
  const [ms, setMs] = useState(preview.report.first_ms ?? 0);
  const cues = preview.cues as Cue[];
  const now = activeCues(cues, ms);
  return (
    <div className="space-y-3 rounded-xl bg-[var(--admin-hover)] p-4" data-testid="sub-preview-panel" data-language={preview.language}>
      <div className="flex items-center gap-2">
        <h4 className="flex-1 text-sm font-semibold text-[var(--admin-text-primary)]">Vorschau: {preview.label} ({preview.language})</h4>
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
