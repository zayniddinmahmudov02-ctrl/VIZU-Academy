import { api } from "@/src/services/api";

const BASE = "/api/v1/admin/medien";

export type Kind = "BOOK" | "SONG" | "FILM";
export type Status = "DRAFT" | "PUBLISHED" | "HIDDEN";
export type Access = "FREE" | "PAID";
export type FileStatus = "ok" | "missing" | "none";

export interface AdminCategory { id: string; kind: Kind; name: string; slug: string; sort_order: number; is_active: boolean; item_count: number }

export interface SubtitleWarning { code: string; count: number; detail: string }
export interface AdminSubtitle {
  id: string; language: string; label: string; file_status: FileStatus;
  /** result of the last check; 0 = a track from before the checks existed ("not checked yet") */
  cue_count: number; last_ms: number | null; format: "srt" | "vtt" | null; original_name: string | null; file_size: number | null;
  warnings: SubtitleWarning[]; updated_at?: string;
  /** students see APPROVED tracks only; an AI transcript / translation starts as DRAFT */
  status?: "DRAFT" | "APPROVED"; source?: "UPLOAD" | "AI" | "TRANSLATION"; source_language?: string | null; ai_model?: string | null;
  approved_at?: string | null; edited_at?: string | null;
}
export type JobStatus = "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
export interface SubtitleJob {
  id: string; kind: "TRANSCRIBE" | "TRANSLATE"; status: JobStatus; language: string; detected_language: string | null; translate_to: string[];
  replace: boolean; provider: string | null; model: string | null; progress_done: number; progress_total: number; attempts: number;
  error_code: string | null; error_message: string | null; result_subtitle_id: string | null; source_subtitle_id: string | null;
  stats: { cues?: number; pieces?: number; batches?: number; speakers_max_per_piece?: number; warnings?: number; from?: string };
  created_at: string; started_at: string | null; finished_at: string | null;
}
export interface AiServiceState { provider: string; configured: boolean; model: string | null; message: string | null }
export interface SubtitleAiStatus { speech_to_text: AiServiceState; translation: AiServiceState; ffmpeg: boolean; languages: string[]; chunk_seconds: number }
export interface AdminRendition { id: string; label: string; height: number | null; size: number; original_name: string | null; file_status: FileStatus }
export interface SubtitleReport { format: "srt" | "vtt"; encoding: string; cue_count: number; first_ms: number | null; last_ms: number | null; warnings: SubtitleWarning[] }
/** Cue = [start_ms, end_ms, plain text] */
export type PreviewCue = [number, number, string];
export interface SubtitleCheck { report: SubtitleReport; preview: PreviewCue[]; video_ms: number | null }
export interface SubtitlePreview extends AdminSubtitle { report: SubtitleReport; cues: PreviewCue[]; video_ms: number | null }

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
  /** PAID books: how many first pages everybody may read (default 10) and the pages of the PDF (empty until it was read once) */
  preview_pages_count?: number;
  page_count?: number | null;
  // song
  artist?: string | null;
  album?: string | null;
  genre?: string | null;
  duration_ms?: number | null;
  /** read from the file on upload: format (mp3, wav, m4a, aac, ogg, flac), bitrate, and whether the reading worked */
  audio_format?: string | null;
  bitrate_kbps?: number | null;
  metadata_status?: "OK" | "FAILED";
  metadata_note?: string | null;
  // film
  duration_minutes?: number | null;
  video_size?: number | null;
  external_url?: string | null;
  processing_status?: "NONE" | "UPLOADING" | "READY" | "FAILED";
  video_duration_ms?: number | null;
  video_format?: string | null;
  subtitles?: AdminSubtitle[];
  renditions?: AdminRendition[];
}

export interface AdminPage { items: AdminItem[]; total: number; page: number; page_size: number }

export interface ItemInput {
  title?: string; description?: string | null; language?: string; level?: string | null; access_type?: Access; price?: number | null; old_price?: number | null;
  is_special_offer?: boolean; is_featured?: boolean; status?: Status; author?: string | null; artist?: string | null; album?: string | null; genre?: string | null;
  year?: number | null; duration_minutes?: number | null; category_id?: string | null; preview_pages_count?: number;
}

