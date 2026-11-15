"use client";

import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, Eye, EyeOff, ListMusic, Loader2, Pencil, Plus, RotateCw, Star, Trash2, Upload, X } from "lucide-react";

import { AdminButton, AdminCard, AdminInput, AdminLabel, AdminPageHeader, AdminSelect } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import FormDialog from "@/components/admin/form-dialog";
import {
  deletePlaylist, deleteItem, getPlaylistSongs, getPlaylists, listItems, medienError, replaceSongFile, savePlaylist, setPlaylistSongs, updateItem, uploadCover, uploadPlaylistCover,
  uploadSong, type AdminItem, type AdminPlaylist, type Status,
} from "@/features/admin/services/medien-admin-service";

import { FILE_DE, FilePick, fileSize, MedienTabs, ProgressBar, STATUS_DE, StatusPill } from "./shared";

export const BULK_MAX = 10;
const AUDIO = ".mp3,.wav,.m4a,.aac,.ogg,.flac,audio/mpeg,audio/wav,audio/x-wav,audio/mp4,audio/x-m4a,audio/aac,audio/ogg,audio/flac,audio/x-flac";
const dur = (ms?: number | null) => (ms ? `${Math.floor(ms / 60000)}:${String(Math.floor((ms % 60000) / 1000)).padStart(2, "0")}` : "—");
/** what the server read from the file: "MP3 · 3:21 · 192 kbps · 7.7 MB" (parts it could not read are left out) */
const audioInfo = (i: AdminItem) => [i.audio_format?.toUpperCase(), i.duration_ms ? dur(i.duration_ms) : null, i.bitrate_kbps ? `${i.bitrate_kbps} kbps` : null, i.file_size ? fileSize(i.file_size) : null].filter(Boolean).join(" · ");
const META_WARNING = "Die Datei ist gespeichert, aber Dauer / Bitrate konnten nicht gelesen werden (Audioverarbeitung nicht verfügbar oder Datei ungewöhnlich). Der Song ist abspielbar.";

interface Row {
  key: string; file: File; title: string; artist: string; album: string; genre: string; language: string; level: string; access_type: "FREE" | "PAID"; price: string; status: Status;
  cover: File | null; state: "wait" | "up" | "done" | "error"; percent: number; error?: string; info?: string; warn?: string;
}

const newRow = (file: File, d: Defaults): Row => ({ key: `${file.name}-${file.size}-${Math.random().toString(36).slice(2, 7)}`, file, title: file.name.replace(/\.[^.]+$/, ""), ...d, price: "", cover: null, state: "wait", percent: 0 });
interface Defaults { artist: string; album: string; genre: string; language: string; level: string; access_type: "FREE" | "PAID"; status: Status }
const DEFAULTS: Defaults = { artist: "", album: "", genre: "", language: "de", level: "", access_type: "FREE", status: "PUBLISHED" };

/** Bulk upload of up to 10 songs: each file has its own metadata, its own progress bar and its own result — a file that
 * fails (wrong format, too large …) does not stop the others, and failed ones can be retried. */
