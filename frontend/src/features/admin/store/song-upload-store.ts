import { create } from "zustand";

import { CONCURRENCY, fileIdOf, isAudioName, localDuplicates, parseDuplicate, restoreState, room, type UploadState } from "../lib/song-upload";
import { checkSongDuplicates, getSongStates, medienError, uploadSong, type SongState, type Status } from "../services/medien-admin-service";

/* The Musik bulk upload (up to 500 songs) as a store that lives OUTSIDE the page component: moving to another admin page does not stop the uploads,
 * coming back shows the same list. What was done is also kept in the browser (localStorage, without the files): after a reload or a lost
 * connection the admin picks the same files again and only the missing ones are sent (finished rows are recognised by name + size + date, and
 * the server refuses a file it already has by its SHA-256).
 * Flow per file: hash (SHA-256, in the browser) → duplicate check (the list itself + the server, in batches) → upload (CONCURRENCY at a time;
 * the server stores the original, checks the hash, queues the metadata) → the metadata the server's queue read is polled and shown. */

export interface Defaults { artist: string; album: string; genre: string; language: string; level: string; access_type: "FREE" | "PAID"; status: Status }
export const DEFAULTS: Defaults = { artist: "", album: "", genre: "", language: "de", level: "", access_type: "FREE", status: "PUBLISHED" };

export interface UploadRow {
  key: string; fileId: string; file: File | null; name: string; size: number; sha: string | null; checked: boolean;
  title: string; artist: string; album: string; genre: string; language: string; level: string; access_type: "FREE" | "PAID"; price: string; status: Status;
  cover: File | null; state: UploadState; percent: number; error?: string; songId?: string;
  dupOf?: { id: string | null; title: string } | null; allowDup?: boolean; processing?: string | null; info?: string; warn?: string;
}

interface UploadStore {
  rows: UploadRow[];
  defaults: Defaults;
  running: boolean;
  paused: boolean;
  /** a list from an earlier visit was restored (its files have to be chosen again) */
  restored: boolean;
  notice: string | null;
  setDefaults: (d: Defaults) => void;
  addFiles: (files: File[]) => void;
  patch: (key: string, p: Partial<UploadRow>) => void;
  remove: (key: string) => void;
  clear: () => void;
  clearFinished: () => void;
  start: (keys?: string[]) => void;
  pause: () => void;
  retryFailed: () => void;
  allowDuplicate: (key: string) => void;
}

const STORAGE_KEY = "vizu.admin.songUpload.v1";
const DUP_BATCH = 25;
const POLL_MS = 2000;
export const META_WARNING = "Die Datei ist gespeichert, aber Dauer / Bitrate konnten nicht gelesen werden (Audioverarbeitung nicht verfügbar oder Datei ungewöhnlich). Der Song ist abspielbar.";
export const INVALID_WARNING = "Die Datei ist keine lesbare Audiodatei: der Song wurde als Entwurf gespeichert — bitte die Datei ersetzen.";

const dur = (ms?: number | null) => (ms ? `${Math.floor(ms / 60000)}:${String(Math.floor((ms % 60000) / 1000)).padStart(2, "0")}` : null);
const mb = (n?: number | null) => (n ? `${(n / 1048576).toFixed(1)} MB` : null);
/** what the server read: "MP3 · 3:21 · 192 kbps · 7.7 MB" (parts it could not read are left out) */
export const infoLine = (s: Pick<SongState, "audio_format" | "duration_ms" | "bitrate_kbps" | "file_size">) =>
  [s.audio_format?.toUpperCase(), dur(s.duration_ms), s.bitrate_kbps ? `${s.bitrate_kbps} kbps` : null, mb(s.file_size)].filter(Boolean).join(" · ");

function load(): { rows: UploadRow[]; defaults: Defaults } | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as { v: number; defaults: Defaults; rows: Omit<UploadRow, "file" | "cover">[] };
    if (data.v !== 1 || !Array.isArray(data.rows) || !data.rows.length) return null;
    return { defaults: { ...DEFAULTS, ...data.defaults }, rows: data.rows.map((r) => ({ ...r, file: null, cover: null, state: restoreState(r.state), percent: r.state === "done" ? 100 : 0 })) };
  } catch {
    return null; // storage blocked / damaged: start empty
  }
}

const saved = load();

