import type { SongCard } from "../types";
import type { RepeatMode } from "./player-store";

const KEY = "vizu-player-v1";

export interface PersistedPlayer {
  queue: SongCard[];
  index: number;
  position: number;
  shuffle: boolean;
  repeat: RepeatMode;
  volume: number;
  muted: boolean;
}

/** localStorage can be blocked or full (private window): the player then simply starts empty. */
export function loadPlayer(): PersistedPlayer | null {
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return null;
    const v = JSON.parse(raw) as Partial<PersistedPlayer>;
    if (!Array.isArray(v.queue) || !v.queue.every((s) => s && typeof s.id === "string" && typeof s.title === "string")) return null;
    return {
      queue: v.queue.slice(0, 200),
      index: Number.isInteger(v.index) ? (v.index as number) : 0,
      position: typeof v.position === "number" && v.position >= 0 ? v.position : 0,
      shuffle: !!v.shuffle,
      repeat: v.repeat === "all" || v.repeat === "one" ? v.repeat : "off",
      volume: typeof v.volume === "number" ? Math.min(1, Math.max(0, v.volume)) : 0.8,
      muted: !!v.muted,
    };
  } catch {
    return null;
  }
}

export function savePlayer(state: PersistedPlayer): void {
  try {
    if (!state.queue.length) window.localStorage.removeItem(KEY);
    else window.localStorage.setItem(KEY, JSON.stringify({ ...state, queue: state.queue.slice(0, 200) }));
  } catch {
    /* ignore */
  }
}

export function forgetPlayer(): void {
  try {
    window.localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}