export interface Stats {
  books: { total: number; free: number; paid: number; published: number };
  songs: { total: number; published: number; playlists: number; student_playlists: number };
  films: { total: number; free: number; paid: number; published: number };
  published: number; draft: number; total: number; pending_purchases: number; pending_book_payments: number; plays_total: number;
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
  SUBTITLE_EMPTY: "Die Untertitel-Datei ist leer.",
  SUBTITLE_BINARY: "Das ist keine Textdatei: Untertitel müssen .srt oder .vtt sein.",
  SUBTITLE_FORMAT: "Keine gültigen Zeitangaben gefunden. Erlaubt sind WebVTT (.vtt) und SubRip (.srt).",
  SUBTITLE_NO_CUES: "Die Datei enthält keinen verwendbaren Untertitel (alle Zeiten fehlerhaft oder ohne Text).",
  SUBTITLE_TOO_LARGE: "Zu viele Untertitel-Zeilen: das ist kein Film-Untertitel.",
  SUBTITLE_ENCODING: "Die Datei konnte nicht gelesen werden. Bitte als UTF-8 speichern.",
  SUBTITLE_EXISTS: "Für diese Sprache gibt es schon einen Untertitel. Erst ersetzen oder löschen (bei KI-Untertiteln: „Vorhandene ersetzen“ ankreuzen).",
  INVALID_QUALITY: "Qualität wie 360p, 480p, 720p oder 1080p angeben.",
  MAIN_VIDEO_REQUIRED: "Erst das Hauptvideo hochladen, dann weitere Qualitäten.",
  MISSING_CHUNKS: "Beim Hochladen fehlen Teile. Bitte erneut versuchen.",
  SIZE_MISMATCH: "Die Dateigröße stimmt nach dem Hochladen nicht. Bitte erneut versuchen.",
  AUDIO_TOOL_MISSING: "Die Audioverarbeitung ist auf dem Server nicht verfügbar.",
  PAYMENT_PENDING: "Für dieses Buch wartet schon eine Zahlung auf Prüfung.",
  REASON_REQUIRED: "Bitte einen Ablehnungsgrund angeben (der Student sieht ihn).",
  SELF_REVIEW_FORBIDDEN: "Niemand kann über seine eigene Zahlung entscheiden.",
  BOOK_GONE: "Das Buch existiert nicht mehr — die Zahlung kann nicht freigeschaltet werden.",
  INVALID_CARD_NUMBER: "Eine Kartennummer hat 16 bis 19 Ziffern.",
  CARD_HOLDER_TOO_LONG: "Der Name des Karteninhabers ist zu lang (höchstens 80 Zeichen).",
  NOTE_TOO_LONG: "Der Text ist zu lang (höchstens 500 Zeichen).",
  INVALID_TRANSITION: "Diese Entscheidung ist für den aktuellen Stand nicht möglich.",
  USER_NOT_FOUND: "Benutzer nicht gefunden.",
  NOT_PAID: "Dieser Inhalt ist kostenlos.",
  AI_NOT_CONFIGURED: "Der KI-Dienst ist auf dem Server nicht eingerichtet (API-Schlüssel fehlt). Ohne ihn werden keine Untertitel erzeugt.",
  VIDEO_MISSING: "Der Film hat keine hochgeladene Videodatei (ein externer Link kann nicht transkribiert werden).",
  FFMPEG_MISSING: "FFmpeg ist auf dem Server nicht verfügbar.",
  JOB_RUNNING: "Für diesen Film läuft bereits ein solcher Auftrag.",
  JOB_NOT_FAILED: "Nur ein fehlgeschlagener Auftrag kann wiederholt werden.",
  JOB_NOT_ACTIVE: "Der Auftrag läuft nicht mehr.",
  SAME_LANGUAGE: "Bitte eine andere Sprache als die der Vorlage wählen.",
  INVALID_CUE_TIME: "Eine Zeile hat ungültige Zeiten (das Ende muss nach dem Anfang liegen).",
  INVALID_CUE: "Eine Zeile ist ungültig.",
  CHECKSUM_MISMATCH: "Die Datei ist nicht vollständig angekommen — bitte erneut versuchen.",
  SONG_DUPLICATE: "Diese Datei ist schon als Song gespeichert.",
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
/** Bulk upload, before sending: which of these SHA-256 hashes are already stored as songs. */
export const checkSongDuplicates = async (sha256: string[]) =>
  (await api.post<{ existing: Record<string, { id: string; title: string; artist: string | null; status: Status }> }>(`${BASE}/songs/duplicates`, { sha256 })).data.existing;
export interface SongState { id: string; title: string; artist: string | null; audio_format: string | null; duration_ms: number | null; bitrate_kbps: number | null; file_size: number | null; metadata_status: string; metadata_note: string | null; status: Status }
/** Bulk upload, after sending: what the metadata queue read for these songs. */
export const getSongStates = async (ids: string[]) => (await api.post<SongState[]>(`${BASE}/songs/states`, { ids })).data;
export const getSongProcessing = async () => (await api.get<{ pending: number; processing: number }>(`${BASE}/songs/processing`)).data;
export const replaceSongFile = async (id: string, file: File, onProgress?: Progress) => {
  const form = new FormData();
  form.append("file", file);
  return (await api.post<AdminItem>(`${BASE}/songs/${id}/file`, form, multipart(onProgress))).data;
};

// ---- films: single (≤ 90 MB) or chunked video upload, external link, subtitles ----
export const setExternalUrl = async (id: string, url: string | null) => (await api.put<AdminItem>(`${BASE}/films/${id}/external-url`, { url })).data;

/** Streams a video in chunks of the size the server announces (never the whole file in one request or in memory). With `quality` ("720p")
 * the file becomes an additional quality of the film instead of its own video. */
export async function uploadFilmVideo(id: string, file: File, onProgress?: Progress, quality?: string): Promise<AdminItem> {
  const init = (await api.post<{ upload_id: string; chunk_size: number; chunks: number }>(`${BASE}/films/${id}/video/init`, { filename: file.name, size: file.size, ...(quality ? { quality } : {}) })).data;
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
/** Dry run: format, times, cleaning and fit to the video length of a file — nothing is stored. */
export const checkSubtitle = async (id: string, file: File) => {
  const form = new FormData();
  form.append("file", file);
  return (await api.post<SubtitleCheck>(`${BASE}/films/${id}/subtitles/check`, form, multipart())).data;
};
/** The stored track as plain cues with a fresh check — the admin preview. */
export const getSubtitlePreview = async (id: string, subtitleId: string) => (await api.get<SubtitlePreview>(`${BASE}/films/${id}/subtitles/${subtitleId}`)).data;
export const recheckSubtitle = async (id: string, subtitleId: string) => (await api.post<AdminItem>(`${BASE}/films/${id}/subtitles/${subtitleId}/check`)).data;
/** Re-assigns the language of a track and / or renames it (no file is touched). */
export const updateSubtitle = async (id: string, subtitleId: string, data: { language?: string; label?: string }) => (await api.put<AdminItem>(`${BASE}/films/${id}/subtitles/${subtitleId}`, data)).data;
export const deleteRendition = async (id: string, renditionId: string) => (await api.delete<AdminItem>(`${BASE}/films/${id}/renditions/${renditionId}`)).data;
/** approved=true: students see the track; false: back to draft. */
export const approveSubtitle = async (id: string, subtitleId: string, approved: boolean) => (await api.post<AdminItem>(`${BASE}/films/${id}/subtitles/${subtitleId}/approve`, { approved })).data;
/** The corrected lines become the track (cleaned like an upload; the status stays). */
export const saveSubtitleCues = async (id: string, subtitleId: string, cues: PreviewCue[]) => (await api.put<SubtitlePreview>(`${BASE}/films/${id}/subtitles/${subtitleId}/cues`, { cues })).data;
/** The track as a .srt / .vtt file (Bearer-authenticated download). */
export const downloadSubtitle = async (id: string, subtitleId: string, format: "srt" | "vtt") => {
  const res = await api.get(`${BASE}/films/${id}/subtitles/${subtitleId}/download`, { params: { format }, responseType: "blob" });
  const name = /filename="([^"]+)"/.exec(String(res.headers["content-disposition"] ?? ""))?.[1] ?? `subtitle.${format}`;
  return { blob: res.data as Blob, name };
};