export const useSongUpload = create<UploadStore>((set, get) => ({
  rows: saved?.rows ?? [],
  defaults: saved?.defaults ?? DEFAULTS,
  running: false,
  paused: false,
  restored: !!saved?.rows.some((r) => r.state === "missing"),
  notice: null,
  setDefaults: (defaults) => set({ defaults }),
  addFiles: (files) => {
    const { rows, defaults } = get();
    const audio = files.filter((f) => isAudioName(f.name));
    const skippedType = files.length - audio.length;
    const byId = new Map(rows.map((r) => [r.fileId, r]));
    const next = [...rows];
    let added = 0, reattached = 0, already = 0;
    const space = room(rows.length);
    for (const f of audio) {
      const id = fileIdOf(f);
      const known = byId.get(id);
      if (known) {
        if (known.state === "missing") {
          const i = next.findIndex((r) => r.key === known.key);
          next[i] = { ...known, file: f, state: known.sha ? "wait" : "hashing", checked: !!known.sha, error: undefined };
          reattached += 1;
        } else already += 1;
        continue;
      }
      if (added >= space) continue;
      next.push({ key: `${id}|${Math.random().toString(36).slice(2, 8)}`, fileId: id, file: f, name: f.name, size: f.size, sha: null, checked: false,
        title: f.name.replace(/\.[^.]+$/, ""), ...defaults, price: "", cover: null, state: "hashing", percent: 0 });
      added += 1;
    }
    const tooMany = audio.length - added - reattached - already;
    const parts = [
      tooMany > 0 ? `Höchstens 500 Dateien auf einmal — ${tooMany} wurden nicht übernommen.` : null,
      skippedType > 0 ? `${skippedType} Datei(en) ohne Audio-Endung (MP3, WAV, M4A, AAC, OGG, FLAC) wurden übersprungen.` : null,
      already > 0 ? `${already} Datei(en) waren schon in der Liste.` : null,
      reattached > 0 ? `${reattached} Datei(en) aus der unterbrochenen Sitzung wieder zugeordnet.` : null,
    ].filter(Boolean);
    set({ rows: next, notice: parts.length ? parts.join(" ") : null, restored: next.some((r) => r.state === "missing") });
    void hashAll();
    if (get().running) pump();
  },
  patch: (key, p) => set((s) => ({ rows: s.rows.map((r) => (r.key === key ? { ...r, ...p } : r)) })),
  remove: (key) => set((s) => ({ rows: s.rows.filter((r) => r.key !== key || r.state === "up") })),
  clear: () => { if (!get().running) set({ rows: [], notice: null, restored: false }); },
  clearFinished: () => set((s) => ({ rows: s.rows.filter((r) => r.state !== "done" && r.state !== "dup") })),
  start: (keys) => {
    set((s) => ({ running: true, paused: false, rows: s.rows.map((r) => ((keys ? keys.includes(r.key) : true) && r.state === "error" && r.file ? { ...r, state: "wait", error: undefined, percent: 0 } : r)) }));
    pump();
  },
  pause: () => set({ paused: true }),
  retryFailed: () => get().start(get().rows.filter((r) => r.state === "error").map((r) => r.key)),
  allowDuplicate: (key) => {
    set((s) => ({ rows: s.rows.map((r) => (r.key === key && r.file ? { ...r, allowDup: true, state: "wait", checked: true, dupOf: null } : r)) }));
    if (get().running) pump();
  },
}));

// ---------------- hashing + duplicate check ----------------

let hashing = false;

async function sha256Hex(file: File): Promise<string | null> {
  if (typeof crypto === "undefined" || !crypto.subtle) return null; // no secure context: the server still checks by its own hash
  const digest = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
  return Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, "0")).join("");
}

async function checkBatch(keys: string[]) {
  const st = useSongUpload.getState();
  const rows = st.rows.filter((r) => keys.includes(r.key) && r.state === "hashing");
  const hashes = rows.map((r) => r.sha).filter((h): h is string => !!h);
  let existing: Awaited<ReturnType<typeof checkSongDuplicates>> = {};
  try { if (hashes.length) existing = await checkSongDuplicates(hashes); } catch { /* the server check at upload still refuses a duplicate */ }
  for (const r of rows) {
    const hit = r.sha ? existing[r.sha] : undefined;
    st.patch(r.key, hit && !r.allowDup ? { state: "dup", checked: true, dupOf: { id: hit.id, title: hit.title } } : { state: "wait", checked: true });
  }
}

/** Hashes every row that needs it, one file at a time (one file in memory), and asks the server about duplicates every DUP_BATCH files. */
async function hashAll() {
  if (hashing) return;
  hashing = true;
  try {
    let batch: string[] = [];
    const seen = new Set<string>(); // each row once per run (a browser without crypto.subtle leaves the hash empty)
    for (;;) {
      const row = useSongUpload.getState().rows.find((r) => r.state === "hashing" && r.file && !seen.has(r.key));
      if (!row) break;
      seen.add(row.key);
      let sha = row.sha;
      if (!sha && row.file) {
        try { sha = await sha256Hex(row.file); } catch { sha = null; }
      }
      useSongUpload.getState().patch(row.key, { sha });
      // the same file twice in the list: the later one is a duplicate of the earlier one
      const local = localDuplicates(useSongUpload.getState().rows).get(row.key);
      if (local) {
        const firstRow = useSongUpload.getState().rows.find((r) => r.key === local);
        useSongUpload.getState().patch(row.key, { state: "dup", checked: true, dupOf: { id: null, title: `gleiche Datei wie „${firstRow?.name ?? ""}“ in dieser Liste` } });
        continue;
      }
      batch.push(row.key);
      if (batch.length >= DUP_BATCH) { await checkBatch(batch); batch = []; pump(); }
    }
    if (batch.length) await checkBatch(batch);
  } finally {
    hashing = false;
  }
  pump();
  if (useSongUpload.getState().rows.some((r) => r.state === "hashing" && r.file)) void hashAll();
}

