import { API_URL } from "@/constants/api";
import { getToken } from "@/src/lib/token";
import { api } from "@/src/services/api";

import type {
  BookCard, Category, ContinueItem, CueList, FilmCard, LookupResult, MediaKind, Overview, Page, Playlist, PlaylistDetail, PlayerState, Progress,
  PurchaseInfo, SongCard, SubtitlePrefs, WatchInfo, AnyCard,
} from "../types";

const BASE = "/api/v1/medien";

/** `/api/v1/...` paths from the backend (covers, signed stream URLs) as absolute URLs for <img>, <audio>, <video>, <track>. */
export function mediaUrl(path: string | null | undefined): string {
  if (!path) return "";
  return /^https?:\/\//i.test(path) ? path : `${API_URL.replace(/\/$/, "")}${path}`;
}

type Params = Record<string, string | number | boolean | null | undefined>;

function clean(params: Params): Params {
  return Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "" && v !== false));
}

export async function getOverview() {
  return (await api.get<Overview>(`${BASE}/overview`)).data;
}

export async function getCategories(kind: "BOOK" | "FILM") {
  return (await api.get<Category[]>(`${BASE}/categories`, { params: { kind } })).data;
}

export async function getSpecialOffers() {
  return (await api.get<AnyCard[]>(`${BASE}/special-offers`)).data;
}

export interface BookQuery { category?: string; level?: string; q?: string; sort?: string; special?: boolean; access?: string; featured?: boolean; page?: number; page_size?: number }
export async function getBooks(query: BookQuery) {
  return (await api.get<Page<BookCard>>(`${BASE}/books`, { params: clean({ ...query }) })).data;
}
export async function getBook(id: string) {
  return (await api.get<BookCard>(`${BASE}/books/${id}`)).data;
}
export async function openBook(id: string) {
  return (await api.post<{ url: string; title: string; progress: Progress | null }>(`${BASE}/books/${id}/open`)).data;
}

export interface SongQuery { q?: string; sort?: string; featured?: boolean; favorites?: boolean; playlist_id?: string; genre?: string; level?: string; page?: number; page_size?: number }
export async function getSongs(query: SongQuery) {
  return (await api.get<Page<SongCard>>(`${BASE}/songs`, { params: clean({ ...query }) })).data;
}
/** The signed audio URL; `count=false` for a silent resume (no history entry, no counter). */
export async function playSong(id: string, count = true) {
  return (await api.post<{ url: string; id: string }>(`${BASE}/songs/${id}/play`, null, { params: count ? {} : { count: false } })).data;
}
export async function setFavorite(id: string, on: boolean) {
  return (on ? await api.put(`${BASE}/songs/${id}/favorite`) : await api.delete(`${BASE}/songs/${id}/favorite`)).data as { song_id: string; favorite: boolean };
}
export async function getHistory() {
  return (await api.get<SongCard[]>(`${BASE}/history`)).data;
}

export async function getPlaylists() {
  return (await api.get<Playlist[]>(`${BASE}/playlists`)).data;
}
export async function getPlaylist(id: string) {
  return (await api.get<PlaylistDetail>(`${BASE}/playlists/${id}`)).data;
}
export async function createPlaylist(name: string, description?: string) {
  return (await api.post<Playlist>(`${BASE}/playlists`, { name, description: description || null })).data;
}
export async function renamePlaylist(id: string, name: string, description?: string | null) {
  return (await api.put<Playlist>(`${BASE}/playlists/${id}`, { name, description: description ?? null })).data;
}
export async function deletePlaylist(id: string) {
  await api.delete(`${BASE}/playlists/${id}`);
}
export async function addToPlaylist(id: string, songId: string) {
  return (await api.post<Playlist>(`${BASE}/playlists/${id}/songs`, { song_id: songId })).data;
}
export async function removeFromPlaylist(id: string, songId: string) {
  return (await api.delete<Playlist>(`${BASE}/playlists/${id}/songs/${songId}`)).data;
}
export async function reorderPlaylist(id: string, songIds: string[]) {
  return (await api.put<Playlist>(`${BASE}/playlists/${id}/order`, { song_ids: songIds })).data;
}