// ---- AI subtitles (background jobs) ----
export const getFilm = async (id: string) => (await api.get<AdminItem>(`${BASE}/films/${id}`)).data;
export const getSubtitleAiStatus = async () => (await api.get<SubtitleAiStatus>(`${BASE}/subtitle-ai/status`)).data;
export const startAiSubtitles = async (id: string, data: { language: string; translate_to: string[]; replace: boolean }) =>
  (await api.post<SubtitleJob>(`${BASE}/films/${id}/subtitles/ai`, data)).data;
export const translateSubtitle = async (id: string, subtitleId: string, target: string, replace: boolean) =>
  (await api.post<SubtitleJob>(`${BASE}/films/${id}/subtitles/${subtitleId}/translate`, { target, replace })).data;
export const getSubtitleJobs = async (id: string) => (await api.get<SubtitleJob[]>(`${BASE}/films/${id}/subtitle-jobs`)).data;
export const retrySubtitleJob = async (id: string, jobId: string) => (await api.post<SubtitleJob>(`${BASE}/films/${id}/subtitle-jobs/${jobId}/retry`)).data;
export const cancelSubtitleJob = async (id: string, jobId: string) => (await api.post<SubtitleJob>(`${BASE}/films/${id}/subtitle-jobs/${jobId}/cancel`)).data;

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

