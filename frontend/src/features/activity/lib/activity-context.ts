/** Activity heartbeats (pure helpers, unit-tested). What the page is about, when the student counts as active, and the
 * contexts sent to POST /activity/heartbeat. The server measures the time itself (backend app/services/activity/tracker.py);
 * the browser only says what is open / playing and whether the student is active. */

export type ActivityArea = "COURSE" | "WORTSCHATZ" | "MUSIC" | "FILM" | "BOOK" | "EXAM";

export interface ActivityContext {
  area: ActivityArea;
  ref_id: string | null;
  position: number | null;
}

export const HEARTBEAT_MS = 30_000;
/** no input for this long = idle (nothing is sent unless a song / film is playing) */
export const IDLE_MS = 120_000;

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function uuidOrNull(value: string | undefined): string | null {
  return value && UUID.test(value) ? value.toLowerCase() : null;
}

/** The learning area of a student page (books and films come from their players, not from the path). */
export function pageContext(pathname: string): ActivityContext | null {
  const parts = pathname.split("?")[0].split("/").filter(Boolean);
  const [first, second, third] = parts;
  if (first === "lektion" || first === "lessons") {
    const lesson = uuidOrNull(second);
    if (!lesson) return null;
    const section = (third ?? "").toLowerCase();
    const vocabulary = section.includes("wortschatz") || section.includes("vocabulary");
    return { area: vocabulary ? "WORTSCHATZ" : "COURSE", ref_id: lesson, position: null };
  }
  if (first === "woerterbuch") return { area: "WORTSCHATZ", ref_id: null, position: null };
  if (first === "vorbereitung" || first === "vizu-multilevel") return { area: "EXAM", ref_id: null, position: null };
  return null;
}

export function isActive(lastInputAt: number, now: number, visible: boolean): boolean {
  return visible && now - lastInputAt <= IDLE_MS;
}

export interface MediaNow {
  area: "MUSIC" | "FILM" | "BOOK";
  refId: string;
  /** seconds; MUSIC / FILM only */
  position: number | null;
  playing: boolean;
}

/** The contexts of one heartbeat, or null when nothing should be sent (idle and nothing playing). A page / book counts only
 * while active; a song or film only while it is playing (also in a hidden tab). */
export function heartbeatContexts(page: ActivityContext | null, media: MediaNow[], active: boolean): ActivityContext[] | null {
  const out: ActivityContext[] = [];
  if (active && page) out.push(page);
  for (const m of media) {
    if (!UUID.test(m.refId)) continue;
    if (m.area === "BOOK") {
      if (active) out.push({ area: "BOOK", ref_id: m.refId.toLowerCase(), position: null });
    } else if (m.playing && m.position !== null && Number.isFinite(m.position)) {
      out.push({ area: m.area, ref_id: m.refId.toLowerCase(), position: Math.max(0, Math.floor(m.position)) });
    }
  }
  const playing = media.some((m) => m.area !== "BOOK" && m.playing);
  if (!active && !playing) return null;
  return out.slice(0, 4);
}

export function newTabId(random: () => number = Math.random): string {
  let id = "";
  for (let i = 0; i < 16; i++) id += "abcdefghijklmnopqrstuvwxyz0123456789"[Math.floor(random() * 36)];
  return id;
}
