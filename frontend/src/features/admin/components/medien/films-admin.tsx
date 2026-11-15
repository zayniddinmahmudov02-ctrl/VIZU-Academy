"use client";

/* eslint-disable @next/next/no-img-element -- admin thumbnails come from the cacheable cover endpoint */

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Captions, Clapperboard, Eye, EyeOff, FileVideo, Gauge, Info, Link2, Pencil, Plus, ShieldCheck, Star, Tag, Trash2, Upload } from "lucide-react";

import { AdminButton, AdminCard, AdminInput, AdminLabel, AdminPageHeader, AdminSelect } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import FormDialog from "@/components/admin/form-dialog";
import {
  createItem, deleteItem, deleteRendition, getCategories, listItems, medienError, setExternalUrl, updateItem, uploadCover, uploadFilmVideo, type AdminItem,
} from "@/features/admin/services/medien-admin-service";
import { mediaUrl } from "@/features/medien/services/medien-service";

import { CategoryManager, ContentFields, contentFrom, contentInput, emptyContent, FILE_DE, FilePick, fileSize, MedienTabs, ProgressBar, StatusPill, type ContentValues } from "./shared";
import SubtitleManager, { clock } from "./subtitle-manager";

const PROCESSING: Record<string, string> = { NONE: "Kein Video", UPLOADING: "Wird hochgeladen …", READY: "Bereit", FAILED: "Fehlgeschlagen" };
const QUALITIES = ["360p", "480p", "720p", "1080p"] as const;
const FORMAT_DE: Record<string, string> = { mp4: "MP4", mov: "MOV (QuickTime)", webm: "WebM" };

/** Admin → Medien → Filme: films with poster, video (chunked upload with progress, extra qualities) or an https streaming link, subtitles in
 * German, Uzbek and English (WebVTT or SRT: check, upload, replace, preview, re-assign, delete), category, genre, level, FREE / PAID, special offer,
 * featured, Published / Draft / Hidden. The dialog has four sections: Video-Informationen, Videodatei, Untertitel, Zugang. */
