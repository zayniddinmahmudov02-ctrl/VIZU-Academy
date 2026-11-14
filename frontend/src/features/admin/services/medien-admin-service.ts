import { api } from "@/src/services/api";

const BASE = "/api/v1/admin/medien";

export type Kind = "BOOK" | "SONG" | "FILM";
export type Status = "DRAFT" | "PUBLISHED" | "HIDDEN";
export type Access = "FREE" | "PAID";
export type FileStatus = "ok" | "missing" | "none";

export interface AdminCategory { id: string; kind: Kind; name: string; slug: string; sort_order: number; is_active: boolean; item_count: number }

export interface AdminItem {
  id: string;
  kind: Kind;
  title: string;
  description: string | null;
  cover_url: string | null;
  has_cover: boolean;
  language: string;
  level: string | null;
  access_type: Access;
  price: number | null;
  old_price: number | null;
  discount_percent: number | null;
  is_special_offer: boolean;
  is_featured: boolean;
  status: Status;
  created_at: string;
  file_status: FileStatus;
  views?: number;
  plays?: number;
  // book
  author?: string | null;
  category_id?: string | null;
  year?: number | null;
  file_format?: string | null;
  file_size?: number | null;
  original_name?: string | null;
  // song
  artist?: string | null;
  album?: string | null;
  genre?: string | null;
  duration_ms?: number | null;
  // film
  duration_minutes?: number | null;
  video_size?: number | null;
  external_url?: string | null;
  processing_status?: "NONE" | "UPLOADING" | "READY" | "FAILED";
  subtitles?: { id: string; language: string; label: string; file_status: FileStatus }[];
}

export interface AdminPage { items: AdminItem[]; total: number; page: number; page_size: number }

export interface ItemInput {
  title?: string; description?: string | null; language?: string; level?: string | null; access_type?: Access; price?: number | null; old_price?: number | null;
  is_special_offer?: boolean; is_featured?: boolean; status?: Status; author?: string | null; artist?: string | null; album?: string | null; genre?: string | null;
  year?: number | null; duration_minutes?: number | null; category_id?: string | null;
}

export interface Stats {
  books: { total: number; free: number; paid: number; published: number };
  songs: { total: number; published: number; playlists: number; student_playlists: number };
  films: { total: number; free: number; paid: number; published: number };
  published: number; draft: number; total: number; pending_purchases: number; plays_total: number;
  most_read_books: { id: string; title: string; views: number }[];
  most_played_songs: { id: string; title: string; plays: number }[];
  most_watched_films: { id: string; title: string; views: number }[];
}

export interface AdminPlaylist { id: string; name: string; description: string | null; status: Status; sort_order: number; song_count: number; has_cover: boolean; cover_url: string | null }
export interface PurchaseRow { id: string; user_id: string; user_email: string; user_name: string; kind: Kind; content_id: string; title: string | null; price: number | null; status: string; note: string | null; created_at: string; decided_at: string | null }

const ROUTE: Record<Kind, string> = { BOOK: "books", SONG: "songs", FILM: "films" };
type Progress = (percent: number) => void;
const multipart = (onProgress?: Progress) => ({
  headers: { "Content-Type": "multipart/form-data" },
  onUploadProgress: onProgress ? (e: { loaded: number; total?: number }) => e.total && onProgress(Math.round((e.loaded / e.total) * 100)) : undefined,
});

const KNOWN: Record<string, string> = {
  UNSUPPORTED_FILE: "Das Dateiformat wird nicht unterstützt oder die Datei ist nicht lesbar.",
  FILE_TOO_LARGE: "Die Datei ist zu groß.",
  PRICE_REQUIRED: "Für kostenpflichtige Inhalte ist ein Preis nötig.",
  TITLE_REQUIRED: "Ein Titel ist nötig.",
  CATEGORY_EXISTS: "Diese Kategorie gibt es schon.",
  CATEGORY_IN_USE: "Die Kategorie wird noch verwendet: erst Inhalte verschieben oder die Kategorie ausblenden.",
  INVALID_URL: "Nur https://-Links sind erlaubt.",
  INVALID_LANGUAGE: "Sprache: de, uz, en oder ru.",
  MISSING_CHUNKS: "Beim Hochladen fehlen Teile. Bitte erneut versuchen.",
  SIZE_MISMATCH: "Die Dateigröße stimmt nach dem Hochladen nicht. Bitte erneut versuchen.",
  AUDIO_TOOL_MISSING: "Die Audioverarbeitung ist auf dem Server nicht verfügbar.",
  INVALID_TRANSITION: "Diese Entscheidung ist für den aktuellen Stand nicht möglich.",
  USER_NOT_FOUND: "Benutzer nicht gefunden.",
  NOT_PAID: "Dieser Inhalt ist kostenlos.",
};

