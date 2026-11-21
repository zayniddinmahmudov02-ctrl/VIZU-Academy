/** Pure helpers of the video lesson UI (no React, no browser APIs): unit tested in tests/unit/video-rooms.test.mjs. */

/** LiveKit protocol TrackSource values in ParticipantPermission.canPublishSources (livekit-client does not export the enum). */
export const SOURCE = { camera: 1, microphone: 2, screenShare: 3, screenShareAudio: 4 } as const;

/** Participant attributes set by the backend only (clients may not change their own). */
export const ATTR_ROLE = "vizu.role";
export const ATTR_HAND = "vizu.hand";

export const CHAT_MAX = 500;

export interface RoomMeta { title: string; chat: boolean; screenShare: boolean; mic: boolean }

/** Room-wide switches the backend writes to the LiveKit room metadata. */
export function parseRoomMeta(metadata: string | undefined | null): RoomMeta {
  const out: RoomMeta = { title: "", chat: true, screenShare: false, mic: true };
  if (!metadata) return out;
  try {
    const m = JSON.parse(metadata) as Record<string, unknown>;
    if (typeof m.title === "string") out.title = m.title;
    if (typeof m.chat === "boolean") out.chat = m.chat;
    if (typeof m.screen_share === "boolean") out.screenShare = m.screen_share;
    if (typeof m.mic === "boolean") out.mic = m.mic;
  } catch {
    // not ours: keep the defaults
  }
  return out;
}

export function roleOf(metadata: string | undefined | null, attributes?: Readonly<Record<string, string>>): "host" | "student" {
  if (attributes?.[ATTR_ROLE] === "host") return "host";
  try {
    return metadata && (JSON.parse(metadata) as { role?: string }).role === "host" ? "host" : "student";
  } catch {
    return "student";
  }
}

/** "05:07", "1:02:03" — negative or unknown durations show "00:00". */
export function formatDuration(ms: number): string {
  const total = Number.isFinite(ms) && ms > 0 ? Math.floor(ms / 1000) : 0;
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const two = (n: number) => String(n).padStart(2, "0");
  return h > 0 ? `${h}:${two(m)}:${two(s)}` : `${two(m)}:${two(s)}`;
}

/** Columns of the grid view: as square as possible, at most 2 on a phone, 4 elsewhere. */
export function gridColumns(count: number, width: number): number {
  if (count <= 1) return 1;
  const max = width < 640 ? 2 : width < 1024 ? 3 : 4;
  return Math.min(max, Math.ceil(Math.sqrt(count)));
}

/** Raised hands in the order they went up (the attribute is an ISO time; empty = down). */
export function handsInOrder<T extends { identity: string; hand: string }>(items: T[]): T[] {
  return items.filter((i) => i.hand).sort((a, b) => a.hand.localeCompare(b.hand) || a.identity.localeCompare(b.identity));
}

/** Initials for a tile without video. */
export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  return (parts[0][0] + (parts.length > 1 ? parts[parts.length - 1][0] : "")).toUpperCase();
}

/** datetime-local value ("2026-11-21T18:30", local time) -> ISO with timezone; "" for empty / invalid. */
export function localInputToIso(value: string): string {
  if (!value) return "";
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? "" : d.toISOString();
}

/** Date -> datetime-local value in local time. */
export function toLocalInput(d: Date): string {
  const two = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${two(d.getMonth() + 1)}-${two(d.getDate())}T${two(d.getHours())}:${two(d.getMinutes())}`;
}

export const KNOWN_ERRORS = [
  "VIDEO_ROOM_NOT_FOUND", "VIDEO_ROOM_NOT_STARTED", "VIDEO_ROOM_NOT_LIVE", "VIDEO_ROOM_FULL", "VIDEO_ROOM_REMOVED", "VIDEO_ROOM_ALREADY_LIVE",
  "VIDEO_ROOM_NOT_SCHEDULED", "VIDEO_SERVICE_NOT_CONFIGURED", "VIDEO_SERVICE_UNAVAILABLE", "VIDEO_TOO_MANY_REQUESTS", "VIDEO_MODERATOR_REQUIRED",
  "VIDEO_JOIN_IN_PROGRESS", "GROUP_NOT_ACTIVE", "SCHEDULE_REQUIRED", "SCHEDULE_IN_PAST", "SCHEDULE_TOO_FAR", "TOO_MANY_SCHEDULED", "TITLE_REQUIRED",
  "CANNOT_MODERATE_HOST", "PARTICIPANT_NOT_FOUND", "NOT_IN_ROOM",
] as const;

/** Backend error code of an axios error ({"message": "CODE"} or {"detail": "CODE"}), or null. */
export function errorCodeOf(err: unknown): string | null {
  const data = (err as { response?: { data?: { detail?: unknown; message?: unknown } } })?.response?.data;
  const code = data?.message ?? data?.detail;
  return typeof code === "string" ? code.split(":")[0].trim() : null;
}

/** Translation key for an error: a known backend code, else the generic text. */
export function errorKey(err: unknown): string {
  const code = errorCodeOf(err);
  return code && (KNOWN_ERRORS as readonly string[]).includes(code) ? `videoRoom.err_${code}` : "videoRoom.err_generic";
}

/** Camera / microphone error -> translation key (DOMException names of getUserMedia). */
export function mediaErrorKey(err: unknown, secure = true): string {
  if (!secure) return "videoRoom.perm_insecure";
  const name = (err as { name?: string })?.name ?? "";
  if (name === "NotAllowedError" || name === "SecurityError" || name === "PermissionDeniedError") return "videoRoom.perm_denied";
  if (name === "NotFoundError" || name === "DevicesNotFoundError" || name === "OverconstrainedError") return "videoRoom.perm_notfound";
  if (name === "NotReadableError" || name === "TrackStartError" || name === "AbortError") return "videoRoom.perm_busy";
  return "videoRoom.perm_other";
}

/** Clean a chat text before sending: trim, collapse control characters, cut to CHAT_MAX. */
export function cleanChat(text: string): string {
  return text.replace(/[\u0000-\u0008\u000B-\u001F\u007F]/g, "").trim().slice(0, CHAT_MAX);
}
