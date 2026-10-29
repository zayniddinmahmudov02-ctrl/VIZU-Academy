import { api } from "@/services/api";

import type { ReplyRef } from "./reply-preview";

const BASE = "/api/v1/global-chat";
const ADMIN = "/api/v1/admin/global-chat";

export const MAX_LENGTH = 2000;

/** "deleted" (by the author) only ever reaches moderators */
export type MessageStatus = "visible" | "pending" | "hidden" | "deleted";
export type RestrictionKind = "mute" | "ban";
export type MuteDuration = "10m" | "1h" | "24h" | "3d" | "7d" | "30d" | "custom";
export type BanDuration = "1y" | "2y" | "3y" | "5y" | "permanent";

export interface ChatMessage {
  id: string;
  /** null for a hidden message (moderators get the text) */
  body: string | null;
  status: MessageStatus;
  created_at: string;
  /** set when the author changed the text */
  edited_at: string | null;
  sender: { id: string; name: string; badge: "admin" | "teacher" | null; email?: string; role?: string } | null;
  mine: boolean;
  is_pinned: boolean;
  pinned_at: string | null;
  /** the message this one answers — built by the server (null: no reply) */
  reply_to?: ReplyRef | null;
  // moderators only
  flagged_words?: string[];
  hidden_reason?: string | null;
  hidden_at?: string | null;
  deleted_at?: string | null;
  can_restrict?: boolean;
}

export interface MessageVersion { id: string; previous_body: string; previous_status: MessageStatus; edited_at: string }

/** Edit / delete are offered for the caller's own messages only — the server checks again. */
export function canEditOwn(m: ChatMessage): boolean {
  return m.mine && (m.status === "visible" || m.status === "pending") && !m.is_pinned;
}

export function canDeleteOwn(m: ChatMessage): boolean {
  return m.mine && (m.status === "visible" || m.status === "pending");
}

export interface ViewerStatus {
  can_post: boolean;
  is_moderator: boolean;
  restriction: { kind: RestrictionKind; ends_at: string | null; permanent: boolean; note: string | null } | null;
}

interface Envelope {
  pinned: ChatMessage[];
  me: ViewerStatus;
  unread: number;
  /** pass back as `since` on the next poll */
  sync: string;
}

export interface HistoryPage extends Envelope {
  items: ChatMessage[];
  has_more: boolean;
}

export interface Updates extends Envelope {
  /** the client fell too far behind: reload the newest page */
  reset: boolean;
  items: ChatMessage[];
  removed_ids: string[];
}

export interface Restriction {
  id: string;
  kind: RestrictionKind;
  state: "active" | "expired" | "revoked";
  starts_at: string;
  ends_at: string | null;
  permanent: boolean;
  reason: string;
  public_note: string | null;
  created_at: string;
  user: { id: string; name: string; email: string | null; role: string | null };
  created_by: string | null;
  revoked_at: string | null;
  revoke_reason: string | null;
}

export interface ModerationAction {
  id: string;
  action: string;
  created_at: string;
  reason: string | null;
  meta: Record<string, unknown> | null;
  /** null = the word filter */
  actor: string | null;
  target_user: { id: string; name: string } | null;
  message_id: string | null;
  restriction_id: string | null;
}

export interface Paged<T> { items: T[]; total: number; page: number; page_size: number }

export interface ChatUser { id: string; name: string; email: string; role: string; is_moderator: boolean; status: ViewerStatus }

export interface UserHistory {
  user: { id: string; name: string; email: string; role: string; is_moderator: boolean };
  status: ViewerStatus;
  messages: { total: number; hidden: number; pending: number; flagged: number; edited: number; deleted: number };
  restrictions: Restriction[];
  actions: ModerationAction[];
}

export interface ChatStats { messages_24h: number; pending: number; hidden_7d: number; pinned: number; active_mutes: number; active_bans: number }

export interface WordFilter { enabled: boolean; words: string[]; is_default: boolean; updated_at: string | null }

export interface RestrictionInput {
  user_id: string;
  kind: RestrictionKind;
  duration: MuteDuration | BanDuration;
  ends_at?: string;
  reason: string;
  public_note?: string;
  message_id?: string;
}

/** The backend's error code (detail), e.g. "chat_muted". */
export function errorCode(err: unknown): string | null {
  const data = (err as { response?: { data?: { detail?: unknown; message?: unknown } } })?.response?.data;
  const code = data?.detail ?? data?.message;
  return typeof code === "string" ? code : null;
}