export default function FilmsAdmin() {
  const queryClient = useQueryClient();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<AdminItem | "new" | null>(null);
  const [deleting, setDeleting] = useState<AdminItem | null>(null);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const films = useQuery({ queryKey: ["admin-medien-films", q, status, page], queryFn: () => listItems("FILM", { q, status, page, page_size: 25 }), placeholderData: (p) => p });
  const categories = useQuery({ queryKey: ["admin-medien-categories", "FILM"], queryFn: () => getCategories("FILM") });
  const refresh = () => void queryClient.invalidateQueries({ queryKey: ["admin-medien-films"] });
  const patch = useMutation({ mutationFn: ({ f, data }: { f: AdminItem; data: Parameters<typeof updateItem>[2] }) => updateItem("FILM", f.id, data), onSuccess: refresh, onError: (e) => setMessage({ ok: false, text: medienError(e) }) });
  const remove = useMutation({ mutationFn: (f: AdminItem) => deleteItem("FILM", f.id), onSuccess: () => { setDeleting(null); setMessage({ ok: true, text: "Film gelöscht (Video, Poster und Untertitel entfernt)." }); refresh(); }, onError: (e) => { setDeleting(null); setMessage({ ok: false, text: medienError(e) }); } });
  const catName = (id?: string | null) => categories.data?.find((c) => c.id === id)?.name ?? "—";
  const total = films.data?.total ?? 0;

  return (
    <div data-testid="films-admin">
      <AdminPageHeader title="Medien · Filme" description="Filme hochladen und verwalten: Poster, Video oder Streaming-Link, Untertitel Deutsch / Usbekisch / Englisch, Kategorie, Niveau, kostenlos oder kostenpflichtig." action={<AdminButton onClick={() => setEditing("new")} data-testid="film-new"><Plus size={16} /> Neuer Film</AdminButton>} />
      <MedienTabs />
      <AdminCard className="mb-5"><h2 className="mb-3 text-sm font-semibold text-[var(--admin-text-primary)]">Kategorien</h2><CategoryManager kind="FILM" /></AdminCard>
      {message && <p role="status" className={`mb-4 rounded-xl px-4 py-2.5 text-sm ${message.ok ? "bg-[var(--admin-success)]/10 text-[var(--admin-success)]" : "bg-[var(--admin-danger)]/10 text-[var(--admin-danger)]"}`} data-testid="films-message">{message.text}</p>}
      <div className="mb-4 flex flex-wrap gap-2">
        <AdminInput className="w-64" placeholder="Titel suchen …" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} aria-label="Suchen" data-testid="films-search" />
        <AdminSelect className="w-44" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} aria-label="Status"><option value="">Alle Status</option><option value="PUBLISHED">Veröffentlicht</option><option value="DRAFT">Entwurf</option><option value="HIDDEN">Ausgeblendet</option></AdminSelect>
      </div>
      <AdminCard className="overflow-x-auto p-0">
        <table className="w-full min-w-[920px] text-left text-sm" data-testid="films-table">
          <thead><tr className="text-xs uppercase text-[var(--admin-text-muted)]"><th className="p-3">Film</th><th>Kategorie</th><th>Niveau</th><th>Zugang</th><th>Status</th><th>Video</th><th>Untertitel</th><th>Aufrufe</th><th className="pr-3 text-right">Aktionen</th></tr></thead>
          <tbody>
            {(films.data?.items ?? []).map((f) => (
              <tr key={f.id} className="border-t border-[var(--admin-border)]" data-testid="film-row" data-title={f.title}>
                <td className="p-3"><div className="flex items-center gap-3"><span className="h-14 w-10 shrink-0 overflow-hidden rounded bg-[var(--admin-hover)]">{f.cover_url && <img src={mediaUrl(f.cover_url)} alt="" className="h-full w-full object-cover" loading="lazy" />}</span>
                  <span className="min-w-0"><span className="block truncate font-semibold text-[var(--admin-text-primary)]">{f.title}</span><span className="text-xs text-[var(--admin-text-muted)]">{f.genre ?? "—"}{f.year ? ` · ${f.year}` : ""}{f.duration_minutes ? ` · ${f.duration_minutes} Min.` : ""}{f.is_featured ? " · ★" : ""}</span></span></div></td>
                <td>{catName(f.category_id)}</td><td>{f.level ?? "—"}</td><td>{f.access_type === "FREE" ? "Kostenlos" : `${new Intl.NumberFormat("de-DE").format(f.price ?? 0)} UZS`}</td>
                <td><StatusPill status={f.status} /></td>
                <td><span className={f.processing_status === "READY" || f.external_url ? "" : "text-[var(--admin-warning)]"}>{f.external_url && f.processing_status !== "READY" ? "Externer Link" : PROCESSING[f.processing_status ?? "NONE"]}</span>{f.video_size ? <span className="block text-xs text-[var(--admin-text-muted)]">{fileSize(f.video_size)}</span> : null}</td>
                <td>{f.subtitles?.length ? f.subtitles.map((s) => s.language.toUpperCase()).join(" · ") : "—"}</td><td>{f.views ?? 0}</td>
                <td className="pr-3"><div className="flex justify-end gap-1">
                  <AdminButton size="sm" variant="secondary" onClick={() => setEditing(f)} aria-label={`${f.title} bearbeiten`} data-testid="film-edit"><Pencil size={13} /></AdminButton>
                  <AdminButton size="sm" variant="secondary" onClick={() => patch.mutate({ f, data: { status: f.status === "PUBLISHED" ? "HIDDEN" : "PUBLISHED" } })} aria-label={f.status === "PUBLISHED" ? "Ausblenden" : "Veröffentlichen"} data-testid="film-toggle">{f.status === "PUBLISHED" ? <EyeOff size={13} /> : <Eye size={13} />}</AdminButton>
                  <AdminButton size="sm" variant="secondary" disabled={f.access_type !== "PAID"} onClick={() => patch.mutate({ f, data: { is_special_offer: !f.is_special_offer } })} aria-label="Sonderangebot an/aus" data-testid="film-offer"><Tag size={13} className={f.is_special_offer ? "text-[var(--admin-primary)]" : ""} /></AdminButton>
                  <AdminButton size="sm" variant="secondary" onClick={() => patch.mutate({ f, data: { is_featured: !f.is_featured } })} aria-label="Empfohlen an/aus" data-testid="film-featured"><Star size={13} className={f.is_featured ? "fill-current text-[var(--admin-primary)]" : ""} /></AdminButton>
                  <AdminButton size="sm" variant="danger" onClick={() => setDeleting(f)} aria-label={`${f.title} löschen`} data-testid="film-delete"><Trash2 size={13} /></AdminButton>
                </div></td>
              </tr>
            ))}
            {films.data && !films.data.items.length && <tr><td colSpan={9} className="p-8 text-center text-[var(--admin-text-muted)]">Keine Filme.</td></tr>}
          </tbody>
        </table>
      </AdminCard>
      {total > 25 && <div className="mt-3 flex items-center justify-center gap-3 text-sm"><AdminButton size="sm" variant="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>Zurück</AdminButton><span>{page} / {Math.ceil(total / 25)}</span><AdminButton size="sm" variant="secondary" disabled={page >= Math.ceil(total / 25)} onClick={() => setPage(page + 1)}>Weiter</AdminButton></div>}
      {editing && <FilmDialog key={editing === "new" ? "new" : editing.id} initial={editing === "new" ? null : editing} categories={(categories.data ?? []).map((c) => ({ id: c.id, name: c.name }))} onClose={() => { setEditing(null); refresh(); }} />}
      <ConfirmDialog open={!!deleting} onOpenChange={(o) => !o && setDeleting(null)} title="Film löschen" description={`„${deleting?.title ?? ""}“ wird mit Video, Poster und Untertiteln gelöscht. Fortschritte und Kaufanfragen dazu werden entfernt.`} isPending={remove.isPending} onConfirm={() => deleting && remove.mutate(deleting)} />
    </div>
  );
}