function BulkUpload({ onDone }: { onDone: () => void }) {
  const [rows, setRows] = useState<Row[]>([]);
  const [defaults, setDefaults] = useState<Defaults>(DEFAULTS);
  const [running, setRunning] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const input = useRef<HTMLInputElement>(null);
  const patch = (key: string, p: Partial<Row>) => setRows((rs) => rs.map((r) => (r.key === key ? { ...r, ...p } : r)));

  function pick(files: FileList | null) {
    if (!files?.length) return;
    const list = Array.from(files);
    const room = BULK_MAX - rows.length;
    setNote(list.length > room ? `Es sind höchstens ${BULK_MAX} Dateien auf einmal möglich — ${list.length - Math.max(0, room)} wurden nicht übernommen.` : null);
    setRows((rs) => [...rs, ...list.slice(0, Math.max(0, room)).map((f) => newRow(f, defaults))]);
    if (input.current) input.current.value = "";
  }

  async function run(only?: string[]) {
    setRunning(true);
    const todo = rows.filter((r) => (only ? only.includes(r.key) : r.state === "wait" || r.state === "error"));
    for (const r of todo) {
      patch(r.key, { state: "up", percent: 0, error: undefined });
      try {
        const saved = await uploadSong(r.file, { title: r.title.trim() || r.file.name, artist: r.artist.trim(), album: r.album.trim(), genre: r.genre.trim(), language: r.language.trim() || "de", level: r.level,
          access_type: r.access_type, price: r.access_type === "PAID" ? r.price : undefined, status: r.status }, r.cover, (percent) => patch(r.key, { percent }));
        patch(r.key, { state: "done", percent: 100, title: saved.title, artist: saved.artist ?? r.artist, info: audioInfo(saved), warn: saved.metadata_status === "FAILED" ? META_WARNING : undefined });
      } catch (err) {
        patch(r.key, { state: "error", error: medienError(err, "Upload fehlgeschlagen.") }); // the next file still goes up
      }
    }
    setRunning(false);
    onDone();
  }

  const done = rows.filter((r) => r.state === "done").length;
  const failed = rows.filter((r) => r.state === "error").length;
  const field = "h-9 px-2 text-xs";
  return (
    <AdminCard className="mb-6" >
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-[var(--admin-text-primary)]">Songs hochladen (bis zu {BULK_MAX} Dateien)</h2>
        <input ref={input} type="file" multiple accept={AUDIO} className="hidden" onChange={(e) => pick(e.target.files)} data-testid="bulk-file" />
        <div className="flex gap-2">
          <AdminButton variant="secondary" onClick={() => input.current?.click()} disabled={running || rows.length >= BULK_MAX} data-testid="bulk-pick"><Upload size={15} /> Dateien wählen ({rows.length}/{BULK_MAX})</AdminButton>
          {rows.length > 0 && <AdminButton variant="ghost" onClick={() => setRows([])} disabled={running} data-testid="bulk-clear">Liste leeren</AdminButton>}
        </div>
      </div>
      <div className="mb-3 grid gap-2 rounded-xl bg-[var(--admin-hover)] p-3 sm:grid-cols-3 lg:grid-cols-7" data-testid="bulk-defaults">
        <p className="col-span-full text-xs text-[var(--admin-text-muted)]">Vorgaben für neu gewählte Dateien (pro Datei änderbar):</p>
        <AdminInput className={field} placeholder="Interpret" value={defaults.artist} onChange={(e) => setDefaults({ ...defaults, artist: e.target.value })} aria-label="Interpret (Vorgabe)" />
        <AdminInput className={field} placeholder="Album" value={defaults.album} onChange={(e) => setDefaults({ ...defaults, album: e.target.value })} aria-label="Album (Vorgabe)" />
        <AdminInput className={field} placeholder="Genre" value={defaults.genre} onChange={(e) => setDefaults({ ...defaults, genre: e.target.value })} aria-label="Genre (Vorgabe)" />
        <AdminInput className={field} placeholder="Sprache" value={defaults.language} onChange={(e) => setDefaults({ ...defaults, language: e.target.value })} aria-label="Sprache (Vorgabe)" />
        <AdminSelect className="h-9 text-xs" value={defaults.level} onChange={(e) => setDefaults({ ...defaults, level: e.target.value })} aria-label="Niveau (Vorgabe)"><option value="">Niveau —</option>{["A1", "A2", "B1", "B2", "C1"].map((l) => <option key={l}>{l}</option>)}</AdminSelect>
        <AdminSelect className="h-9 text-xs" value={defaults.access_type} onChange={(e) => setDefaults({ ...defaults, access_type: e.target.value as "FREE" | "PAID" })} aria-label="Zugang (Vorgabe)"><option value="FREE">Kostenlos</option><option value="PAID">Kostenpflichtig</option></AdminSelect>
        <AdminSelect className="h-9 text-xs" value={defaults.status} onChange={(e) => setDefaults({ ...defaults, status: e.target.value as Status })} aria-label="Status (Vorgabe)">{(Object.keys(STATUS_DE) as Status[]).map((s) => <option key={s} value={s}>{STATUS_DE[s]}</option>)}</AdminSelect>
      </div>
      {note && <p className="mb-2 text-sm text-[var(--admin-warning)]" role="status" data-testid="bulk-note">{note}</p>}

      <ul className="space-y-2" data-testid="bulk-list">
        {rows.map((r) => (
          <li key={r.key} className="rounded-xl p-3 ring-1 ring-[var(--admin-border)]" data-testid="bulk-row" data-state={r.state} data-file={r.file.name}>
            <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-6">
              <AdminInput className={`${field} sm:col-span-2`} value={r.title} disabled={r.state !== "wait" && r.state !== "error"} onChange={(e) => patch(r.key, { title: e.target.value })} aria-label="Titel" data-testid="bulk-title" />
              <AdminInput className={field} placeholder="Interpret" value={r.artist} disabled={r.state === "up" || r.state === "done"} onChange={(e) => patch(r.key, { artist: e.target.value })} aria-label="Interpret" />
              <AdminInput className={field} placeholder="Album" value={r.album} disabled={r.state === "up" || r.state === "done"} onChange={(e) => patch(r.key, { album: e.target.value })} aria-label="Album" />
              <AdminInput className={field} placeholder="Genre" value={r.genre} disabled={r.state === "up" || r.state === "done"} onChange={(e) => patch(r.key, { genre: e.target.value })} aria-label="Genre" />
              <AdminSelect className="h-9 text-xs" value={r.level} disabled={r.state === "up" || r.state === "done"} onChange={(e) => patch(r.key, { level: e.target.value })} aria-label="Niveau"><option value="">Niveau —</option>{["A1", "A2", "B1", "B2", "C1"].map((l) => <option key={l}>{l}</option>)}</AdminSelect>
              <AdminSelect className="h-9 text-xs" value={r.access_type} disabled={r.state === "up" || r.state === "done"} onChange={(e) => patch(r.key, { access_type: e.target.value as "FREE" | "PAID" })} aria-label="Zugang"><option value="FREE">Kostenlos</option><option value="PAID">Kostenpflichtig</option></AdminSelect>
              {r.access_type === "PAID" && <AdminInput className={field} type="number" min={1} placeholder="Preis UZS" value={r.price} onChange={(e) => patch(r.key, { price: e.target.value })} aria-label="Preis" />}
              <AdminSelect className="h-9 text-xs" value={r.status} disabled={r.state === "up" || r.state === "done"} onChange={(e) => patch(r.key, { status: e.target.value as Status })} aria-label="Status">{(Object.keys(STATUS_DE) as Status[]).map((s) => <option key={s} value={s}>{STATUS_DE[s]}</option>)}</AdminSelect>
              <label className="flex items-center gap-2 text-xs text-[var(--admin-text-muted)] sm:col-span-2">Cover
                <input type="file" accept="image/jpeg,image/png,image/webp" disabled={r.state === "up" || r.state === "done"} onChange={(e) => patch(r.key, { cover: e.target.files?.[0] ?? null })} className="min-w-0 flex-1 text-xs" aria-label="Cover" /></label>
            </div>
            <div className="mt-2 flex items-center gap-3">
              <span className="min-w-0 flex-1 truncate text-xs text-[var(--admin-text-muted)]">{r.file.name} · {fileSize(r.file.size)}</span>
              <span className="w-28 text-right text-xs font-semibold" data-testid="bulk-state">
                {r.state === "wait" && "Wartet"}{r.state === "up" && <span className="inline-flex items-center gap-1"><Loader2 size={12} className="animate-spin" /> {r.percent}%</span>}
                {r.state === "done" && <span className="text-[var(--admin-success)]">Hochgeladen</span>}{r.state === "error" && <span className="text-[var(--admin-danger)]">Fehler</span>}
              </span>
              {(r.state === "wait" || r.state === "error") && !running && <button className="rounded p-1 text-[var(--admin-text-muted)] hover:text-[var(--admin-danger)]" aria-label="Aus der Liste entfernen" onClick={() => setRows((rs) => rs.filter((x) => x.key !== r.key))} data-testid="bulk-remove"><X size={14} /></button>}
              {r.state === "error" && !running && <button className="rounded p-1 text-[var(--admin-primary)]" aria-label="Erneut versuchen" onClick={() => void run([r.key])} data-testid="bulk-retry"><RotateCw size={14} /></button>}
            </div>
            {(r.state === "up" || r.state === "done") && <div className="mt-1.5"><ProgressBar percent={r.percent} testId="bulk-progress" /></div>}
            {r.info && <p className="mt-1.5 text-xs text-[var(--admin-text-muted)]" data-testid="bulk-info">{r.info}</p>}
            {r.warn && <p className="mt-1 text-xs text-[var(--admin-warning)]" role="status" data-testid="bulk-warn">{r.warn}</p>}
            {r.error && <p className="mt-1.5 text-xs text-[var(--admin-danger)]" role="alert" data-testid="bulk-error">{r.error}</p>}
          </li>
        ))}
      </ul>
      {rows.length > 0 && (
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <AdminButton onClick={() => void run()} disabled={running || !rows.some((r) => r.state === "wait" || r.state === "error")} data-testid="bulk-start">{running ? <Loader2 size={15} className="animate-spin" /> : <Upload size={15} />} Alle hochladen</AdminButton>
          <span className="text-sm text-[var(--admin-text-secondary)]" data-testid="bulk-summary">{done} hochgeladen{failed ? ` · ${failed} mit Fehler` : ""} · {rows.length} insgesamt</span>
        </div>
      )}
    </AdminCard>
  );
}