export function errorStatus(err: unknown): number | null {
  return (err as { response?: { status?: number } })?.response?.status ?? null;
}

const clean = (p: Record<string, unknown>) => Object.fromEntries(Object.entries(p).filter(([, v]) => v !== undefined && v !== "" && v !== null));

// chat
export const getHistory = async (before?: string) =>
  (await api.get<HistoryPage>(`${BASE}/messages`, { params: clean({ before }) })).data;
export const getUpdates = async (since: string) => (await api.get<Updates>(`${BASE}/updates`, { params: { since } })).data;
/** replyToId: only the id — the server checks it and builds the quote */
export const sendMessage = async (body: string, replyToId?: string | null) =>
  (await api.post<ChatMessage>(`${BASE}/messages`, clean({ body, reply_to_id: replyToId }))).data;
export const editMessage = async (id: string, body: string) => (await api.patch<ChatMessage>(`${BASE}/messages/${id}`, { body })).data;
export const deleteMessage = async (id: string) => api.delete(`${BASE}/messages/${id}`);
export const getUnreadCount = async () => (await api.get<{ unread: number }>(`${BASE}/unread-count`)).data?.unread ?? 0;
export const markRead = async (untilId?: string) => api.post(`${BASE}/read`, clean({ until_id: untilId }));

// moderation
export const moderateMessage = async (id: string, action: "pin" | "unpin" | "hide" | "unhide" | "approve", reason?: string) =>
  (await api.patch<ChatMessage>(`${ADMIN}/messages/${id}`, clean({ action, reason }))).data;
export const createRestriction = async (data: RestrictionInput) => (await api.post<Restriction>(`${ADMIN}/restrictions`, clean({ ...data }))).data;
export const updateRestriction = async (id: string, data: { ends_at?: string; ban_years?: number; permanent?: boolean; reason?: string; public_note?: string }) =>
  (await api.patch<Restriction>(`${ADMIN}/restrictions/${id}`, data)).data;
export const revokeRestriction = async (id: string, reason?: string) =>
  (await api.post<Restriction>(`${ADMIN}/restrictions/${id}/revoke`, clean({ reason }))).data;
export const getRestrictions = async (params: { state?: string; kind?: string; user_id?: string; q?: string; page?: number }) =>
  (await api.get<Paged<Restriction>>(`${ADMIN}/restrictions`, { params: clean(params) })).data;
export const getAdminMessages = async (params: { filter?: string; user_id?: string; q?: string; page?: number }) =>
  (await api.get<Paged<ChatMessage>>(`${ADMIN}/messages`, { params: clean(params) })).data;
export const getMessageEdits = async (id: string) => (await api.get<MessageVersion[]>(`${ADMIN}/messages/${id}/edits`)).data ?? [];
export const getActions = async (params: { user_id?: string; action?: string; page?: number }) =>
  (await api.get<Paged<ModerationAction>>(`${ADMIN}/actions`, { params: clean(params) })).data;
export const getStats = async () => (await api.get<ChatStats>(`${ADMIN}/stats`)).data;
export const searchUsers = async (q: string) => (await api.get<ChatUser[]>(`${ADMIN}/users`, { params: { q } })).data ?? [];
export const getUserHistory = async (userId: string) => (await api.get<UserHistory>(`${ADMIN}/users/${userId}`)).data;
export const getWordFilter = async () => (await api.get<WordFilter>(`${ADMIN}/word-filter`)).data;
export const saveWordFilter = async (data: { enabled: boolean; words: string[] }) => (await api.put<WordFilter>(`${ADMIN}/word-filter`, data)).data;
export const resetWordFilter = async () => (await api.delete<WordFilter>(`${ADMIN}/word-filter`)).data;

/** Calendar years (29 Feb → 28 Feb), the same rule as the server. */
export function addYears(date: Date, years: number): Date {
  const d = new Date(date);
  const month = d.getMonth();
  d.setFullYear(d.getFullYear() + years);
  if (d.getMonth() !== month) d.setDate(0);
  return d;
}

export function fmtDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

/** "14:05" today, "28.10. 14:05" this year, else with the year. */
export function fmtMessageTime(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const time = d.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" });
  if (d.toDateString() === now.toDateString()) return time;
  const date = d.toLocaleDateString("de-DE", d.getFullYear() === now.getFullYear() ? { day: "2-digit", month: "2-digit" } : { day: "2-digit", month: "2-digit", year: "numeric" });
  return `${date} ${time}`;
}