export function medienError(err: unknown, fallback = "Aktion fehlgeschlagen."): string {
  const data = (err as { response?: { data?: { message?: unknown; detail?: unknown } } })?.response?.data;
  const raw = data?.message ?? data?.detail;
  if (typeof raw === "string") {
    const code = raw.split(":")[0].trim();
    return KNOWN[code] ?? (/^[A-Z_]+(:|$)/.test(raw) ? raw.replace(/^[A-Z_]+:?\s*/, "") || fallback : raw);
  }
  return fallback;
}

export const getStats = async () => (await api.get<Stats>(`${BASE}/stats`)).data;

export const getCategories = async (kind: "BOOK" | "FILM") => (await api.get<AdminCategory[]>(`${BASE}/categories`, { params: { kind } })).data;
export const createCategory = async (kind: "BOOK" | "FILM", name: string) => (await api.post<AdminCategory>(`${BASE}/categories`, { kind, name })).data;
export const updateCategory = async (id: string, data: { name?: string; sort_order?: number; is_active?: boolean }) => (await api.put<AdminCategory>(`${BASE}/categories/${id}`, data)).data;
export const deleteCategory = async (id: string) => { await api.delete(`${BASE}/categories/${id}`); };

export interface ListQuery { q?: string; status?: string; access?: string; page?: number; page_size?: number }
export const listItems = async (kind: Kind, query: ListQuery) =>
  (await api.get<AdminPage>(`${BASE}/${ROUTE[kind]}`, { params: Object.fromEntries(Object.entries(query).filter(([, v]) => v !== "" && v !== undefined)) })).data;
export const createItem = async (kind: "BOOK" | "FILM", data: ItemInput) => (await api.post<AdminItem>(`${BASE}/${ROUTE[kind]}`, data)).data;
export const updateItem = async (kind: Kind, id: string, data: ItemInput) => (await api.put<AdminItem>(`${BASE}/${ROUTE[kind]}/${id}`, data)).data;
export const deleteItem = async (kind: Kind, id: string) => { await api.delete(`${BASE}/${ROUTE[kind]}/${id}`); };
export const uploadCover = async (kind: Kind, id: string, file: File, onProgress?: Progress) => {
  const form = new FormData();
  form.append("file", file);
  return (await api.post<AdminItem>(`${BASE}/${ROUTE[kind]}/${id}/cover`, form, multipart(onProgress))).data;
};
export const uploadBookFile = async (id: string, file: File, onProgress?: Progress) => {
  const form = new FormData();
  form.append("file", file);
  return (await api.post<AdminItem>(`${BASE}/books/${id}/file`, form, multipart(onProgress))).data;
};

/** One song with its metadata — the bulk upload calls this once per file (own progress, own error). */
export const uploadSong = async (file: File, meta: Record<string, string | number | boolean | undefined>, cover: File | null, onProgress?: Progress) => {
  const form = new FormData();
  form.append("file", file);
  if (cover) form.append("cover", cover);
  Object.entries(meta).forEach(([k, v]) => { if (v !== undefined && v !== "") form.append(k, String(v)); });
  return (await api.post<AdminItem>(`${BASE}/songs`, form, multipart(onProgress))).data;
};
export const replaceSongFile = async (id: string, file: File, onProgress?: Progress) => {
  const form = new FormData();
  form.append("file", file);
  return (await api.post<AdminItem>(`${BASE}/songs/${id}/file`, form, multipart(onProgress))).data;
};