function SongDialog({ song, onClose }: { song: AdminItem; onClose: () => void }) {
  const [v, setV] = useState({ title: song.title, artist: song.artist ?? "", album: song.album ?? "", genre: song.genre ?? "", language: song.language, level: song.level ?? "", access_type: song.access_type,
    price: song.price ? String(song.price) : "", old_price: song.old_price ? String(song.old_price) : "", is_featured: song.is_featured, status: song.status });
  const [cover, setCover] = useState<File | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [percent, setPercent] = useState(0);
  const [note, setNote] = useState<{ ok: boolean; text: string } | null>(null);
  async function save() {
    setBusy(true); setNote(null);
    try {
      await updateItem("SONG", song.id, { title: v.title.trim(), artist: v.artist.trim() || null, album: v.album.trim() || null, genre: v.genre.trim() || null, language: v.language, level: v.level || null,
        access_type: v.access_type, ...(v.access_type === "PAID" ? { price: Number(v.price) || null, old_price: v.old_price ? Number(v.old_price) : null } : {}), is_featured: v.is_featured, status: v.status });
      if (cover) await uploadCover("SONG", song.id, cover, setPercent);
      if (file) await replaceSongFile(song.id, file, setPercent);
      setNote({ ok: true, text: "Gespeichert." }); setCover(null); setFile(null);
    } catch (err) { setNote({ ok: false, text: medienError(err) }); } finally { setBusy(false); }
  }
  const set = (k: string, val: string | boolean) => setV((s) => ({ ...s, [k]: val }));
  return (
    <FormDialog open onOpenChange={(o) => !o && !busy && onClose()} title="Song bearbeiten" size="lg"
                footer={<><AdminButton variant="ghost" onClick={onClose} disabled={busy}>Schließen</AdminButton><AdminButton onClick={save} disabled={busy || !v.title.trim()} data-testid="song-save">{busy ? "Speichern …" : "Speichern"}</AdminButton></>}>
      <div className="space-y-3" data-testid="song-dialog">
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="sm:col-span-2"><AdminLabel>Titel *</AdminLabel><AdminInput value={v.title} onChange={(e) => set("title", e.target.value)} data-testid="f-title" /></div>
          <div><AdminLabel>Interpret</AdminLabel><AdminInput value={v.artist} onChange={(e) => set("artist", e.target.value)} /></div>
          <div><AdminLabel>Album</AdminLabel><AdminInput value={v.album} onChange={(e) => set("album", e.target.value)} /></div>
          <div><AdminLabel>Genre</AdminLabel><AdminInput value={v.genre} onChange={(e) => set("genre", e.target.value)} /></div>
          <div><AdminLabel>Sprache</AdminLabel><AdminInput value={v.language} onChange={(e) => set("language", e.target.value)} /></div>
          <div><AdminLabel>Niveau</AdminLabel><AdminSelect value={v.level} onChange={(e) => set("level", e.target.value)}><option value="">—</option>{["A1", "A2", "B1", "B2", "C1"].map((l) => <option key={l}>{l}</option>)}</AdminSelect></div>
          <div><AdminLabel>Status</AdminLabel><AdminSelect value={v.status} onChange={(e) => set("status", e.target.value)} data-testid="f-status">{(Object.keys(STATUS_DE) as Status[]).map((s) => <option key={s} value={s}>{STATUS_DE[s]}</option>)}</AdminSelect></div>
          <div><AdminLabel>Zugang</AdminLabel><AdminSelect value={v.access_type} onChange={(e) => set("access_type", e.target.value)} data-testid="f-access"><option value="FREE">Kostenlos</option><option value="PAID">Kostenpflichtig</option></AdminSelect></div>
          {v.access_type === "PAID" && <><div><AdminLabel>Preis (UZS)</AdminLabel><AdminInput type="number" min={1} value={v.price} onChange={(e) => set("price", e.target.value)} data-testid="f-price" /></div><div><AdminLabel>Alter Preis</AdminLabel><AdminInput type="number" min={1} value={v.old_price} onChange={(e) => set("old_price", e.target.value)} /></div></>}
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={v.is_featured} onChange={(e) => set("is_featured", e.target.checked)} data-testid="f-featured" /> Empfohlen</label>
        </div>
        <div className="grid gap-3 sm:grid-cols-2"><FilePick label="Cover ersetzen" accept="image/jpeg,image/png,image/webp" file={cover} onFile={setCover} testId="song-cover-file" /><FilePick label="Audiodatei ersetzen" accept={AUDIO} file={file} onFile={setFile} testId="song-audio-file" hint={`Aktuell: ${FILE_DE[song.file_status]} · ${audioInfo(song) || dur(song.duration_ms)}`} /></div>
        {song.metadata_status === "FAILED" && <p className="text-xs text-[var(--admin-warning)]" role="status" data-testid="song-meta-warning">{META_WARNING}</p>}
        {busy && (cover || file) && <ProgressBar percent={percent} />}
        {note && <p role="status" className={`text-sm ${note.ok ? "text-[var(--admin-success)]" : "text-[var(--admin-danger)]"}`} data-testid="song-note">{note.text}</p>}
      </div>
    </FormDialog>
  );
}