export interface FilmQuery { category?: string; level?: string; q?: string; genre?: string; access?: string; min_minutes?: number; max_minutes?: number; featured?: boolean; special?: boolean; sort?: string; page?: number; page_size?: number }
export async function getFilms(query: FilmQuery) {
  return (await api.get<Page<FilmCard>>(`${BASE}/films`, { params: clean({ ...query }) })).data;
}
export async function getFilm(id: string) {
  return (await api.get<FilmCard>(`${BASE}/films/${id}`)).data;
}
export async function watchFilm(id: string) {
  return (await api.post<WatchInfo>(`${BASE}/films/${id}/watch`)).data;
}

export async function getContinue(completed = false) {
  return (await api.get<ContinueItem[]>(`${BASE}/continue`, { params: completed ? { completed: true } : {} })).data;
}
export async function saveProgress(kind: Exclude<MediaKind, "SONG">, id: string, position: number, total?: number | null, state?: PlayerState | null) {
  return (await api.put<Progress>(`${BASE}/progress/${kind}/${id}`, { position: Math.max(0, Math.round(position)), total: total ? Math.round(total) : null, ...(state ? { state } : {}) })).data;
}

/** Same save as `saveProgress`, as a `keepalive` fetch: it survives the page being closed or reloaded (an XHR is cancelled).
 * Fire and forget — used on pagehide / tab hidden, where nothing can wait for the answer. */
export function saveProgressKeepalive(kind: Exclude<MediaKind, "SONG">, id: string, position: number, total?: number | null, state?: PlayerState | null): void {
  const token = getToken();
  if (!token) return;
  try {
    void fetch(`${API_URL.replace(/\/$/, "")}${BASE}/progress/${kind}/${id}`, {
      method: "PUT", keepalive: true,
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ position: Math.max(0, Math.round(position)), total: total ? Math.round(total) : null, ...(state ? { state } : {}) }),
    }).catch(() => undefined);
  } catch {
    /* ignore */
  }
}

/** The student's subtitle settings (size, colour, background, position, font, on/off, dual) — kept per user on the server. */
export async function getPlayerPrefs() {
  return (await api.get<SubtitlePrefs>(`${BASE}/player-prefs`)).data;
}
export async function savePlayerPrefs(patch: Partial<SubtitlePrefs>) {
  return (await api.put<SubtitlePrefs>(`${BASE}/player-prefs`, patch)).data;
}

/** One subtitle track as plain cues. `url` is the signed `cues_url` from the watch answer (the token is in it). */
export async function getCues(url: string): Promise<CueList> {
  const res = await fetch(mediaUrl(url), { cache: "no-store" });
  if (!res.ok) throw new Error(`cues ${res.status}`);
  const data = (await res.json()) as CueList;
  return { ...data, cues: Array.isArray(data.cues) ? data.cues : [] };
}

/** A clicked subtitle word answered from the Wörterbuch (exact / inflected form / similar entries / nothing). */
export async function lookupWord(word: string) {
  return (await api.get<LookupResult>(`${BASE}/lookup`, { params: { word } })).data;
}

export async function requestPurchase(kind: MediaKind, contentId: string) {
  return (await api.post<{ id: string; status: string }>(`${BASE}/purchases`, { kind, content_id: contentId })).data;
}
export async function getMyPurchases() {
  return (await api.get<PurchaseInfo[]>(`${BASE}/purchases/mine`)).data;
}

/** A readable key for an API error code ("PURCHASE_REQUIRED: text" -> PURCHASE_REQUIRED), or null. */
export function errorCode(err: unknown): string | null {
  const data = (err as { response?: { data?: { message?: unknown; detail?: unknown } } })?.response?.data;
  const raw = data?.message ?? data?.detail;
  return typeof raw === "string" ? raw.split(":")[0].trim() : null;
}
