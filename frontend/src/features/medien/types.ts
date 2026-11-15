import type { WordBrief, WordCard } from "@/features/woerterbuch/woerterbuch-service";

import type { Cue, PlayerState, SubtitlePrefs } from "./lib/subtitles";

export type { Cue, PlayerState, SubtitlePrefs };

export type MediaKind = "BOOK" | "SONG" | "FILM";
export type AccessType = "FREE" | "PAID";
export type Level = "A1" | "A2" | "B1" | "B2" | "C1";
export const LEVELS: Level[] = ["A1", "A2", "B1", "B2", "C1"];

export interface Progress {
  position: number;
  total: number | null;
  completed: boolean;
  updated_at?: string;
  /** films: subtitle language, dual subtitles, speed, quality of the last visit */
  state?: PlayerState | null;
  /** books: how far down the page `position` the student read (0..1), and when the reader was opened last */
  scroll?: number | null;
  opened_at?: string | null;
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

export type PaymentStatus = "PENDING" | "APPROVED" | "REJECTED" | "CANCELLED";

/** The student's latest payment for a book (shown on its page). The reason of a rejection is only set for REJECTED. */
export interface MyPayment { id: string; status: PaymentStatus; created_at: string; reviewed_at: string | null; admin_note: string | null }

/** `GET /medien/books/{id}`: the card plus what the reader / buy / download buttons need. */
export interface BookDetail extends BookCard {
  preview_pages_count: number;
  page_count: number | null;
  /** a locked PAID book whose first pages can be read without buying */
  preview_available: boolean;
  can_download: boolean;
  my_payment: MyPayment | null;
}

/** `POST /medien/books/{id}/open`: "full" = the whole PDF, "preview" = a separate PDF with only the first `preview_pages` pages. */
export interface OpenBookInfo {
  url: string;
  title: string;
  progress: Progress | null;
  mode: "full" | "preview";
  preview_pages: number | null;
  total_pages: number | null;
  can_download: boolean;
}

export interface BookPayment {
  id: string;
  book_id: string | null;
  book_title: string | null;
  amount: number;
  currency: string;
  status: PaymentStatus;
  has_receipt: boolean;
  receipt_type: string | null;
  no_receipt: boolean;
  transfer_date: string | null;
  transfer_time: string | null;
  note: string | null;
  created_at: string;
  reviewed_at: string | null;
  can_cancel: boolean;
  admin_note: string | null;
}

/** The card students pay to. */
export interface PaymentInfo { card_number: string; card_holder: string; currency: string; configured: boolean }

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

export interface WatchSubtitle extends FilmSubtitleInfo { url: string; cues_url: string; cue_count: number }
/** One quality of the video: "main" = the film's own file ("Original"), the others were uploaded by the admin (720p …). */
export interface VideoSource { id: string; label: string; height: number | null; url: string }
export interface FilmNeighbor { id: string; title: string }

export interface WatchInfo {
  title: string;
  source: { type: "file" | "external"; url: string };
  sources: VideoSource[];
  subtitles: WatchSubtitle[];
  progress: Progress | null;
  prefs: SubtitlePrefs;
  neighbors: { prev: FilmNeighbor | null; next: FilmNeighbor | null };
  duration_ms: number | null;
}

export interface CueList { language: string; label: string; cues: Cue[] }

/** Answer of `GET /medien/lookup`: exact headword / inflected form (`entries`), or only `suggestions`, or nothing. */
export interface LookupResult {
  word: string;
  status: "exact" | "form" | "similar" | "none";
  entries: WordCard[];
  suggestions: WordBrief[];
}

export interface PurchaseInfo { id: string; kind: MediaKind; content_id: string; title: string | null; price: number | null; status: string; created_at: string }