/** Official playlists: name, description, cover, status and the songs in their order. */
function PlaylistsAdmin({ songs }: { songs: AdminItem[] }) {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<AdminPlaylist | "new" | null>(null);
  const [deleting, setDeleting] = useState<AdminPlaylist | null>(null);
  const lists = useQuery({ queryKey: ["admin-medien-playlists"], queryFn: getPlaylists });
  const refresh = () => void queryClient.invalidateQueries({ queryKey: ["admin-medien-playlists"] });
  const remove = useMutation({ mutationFn: (p: AdminPlaylist) => deletePlaylist(p.id), onSuccess: () => { setDeleting(null); refresh(); } });
  return (
    <AdminCard className="mt-6" >
      <div className="mb-3 flex items-center justify-between"><h2 className="flex items-center gap-2 text-sm font-semibold text-[var(--admin-text-primary)]"><ListMusic size={16} /> Playlists (VIZU)</h2><AdminButton size="sm" onClick={() => setEditing("new")} data-testid="playlist-new"><Plus size={14} /> Neue Playlist</AdminButton></div>
      <ul className="divide-y divide-[var(--admin-border)]" data-testid="admin-playlists">
        {(lists.data ?? []).map((p) => (
          <li key={p.id} className="flex flex-wrap items-center gap-3 py-2" data-testid="admin-playlist" data-name={p.name}>
            <span className="min-w-0 flex-1"><span className="block truncate text-sm font-semibold text-[var(--admin-text-primary)]">{p.name}</span><span className="text-xs text-[var(--admin-text-muted)]">{p.song_count} Songs</span></span>
            <StatusPill status={p.status} />
            <AdminButton size="sm" variant="secondary" onClick={() => setEditing(p)} aria-label={`${p.name} bearbeiten`} data-testid="playlist-edit"><Pencil size={13} /></AdminButton>
            <AdminButton size="sm" variant="danger" onClick={() => setDeleting(p)} aria-label={`${p.name} löschen`} data-testid="playlist-delete"><Trash2 size={13} /></AdminButton>
          </li>
        ))}
        {lists.data && !lists.data.length && <li className="py-6 text-center text-sm text-[var(--admin-text-muted)]">Noch keine Playlists.</li>}
      </ul>
      {editing && <PlaylistDialog key={editing === "new" ? "new" : editing.id} initial={editing === "new" ? null : editing} songs={songs} onClose={() => { setEditing(null); refresh(); }} />}
      <ConfirmDialog open={!!deleting} onOpenChange={(o) => !o && setDeleting(null)} title="Playlist löschen" description={`„${deleting?.name ?? ""}“ wird gelöscht. Die Songs selbst bleiben.`} isPending={remove.isPending} onConfirm={() => deleting && remove.mutate(deleting)} />
    </AdminCard>
  );
}