function Section({ id, title, icon, hint, children }: { id: string; title: string; icon: React.ReactNode; hint?: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3 rounded-xl p-4 ring-1 ring-[var(--admin-border)]" data-testid={`section-${id}`}>
      <div>
        <h3 className="flex items-center gap-2 text-sm font-semibold text-[var(--admin-text-primary)]">{icon} {title}</h3>
        {hint && <p className="mt-0.5 text-xs text-[var(--admin-text-muted)]">{hint}</p>}
      </div>
      {children}
    </section>
  );
}

function FilmDialog({ initial, categories, onClose }: { initial: AdminItem | null; categories: { id: string; name: string }[]; onClose: () => void }) {
  const [item, setItem] = useState<AdminItem | null>(initial);
  const [values, setValues] = useState<ContentValues>(initial ? contentFrom(initial) : emptyContent());
  const [genre, setGenre] = useState(initial?.genre ?? "");
  const [category, setCategory] = useState(initial?.category_id ?? "");
  const [year, setYear] = useState(initial?.year ? String(initial.year) : "");
  const [minutes, setMinutes] = useState(initial?.duration_minutes ? String(initial.duration_minutes) : "");
  const [poster, setPoster] = useState<File | null>(null);
  const [video, setVideo] = useState<File | null>(null);
  const [link, setLink] = useState(initial?.external_url ?? "");
  const [quality, setQuality] = useState<string>("720p");
  const [qualityFile, setQualityFile] = useState<File | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [percent, setPercent] = useState(0);
  const [note, setNote] = useState<{ ok: boolean; text: string } | null>(null);

  const run = async (label: string, job: () => Promise<AdminItem | void>, ok: string) => {
    setNote(null); setBusy(label); setPercent(0);
    try { const out = await job(); if (out) setItem(out); setNote({ ok: true, text: ok }); return true; }
    catch (err) { setNote({ ok: false, text: medienError(err) }); return false; }
    finally { setBusy(null); }
  };

  async function save() {
    await run("Speichern …", async () => {
      const data = { ...contentInput(values), genre: genre.trim() || null, category_id: category || null, year: year ? Number(year) : null, duration_minutes: minutes ? Number(minutes) : null };
      let saved = item ? await updateItem("FILM", item.id, data) : await createItem("FILM", data);
      setItem(saved);
      if (poster) { setBusy("Poster wird hochgeladen …"); saved = await uploadCover("FILM", saved.id, poster, setPercent); setPoster(null); }
      return saved;
    }, "Gespeichert.");
  }

  const busyUpload = !!busy && (busy.includes("hochgeladen"));
  const ready = item?.processing_status === "READY" && item.file_status === "ok";
  const renditions = item?.renditions ?? [];
  return (
    <FormDialog open onOpenChange={(o) => { if (!o && !busy) onClose(); }} title={item ? "Film bearbeiten" : "Neuer Film"} size="xl"
                footer={<><AdminButton variant="ghost" onClick={onClose} disabled={!!busy} data-testid="film-close">Schließen</AdminButton><AdminButton onClick={save} disabled={!!busy || !values.title.trim()} data-testid="film-save">{busy && !busyUpload ? busy : "Speichern"}</AdminButton></>}>
      <div className="space-y-5" data-testid="film-dialog">
        <Section id="info" title="Video-Informationen" icon={<Info size={15} />}>
          <ContentFields value={values} onChange={setValues} part="info" />
          <div className="grid gap-3 sm:grid-cols-4">
            <div><AdminLabel>Genre</AdminLabel><AdminInput value={genre} onChange={(e) => setGenre(e.target.value)} maxLength={80} data-testid="f-genre" /></div>
            <div><AdminLabel>Kategorie</AdminLabel><AdminSelect value={category} onChange={(e) => setCategory(e.target.value)} data-testid="f-category"><option value="">—</option>{categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</AdminSelect></div>
            <div><AdminLabel>Jahr</AdminLabel><AdminInput type="number" value={year} onChange={(e) => setYear(e.target.value)} data-testid="f-year" /></div>
            <div><AdminLabel>Dauer (Min.)</AdminLabel><AdminInput type="number" min={1} value={minutes} onChange={(e) => setMinutes(e.target.value)} data-testid="f-minutes" /></div>
          </div>
          <FilePick label={item?.has_cover ? "Poster ersetzen" : "Poster (JPG, PNG, WebP)"} accept="image/jpeg,image/png,image/webp" file={poster} onFile={setPoster} testId="film-poster-file" />
        </Section>

        {!item && <p className="rounded-lg bg-[var(--admin-hover)] p-3 text-sm text-[var(--admin-text-secondary)]">Erst speichern — danach können Video, Streaming-Link, weitere Qualitäten und Untertitel hinzugefügt werden.</p>}
        {item && (
          <>
            <Section id="video" title="Videodatei" icon={<FileVideo size={15} />} hint="MP4, MOV oder WebM — das Format wird am Dateiinhalt geprüft, nicht am Namen. Der Upload läuft in Teilen mit Fortschritt; Vorspulen (HTTP Range) funktioniert nach dem Upload.">
              <div className="space-y-1 rounded-lg bg-[var(--admin-hover)] p-3 text-xs text-[var(--admin-text-secondary)]" data-testid="film-video-readiness">
                <p data-testid="film-video-status">Status: <b>{PROCESSING[item.processing_status ?? "NONE"]}</b>{item.video_size ? ` · ${fileSize(item.video_size)}` : ""} · Datei: {FILE_DE[item.file_status]}</p>
                {item.video_format && <p>Format: <b>{FORMAT_DE[item.video_format] ?? item.video_format}</b>{item.video_duration_ms ? ` · Länge ${clock(item.video_duration_ms)}` : ""}{item.original_name ? ` · ${item.original_name}` : ""}</p>}
                <p className={`flex items-center gap-1.5 font-semibold ${ready ? "text-[var(--admin-success)]" : "text-[var(--admin-warning)]"}`} data-testid="film-stream-ready"><ShieldCheck size={13} /> {ready ? "Bereit für Streaming (private Datei, geschützte Adresse, Vorspulen möglich)" : item.external_url ? "Streaming über externen Link" : "Noch nicht bereit für Streaming"}</p>
              </div>
              <div className="flex flex-wrap items-end gap-2">
                <div className="min-w-[16rem] flex-1"><FilePick label="Videodatei (MP4, MOV, WebM — wird in Teilen hochgeladen)" accept="video/mp4,video/quicktime,video/webm" file={video} onFile={setVideo} testId="film-video-file" /></div>
                <AdminButton disabled={!video || !!busy} onClick={() => void run("Video wird hochgeladen …", async () => { const out = await uploadFilmVideo(item.id, video!, setPercent); setVideo(null); return out; }, "Video hochgeladen und bereit.")} data-testid="film-video-upload"><Upload size={15} /> Video hochladen</AdminButton>
              </div>
              {busy === "Video wird hochgeladen …" && <div className="space-y-1"><ProgressBar percent={percent} testId="film-video-progress" /><p className="text-xs text-[var(--admin-text-muted)]">{percent}% · {video ? fileSize(video.size) : ""}</p></div>}

              <div className="space-y-2 border-t border-[var(--admin-border)] pt-3" data-testid="film-renditions">
                <h4 className="flex items-center gap-2 text-sm font-semibold text-[var(--admin-text-primary)]"><Gauge size={14} /> Weitere Qualitäten (optional)</h4>
                <p className="text-xs text-[var(--admin-text-muted)]">Die Hauptdatei ist die Qualität „Original“. Zusätzliche Dateien (z. B. 360p für schwache Verbindungen) erscheinen im Player im Qualitätsmenü; ohne sie gibt es kein Menü.</p>
                <ul className="space-y-1">
                  {renditions.map((r) => (
                    <li key={r.id} className="flex items-center gap-2 text-sm" data-testid="film-rendition" data-label={r.label}><span className="flex-1">{r.label} <span className="text-xs text-[var(--admin-text-muted)]">· {fileSize(r.size)} · {FILE_DE[r.file_status]}</span></span>
                      <AdminButton size="sm" variant="danger" disabled={!!busy} onClick={() => void run("Qualität löschen …", () => deleteRendition(item.id, r.id), "Qualität gelöscht.")} aria-label={`${r.label} löschen`} data-testid="film-rendition-delete"><Trash2 size={12} /></AdminButton></li>
                  ))}
                  {!renditions.length && <li className="text-xs text-[var(--admin-text-muted)]">Keine weiteren Qualitäten.</li>}
                </ul>
                <div className="flex flex-wrap items-end gap-2">
                  <div><AdminLabel>Qualität</AdminLabel><AdminSelect className="w-28" value={quality} onChange={(e) => setQuality(e.target.value)} data-testid="film-quality-label">{QUALITIES.map((q) => <option key={q} value={q}>{q}</option>)}</AdminSelect></div>
                  <div className="min-w-[14rem] flex-1"><FilePick label="Datei für diese Qualität" accept="video/mp4,video/quicktime,video/webm" file={qualityFile} onFile={setQualityFile} testId="film-quality-file" /></div>
                  <AdminButton variant="secondary" disabled={!qualityFile || !!busy || !item.video_size} onClick={() => void run("Qualität wird hochgeladen …", async () => { const out = await uploadFilmVideo(item.id, qualityFile!, setPercent, quality); setQualityFile(null); return out; }, `Qualität ${quality} gespeichert.`)} data-testid="film-quality-upload"><Upload size={15} /> Hochladen</AdminButton>
                </div>
              </div>

              <div className="space-y-2 border-t border-[var(--admin-border)] pt-3">
                <h4 className="flex items-center gap-2 text-sm font-semibold text-[var(--admin-text-primary)]"><Link2 size={15} /> Oder Streaming-Link (https)</h4>
                <div className="flex gap-2"><AdminInput value={link} onChange={(e) => setLink(e.target.value)} placeholder="https://…" aria-label="Streaming-Link" data-testid="film-link" /><AdminButton variant="secondary" disabled={!!busy} onClick={() => void run("Link speichern …", () => setExternalUrl(item.id, link.trim() || null), link.trim() ? "Link gespeichert." : "Link entfernt.")} data-testid="film-link-save">Link speichern</AdminButton></div>
              </div>
            </Section>

            <Section id="subtitles" title="Untertitel" icon={<Captions size={15} />} hint="Pro Sprache eine Datei (.srt oder .vtt, bis 2 MB). Vor dem Speichern prüfen: Format, Zeitangaben, Bereinigung (kein HTML/Skript) und Passung zur Videolänge. Fehlerhafte Zeilen werden übersprungen, der Player bleibt stabil.">
              <SubtitleManager film={item} busy={busy} run={run} />
            </Section>
          </>
        )}

        <Section id="access" title="Zugang" icon={<Clapperboard size={15} />} hint="Kostenlos oder kostenpflichtig (Preis, Sonderangebot), veröffentlicht oder Entwurf.">
          <ContentFields value={values} onChange={setValues} part="access" />
        </Section>

        {busyUpload && busy !== "Video wird hochgeladen …" && <ProgressBar percent={percent} />}
        {note && <p role="status" className={`text-sm ${note.ok ? "text-[var(--admin-success)]" : "text-[var(--admin-danger)]"}`} data-testid="film-note">{note.text}</p>}
      </div>
    </FormDialog>
  );
}
