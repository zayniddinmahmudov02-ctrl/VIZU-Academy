export type MediaKind = "BOOK" | "SONG" | "FILM";
export type AccessType = "FREE" | "PAID";
export type Level = "A1" | "A2" | "B1" | "B2" | "C1";
export const LEVELS: Level[] = ["A1", "A2", "B1", "B2", "C1"];

export interface Progress {
  position: number;
  total: number | null;
  completed: boolean;
  updated_at?: string;
}

export interface MediaCard {
  id: string;
  kind: MediaKind;
  title: string;
  description: string | null;
  cover_url: string | null;
  language: string;
  level: Level | null;
  access_type: AccessType;
  price: number | null;
  old_price: number | null;
  discount_percent: number | null;
  is_special_offer: boolean;
  is_featured: boolean;
  /** the student may open it (FREE, bought, or staff) */
  owned: boolean;
  locked: boolean;
  status: string;
  currency: string;
}

export interface Category { id: string; name: string; slug: string; count?: number }

export interface BookCard extends MediaCard {
  author: string | null;
  category: Category | null;
  year: number | null;
  file_format: string | null;
  has_file: boolean;
  progress?: Progress | null;
}

export interface SongCard extends MediaCard {
  artist: string | null;
  album: string | null;
  genre: string | null;
  duration_ms: number | null;
  favorite: boolean;
}

export interface FilmSubtitleInfo { id: string; language: string; label: string }

export interface FilmCard extends MediaCard {
  category: Category | null;
  genre: string | null;
  year: number | null;
  duration_minutes: number | null;
  playable: boolean;
  subtitle_count?: number;
  subtitles?: FilmSubtitleInfo[];
  progress?: Progress | null;
}

export type AnyCard = BookCard | FilmCard;
export type ContinueItem = (BookCard | FilmCard) & { progress: Progress };

export interface Page<T> { items: T[]; total: number; page: number; page_size: number }

export interface Playlist { id: string; name: string; description: string | null; official: boolean; song_count: number; cover_url: string | null }
export interface PlaylistDetail extends Playlist { songs: SongCard[] }

export interface Overview {
  counts: { books: number; songs: number; films: number };
  continue: ContinueItem[];
  special_offers: AnyCard[];
  featured_film: FilmCard | null;
}

export interface WatchInfo {
  title: string;
  source: { type: "file" | "external"; url: string };
  subtitles: (FilmSubtitleInfo & { url: string })[];
  progress: Progress | null;
}

export interface PurchaseInfo { id: string; kind: MediaKind; content_id: string; title: string | null; price: number | null; status: string; created_at: string }