function PlaylistDialog({ initial, songs, onClose }: { initial: AdminPlaylist | null; songs: AdminItem[]; onClose: () => void }) {
  const [id, setId] = useState<string | null>(initial?.id ?? null);
  const [name, setName] = useState(initial?.name ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [status, setStatus] = useState<Status>(initial?.status ?? "PUBLISHED");
  const [order, setOrder] = useState<string[] | null>(null);
  const [cover, setCover] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<{ ok: boolean; text: string } | null>(null);
  const current = useQuery({ queryKey: ["admin-playlist-songs", initial?.id], queryFn: () => getPlaylistSongs(initial!.id), enabled: !!initial });
  const ids = order ?? current.data?.map((s) => s.id) ?? [];
  const titleOf = (sid: string) => songs.find((s) => s.id === sid)?.title ?? current.data?.find((s) => s.id === sid)?.title ?? sid;
  const move = (i: number, d: -1 | 1) => { const next = [...ids]; [next[i], next[i + d]] = [next[i + d], next[i]]; setOrder(next); };
  async function save() {
    setBusy(true); setNote(null);
    try {
      const saved = await savePlaylist({ name: name.trim(), description: description.trim() || null, status }, id ?? undefined);
      setId(saved.id);
      await setPlaylistSongs(saved.id, ids);
      if (cover) { await uploadPlaylistCover(saved.id, cover); setCover(null); }
      setNote({ ok: true, text: "Gespeichert." });
    } catch (err) { setNote({ ok: false, text: medienError(err) }); } finally { setBusy(false); }
  }
  return (
    <FormDialog open onOpenChange={(o) => !o && !busy && onClose()} title={id ? "Playlist bearbeiten" : "Neue Playlist"} size="lg"
                footer={<><AdminButton variant="ghost" onClick={onClose} disabled={busy}>Schließen</AdminButton><AdminButton onClick={save} disabled={busy || !name.trim()} data-testid="playlist-save">{busy ? "Speichern …" : "Speichern"}</AdminButton></>}>
      <div className="space-y-3" data-testid="playlist-dialog">
        <div className="grid gap-3 sm:grid-cols-2">
          <div><AdminLabel>Name *</AdminLabel><AdminInput value={name} onChange={(e) => setName(e.target.value)} maxLength={160} data-testid="playlist-name" /></div>
          <div><AdminLabel>Status</AdminLabel><AdminSelect value={status} onChange={(e) => setStatus(e.target.value as Status)}>{(Object.keys(STATUS_DE) as Status[]).map((s) => <option key={s} value={s}>{STATUS_DE[s]}</option>)}</AdminSelect></div>
          <div className="sm:col-span-2"><AdminLabel>Beschreibung</AdminLabel><AdminInput value={description} onChange={(e) => setDescription(e.target.value)} /></div>
          <FilePick label="Cover" accept="image/jpeg,image/png,image/webp" file={cover} onFile={setCover} testId="playlist-cover-file" />
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          <div><AdminLabel>Songs hinzufügen</AdminLabel><ul className="max-h-56 overflow-y-auto rounded-lg ring-1 ring-[var(--admin-border)]" data-testid="playlist-candidates">
            {songs.filter((s) => !ids.includes(s.id)).map((s) => <li key={s.id}><button className="flex w-full items-center justify-between px-3 py-1.5 text-left text-sm hover:bg-[var(--admin-hover)]" onClick={() => setOrder([...ids, s.id])} data-testid="playlist-add-song"><span className="truncate">{s.title}</span><Plus size={13} /></button></li>)}
          </ul></div>
          <div><AdminLabel>In der Playlist ({ids.length})</AdminLabel><ol className="max-h-56 overflow-y-auto rounded-lg ring-1 ring-[var(--admin-border)]" data-testid="playlist-members">
            {ids.map((sid, i) => <li key={sid} className="flex items-center gap-1 px-3 py-1 text-sm" data-testid="playlist-member"><span className="min-w-0 flex-1 truncate">{i + 1}. {titleOf(sid)}</span>
              <button aria-label="Nach oben" disabled={i === 0} onClick={() => move(i, -1)} className="p-1 disabled:opacity-30"><ArrowUp size={13} /></button><button aria-label="Nach unten" disabled={i === ids.length - 1} onClick={() => move(i, 1)} className="p-1 disabled:opacity-30"><ArrowDown size={13} /></button>
              <button aria-label="Entfernen" onClick={() => setOrder(ids.filter((x) => x !== sid))} className="p-1 text-[var(--admin-danger)]"><X size={13} /></button></li>)}
          </ol></div>
        </div>
        {note && <p role="status" className={`text-sm ${note.ok ? "text-[var(--admin-success)]" : "text-[var(--admin-danger)]"}`} data-testid="playlist-note">{note.text}</p>}
      </div>
    </FormDialog>
  );
}

/** Admin → Medien → Musik: bulk upload (10 files), songs (edit / hide / featured / delete) and official playlists. */
export default function SongsAdmin() {
  const queryClient = useQueryClient();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<AdminItem | null>(null);
  const [deleting, setDeleting] = useState<AdminItem | null>(null);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const songs = useQuery({ queryKey: ["admin-medien-songs", q, status, page], queryFn: () => listItems("SONG", { q, status, page, page_size: 25 }), placeholderData: (p) => p });
  const all = useQuery({ queryKey: ["admin-medien-songs-all"], queryFn: () => listItems("SONG", { page_size: 100 }) });
  const refresh = () => { void queryClient.invalidateQueries({ queryKey: ["admin-medien-songs"] }); void queryClient.invalidateQueries({ queryKey: ["admin-medien-songs-all"] }); };
  const patch = useMutation({ mutationFn: ({ s, data }: { s: AdminItem; data: Parameters<typeof updateItem>[2] }) => updateItem("SONG", s.id, data), onSuccess: refresh, onError: (e) => setMessage({ ok: false, text: medienError(e) }) });
  const remove = useMutation({ mutationFn: (s: AdminItem) => deleteItem("SONG", s.id), onSuccess: () => { setDeleting(null); setMessage({ ok: true, text: "Song gelöscht (Datei und Cover entfernt)." }); refresh(); }, onError: (e) => { setDeleting(null); setMessage({ ok: false, text: medienError(e) }); } });
  const total = songs.data?.total ?? 0;
  return (
    <div data-testid="songs-admin">
      <AdminPageHeader title="Medien · Musik" description="Songs im Stapel hochladen (bis zu 10), Metadaten pflegen, Playlists bauen, Songs empfehlen oder ausblenden." />
      <MedienTabs />
      <BulkUpload onDone={refresh} />
      {message && <p role="status" className={`mb-4 rounded-xl px-4 py-2.5 text-sm ${message.ok ? "bg-[var(--admin-success)]/10 text-[var(--admin-success)]" : "bg-[var(--admin-danger)]/10 text-[var(--admin-danger)]"}`} data-testid="songs-message">{message.text}</p>}
      <div className="mb-4 flex flex-wrap gap-2">
        <AdminInput className="w-64" placeholder="Titel suchen …" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} aria-label="Suchen" data-testid="songs-search" />
        <AdminSelect className="w-44" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} aria-label="Status"><option value="">Alle Status</option><option value="PUBLISHED">Veröffentlicht</option><option value="DRAFT">Entwurf</option><option value="HIDDEN">Ausgeblendet</option></AdminSelect>
      </div>
      <AdminCard className="overflow-x-auto p-0">
        <table className="w-full min-w-[820px] text-left text-sm" data-testid="songs-table">
          <thead><tr className="text-xs uppercase text-[var(--admin-text-muted)]"><th className="p-3">Song</th><th>Album</th><th>Dauer</th><th>Zugang</th><th>Status</th><th>Datei</th><th>Wiedergaben</th><th className="pr-3 text-right">Aktionen</th></tr></thead>
          <tbody>
            {(songs.data?.items ?? []).map((s) => (
              <tr key={s.id} className="border-t border-[var(--admin-border)]" data-testid="song-admin-row" data-title={s.title}>
                <td className="p-3"><span className="block font-semibold text-[var(--admin-text-primary)]">{s.title}</span><span className="text-xs text-[var(--admin-text-muted)]">{s.artist ?? "—"}{s.genre ? ` · ${s.genre}` : ""}{s.level ? ` · ${s.level}` : ""}{s.is_featured ? " · ★" : ""}</span></td>
                <td>{s.album ?? "—"}</td><td>{dur(s.duration_ms)}{(s.audio_format || s.bitrate_kbps) && <span className="block text-xs text-[var(--admin-text-muted)]" data-testid="song-format">{[s.audio_format?.toUpperCase(), s.bitrate_kbps ? `${s.bitrate_kbps} kbps` : null].filter(Boolean).join(" · ")}</span>}{s.metadata_status === "FAILED" && <span className="block text-xs text-[var(--admin-warning)]" title={META_WARNING} data-testid="song-meta-failed">Metadaten fehlen</span>}</td><td>{s.access_type === "FREE" ? "Kostenlos" : `${new Intl.NumberFormat("de-DE").format(s.price ?? 0)} UZS`}</td>
                <td><StatusPill status={s.status} /></td><td className={s.file_status === "ok" ? "" : "text-[var(--admin-warning)]"}>{FILE_DE[s.file_status]}</td><td>{s.plays ?? 0}</td>
                <td className="pr-3"><div className="flex justify-end gap-1">
                  <AdminButton size="sm" variant="secondary" onClick={() => setEditing(s)} aria-label={`${s.title} bearbeiten`} data-testid="song-edit"><Pencil size={13} /></AdminButton>
                  <AdminButton size="sm" variant="secondary" onClick={() => patch.mutate({ s, data: { status: s.status === "PUBLISHED" ? "HIDDEN" : "PUBLISHED" } })} aria-label={s.status === "PUBLISHED" ? "Ausblenden" : "Veröffentlichen"} data-testid="song-toggle">{s.status === "PUBLISHED" ? <EyeOff size={13} /> : <Eye size={13} />}</AdminButton>
                  <AdminButton size="sm" variant="secondary" onClick={() => patch.mutate({ s, data: { is_featured: !s.is_featured } })} aria-label="Empfohlen an/aus" data-testid="song-featured"><Star size={13} className={s.is_featured ? "fill-current text-[var(--admin-primary)]" : ""} /></AdminButton>
                  <AdminButton size="sm" variant="danger" onClick={() => setDeleting(s)} aria-label={`${s.title} löschen`} data-testid="song-delete"><Trash2 size={13} /></AdminButton>
                </div></td>
              </tr>
            ))}
            {songs.data && !songs.data.items.length && <tr><td colSpan={8} className="p-8 text-center text-[var(--admin-text-muted)]">Keine Songs.</td></tr>}
          </tbody>
        </table>
      </AdminCard>
      {total > 25 && <div className="mt-3 flex items-center justify-center gap-3 text-sm"><AdminButton size="sm" variant="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>Zurück</AdminButton><span>{page} / {Math.ceil(total / 25)}</span><AdminButton size="sm" variant="secondary" disabled={page >= Math.ceil(total / 25)} onClick={() => setPage(page + 1)}>Weiter</AdminButton></div>}
      <PlaylistsAdmin songs={all.data?.items ?? []} />
      {editing && <SongDialog key={editing.id} song={editing} onClose={() => { setEditing(null); refresh(); }} />}
      <ConfirmDialog open={!!deleting} onOpenChange={(o) => !o && setDeleting(null)} title="Song löschen" description={`„${deleting?.title ?? ""}“ wird mit Audio und Cover gelöscht und aus allen Playlists und Favoriten entfernt.`} isPending={remove.isPending} onConfirm={() => deleting && remove.mutate(deleting)} />
    </div>
  );
}