// ---------------- uploads ----------------

const inflight = new Set<string>();

function rawMessage(err: unknown): string {
  const data = (err as { response?: { data?: { message?: unknown; detail?: unknown } } })?.response?.data;
  const raw = data?.message ?? data?.detail;
  return typeof raw === "string" ? raw : "";
}

function pump() {
  const st = useSongUpload.getState();
  if (!st.running || st.paused) return;
  while (inflight.size < CONCURRENCY) {
    const next = useSongUpload.getState().rows.find((r) => r.state === "wait" && r.file && !inflight.has(r.key));
    if (!next) break;
    inflight.add(next.key);
    void uploadOne(next).finally(() => { inflight.delete(next.key); pump(); finishIfIdle(); });
  }
  finishIfIdle();
}

function finishIfIdle() {
  const rows = useSongUpload.getState().rows;
  if (!inflight.size && !hashing && !rows.some((r) => (r.state === "wait" || r.state === "hashing") && r.file)) useSongUpload.setState({ running: false, paused: false });
}

async function uploadOne(r: UploadRow) {
  const st = useSongUpload.getState();
  st.patch(r.key, { state: "up", percent: 0, error: undefined });
  let last = 0;
  try {
    const savedSong = await uploadSong(r.file!, {
      title: r.title.trim() || r.name, artist: r.artist.trim(), album: r.album.trim(), genre: r.genre.trim(), language: r.language.trim() || "de", level: r.level,
      access_type: r.access_type, price: r.access_type === "PAID" ? r.price : undefined, status: r.status,
      sha256: r.sha ?? undefined, defer_metadata: true, allow_duplicate: r.allowDup ? true : undefined,
    }, r.cover, (percent) => { if (percent - last >= 5 || percent === 100) { last = percent; useSongUpload.getState().patch(r.key, { percent: Math.min(99, percent) }); } });
    useSongUpload.getState().patch(r.key, { state: "done", percent: 100, songId: savedSong.id, title: savedSong.title, artist: savedSong.artist ?? r.artist,
      processing: savedSong.metadata_status ?? null, info: infoLine({ audio_format: savedSong.audio_format ?? null, duration_ms: savedSong.duration_ms ?? null,
        bitrate_kbps: savedSong.bitrate_kbps ?? null, file_size: savedSong.file_size ?? null }), warn: savedSong.metadata_status === "FAILED" ? META_WARNING : undefined });
  } catch (err) {
    const dup = parseDuplicate(rawMessage(err));
    if (dup) useSongUpload.getState().patch(r.key, { state: "dup", percent: 0, dupOf: dup, checked: true });
    else useSongUpload.getState().patch(r.key, { state: "error", percent: 0, error: medienError(err, "Upload fehlgeschlagen — die Datei kann erneut gesendet werden.") });
  }
}

// ---------------- the server's metadata queue ----------------

let polling = false;

async function pollProcessing() {
  if (polling) return;
  const ids = useSongUpload.getState().rows.filter((r) => r.state === "done" && r.songId && (r.processing === "PENDING" || r.processing === "PROCESSING")).map((r) => r.songId!).slice(0, 200);
  if (!ids.length) return;
  polling = true;
  try {
    const states = await getSongStates(ids);
    const byId = new Map(states.map((s) => [s.id, s]));
    useSongUpload.setState((s) => ({
      rows: s.rows.map((r) => {
        const st = r.songId ? byId.get(r.songId) : undefined;
        if (!st || st.metadata_status === r.processing) return r;
        return { ...r, processing: st.metadata_status, title: st.title, artist: st.artist ?? r.artist, info: infoLine(st),
          warn: st.metadata_status === "FAILED" ? META_WARNING : st.metadata_status === "INVALID" ? INVALID_WARNING : undefined };
      }),
    }));
  } catch { /* try again on the next tick */ } finally {
    polling = false;
  }
}

// ---------------- browser side: keep the list, warn before leaving ----------------

if (typeof window !== "undefined") {
  window.setInterval(() => { void pollProcessing(); }, POLL_MS);
  let timer: number | undefined;
  useSongUpload.subscribe((s) => {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => {
      try {
        if (!s.rows.length) { window.localStorage.removeItem(STORAGE_KEY); return; }
        const rows = s.rows.map((r) => ({ ...r, file: undefined, cover: undefined }));
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ v: 1, defaults: s.defaults, rows }));
      } catch { /* storage full / blocked: the upload itself goes on */ }
    }, 800);
  });
  window.addEventListener("beforeunload", (e) => {
    const s = useSongUpload.getState();
    if (s.running && s.rows.some((r) => r.state === "up" || r.state === "wait" || r.state === "hashing")) { e.preventDefault(); e.returnValue = ""; }
  });
}