// ---- book payment requests (Super Admin): the student's receipt or transfer time, checked by hand, then approved / rejected ----
export type PaymentStatus = "PENDING" | "APPROVED" | "REJECTED" | "CANCELLED";
export interface BookPaymentRow {
  id: string; book_id: string | null; book_title: string | null; amount: number; currency: string; status: PaymentStatus;
  has_receipt: boolean; receipt_type: string | null; receipt_size: number | null; no_receipt: boolean; transfer_date: string | null; transfer_time: string | null;
  note: string | null; created_at: string; reviewed_at: string | null; admin_note: string | null; card_last4: string | null;
  user_id: string; user_name: string | null; user_email: string | null; reviewed_by_id: string | null; reviewed_by_name: string | null;
}
export interface BookPaymentList { items: BookPaymentRow[]; total: number; page: number; page_size: number; counts: Record<PaymentStatus, number> }
export interface BookPaymentDetail extends BookPaymentRow {
  book_exists: boolean; book_price: number | null; book_access: string | null; history: BookPaymentRow[];
  purchases: { id: string; kind: Kind; title: string | null; status: string; price: number | null; decided_at: string | null; payment_request_id: string | null }[];
}
export interface BookPaymentSettings { card_number: string; card_holder: string; currency: string; configured: boolean }

export const getBookPayments = async (params: { status?: string; q?: string; page?: number; page_size?: number }) =>
  (await api.get<BookPaymentList>(`${BASE}/book-payments`, { params: Object.fromEntries(Object.entries(params).filter(([, v]) => v !== "" && v !== undefined)) })).data;
export const getBookPayment = async (id: string) => (await api.get<BookPaymentDetail>(`${BASE}/book-payments/${id}`)).data;
export const decideBookPayment = async (id: string, status: "APPROVED" | "REJECTED", note?: string) =>
  (await api.post<BookPaymentDetail>(`${BASE}/book-payments/${id}/decision`, { status, note: note?.trim() || null })).data;
/** The receipt as a Blob (Bearer-authenticated, never a public URL); the caller turns it into a short-lived object URL. */
export const getBookPaymentReceipt = async (id: string) => (await api.get(`${BASE}/book-payments/${id}/receipt`, { responseType: "blob" })).data as Blob;
export const getBookPaymentSettings = async () => (await api.get<BookPaymentSettings>(`${BASE}/book-payment-settings`)).data;
export const saveBookPaymentSettings = async (data: { card_number?: string; card_holder?: string }) => (await api.put<BookPaymentSettings>(`${BASE}/book-payment-settings`, data)).data;