// ---- films: single (≤ 90 MB) or chunked video upload, external link, subtitles ----
export const setExternalUrl = async (id: string, url: string | null) => (await api.put<AdminItem>(`${BASE}/films/${id}/external-url`, { url })).data;

/** Streams a video in chunks of the size the server announces (never the whole file in one request or in memory). */
export async function uploadFilmVideo(id: string, file: File, onProgress?: Progress): Promise<AdminItem> {
  const init = (await api.post<{ upload_id: string; chunk_size: number; chunks: number }>(`${BASE}/films/${id}/video/init`, { filename: file.name, size: file.size })).data;
  try {
    for (let i = 0; i < init.chunks; i += 1) {
      const slice = file.slice(i * init.chunk_size, Math.min(file.size, (i + 1) * init.chunk_size));
      for (let attempt = 0; ; attempt += 1) {
        try {
          await api.put(`${BASE}/films/${id}/video/${init.upload_id}/${i}`, slice, {
            headers: { "Content-Type": "application/octet-stream" },
            onUploadProgress: (e) => onProgress?.(Math.min(99, Math.round(((i * init.chunk_size + (e.loaded ?? 0)) / file.size) * 100))),
          });
          break;
        } catch (err) {
          if (attempt >= 2) throw err; // a failed chunk is retried twice before giving up
        }
      }
    }
    onProgress?.(99);
    const done = (await api.post<AdminItem>(`${BASE}/films/${id}/video/${init.upload_id}/complete`)).data;
    onProgress?.(100);
    return done;
  } catch (err) {
    await api.delete(`${BASE}/films/${id}/video/${init.upload_id}`).catch(() => undefined);
    throw err;
  }
}
export const uploadSubtitle = async (id: string, language: string, file: File, label?: string) => {
  const form = new FormData();
  form.append("language", language);
  if (label) form.append("label", label);
  form.append("file", file);
  return (await api.post<AdminItem>(`${BASE}/films/${id}/subtitles`, form, multipart())).data;
};
export const deleteSubtitle = async (id: string, subtitleId: string) => (await api.delete<AdminItem>(`${BASE}/films/${id}/subtitles/${subtitleId}`)).data;

/** The stored file as a Blob for the admin preview (Bearer-authenticated, never a public URL). */
export const previewBlob = async (kind: Kind, id: string) => (await api.get(`${BASE}/${ROUTE[kind]}/${id}/file`, { responseType: "blob" })).data as Blob;

// ---- official playlists ----
export const getPlaylists = async () => (await api.get<AdminPlaylist[]>(`${BASE}/playlists`)).data;
export const savePlaylist = async (data: { name?: string; description?: string | null; status?: Status; sort_order?: number }, id?: string) =>
  (id ? await api.put<{ id: string }>(`${BASE}/playlists/${id}`, data) : await api.post<{ id: string }>(`${BASE}/playlists`, data)).data;
export const deletePlaylist = async (id: string) => { await api.delete(`${BASE}/playlists/${id}`); };
export const uploadPlaylistCover = async (id: string, file: File) => {
  const form = new FormData();
  form.append("file", file);
  await api.post(`${BASE}/playlists/${id}/cover`, form, multipart());
};
export const getPlaylistSongs = async (id: string) => (await api.get<{ id: string; title: string; artist: string | null; status: Status; position: number }[]>(`${BASE}/playlists/${id}/songs`)).data;
export const setPlaylistSongs = async (id: string, songIds: string[]) => (await api.put(`${BASE}/playlists/${id}/songs`, { song_ids: songIds })).data;

// ---- purchases (Super Admin) ----
export const getPurchases = async (status?: string) => (await api.get<PurchaseRow[]>(`${BASE}/purchases`, { params: status ? { status } : {} })).data;
export const decidePurchase = async (id: string, status: "GRANTED" | "REJECTED" | "REVOKED", note?: string) => (await api.post(`${BASE}/purchases/${id}/decision`, { status, note: note || null })).data;
export const grantAccess = async (data: { kind: Kind; content_id: string; email: string; note?: string }) => (await api.post(`${BASE}/purchases/grant`, data)).data;
