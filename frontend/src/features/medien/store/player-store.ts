import { create } from "zustand";

import type { SongCard } from "../types";

export type RepeatMode = "off" | "all" | "one";

/** The global music player state (one player for the whole student panel; the single <audio> element lives in
 * GlobalAudioPlayer inside the dashboard layout, so changing pages never recreates it). `playing` is the intent, the
 * component keeps the element in sync. Only `PERSISTED` keys survive a reload (see persist.ts). */
interface PlayerState {
  queue: SongCard[];
  index: number;
  playing: boolean;
  shuffle: boolean;
  repeat: RepeatMode;
  volume: number;
  muted: boolean;
  currentTime: number;
  duration: number;
  loading: boolean;
  error: string | null;
  queueOpen: boolean;
  /** a seek requested by the UI (seconds); the component applies it and clears it */
  seekTo: number | null;
  /** position to resume at after a reload, for the first load of the restored song */
  resumeAt: number | null;
  /** bumped for every explicit "play this" so the same song can restart */
  playNonce: number;

  playQueue: (songs: SongCard[], startIndex?: number) => void;
  playIndex: (index: number) => void;
  toggle: () => void;
  pause: () => void;
  next: (auto?: boolean) => void;
  prev: () => void;
  seek: (seconds: number) => void;
  setVolume: (v: number) => void;
  toggleMute: () => void;
  toggleShuffle: () => void;
  cycleRepeat: () => void;
  removeFromQueue: (index: number) => void;
  enqueue: (song: SongCard) => void;
  toggleQueue: () => void;
  clear: () => void;
  patchSong: (id: string, patch: Partial<SongCard>) => void;
  setProgress: (currentTime: number, duration: number) => void;
  setLoading: (v: boolean) => void;
  setError: (e: string | null) => void;
  restore: (s: { queue: SongCard[]; index: number; position: number; shuffle: boolean; repeat: RepeatMode; volume: number; muted: boolean }) => void;
  clearSeek: () => void;
  clearResume: () => void;
}

const playable = (s: SongCard) => !s.locked;

function pickNext(state: PlayerState, auto: boolean): number | null {
  const { queue, index, repeat, shuffle } = state;
  const open = queue.map((s, i) => (playable(s) ? i : -1)).filter((i) => i >= 0);
  if (!open.length) return null;
  if (auto && repeat === "one" && playable(queue[index])) return index;
  if (shuffle && open.length > 1) {
    const others = open.filter((i) => i !== index);
    return others[Math.floor(Math.random() * others.length)];
  }
  const after = open.find((i) => i > index);
  if (after !== undefined) return after;
  return repeat === "all" || !auto ? open[0] : null;
}

export const usePlayerStore = create<PlayerState>((set, get) => ({
  queue: [],
  index: 0,
  playing: false,
  shuffle: false,
  repeat: "off",
  volume: 0.8,
  muted: false,
  currentTime: 0,
  duration: 0,
  loading: false,
  error: null,
  queueOpen: false,
  seekTo: null,
  resumeAt: null,
  playNonce: 0,

  playQueue: (songs, startIndex = 0) => {
    const list = songs.filter(playable);
    if (!list.length) return;
    const wanted = songs[startIndex];
    const index = Math.max(0, wanted ? list.findIndex((s) => s.id === wanted.id) : 0);
    set((s) => ({ queue: list, index, playing: true, error: null, currentTime: 0, resumeAt: null, playNonce: s.playNonce + 1 }));
  },
  playIndex: (index) => {
    const { queue } = get();
    if (!queue[index] || !playable(queue[index])) return;
    set((s) => ({ index, playing: true, error: null, currentTime: 0, resumeAt: null, playNonce: s.playNonce + 1 }));
  },
  toggle: () => {
    if (!get().queue.length) return;
    set((s) => ({ playing: !s.playing }));
  },
  pause: () => set({ playing: false }),
  next: (auto = false) => {
    const target = pickNext(get(), auto);
    if (target === null) {
      set({ playing: false, currentTime: 0 });
      return;
    }
    set((s) => ({ index: target, playing: true, error: null, currentTime: 0, resumeAt: null, playNonce: s.playNonce + 1 }));
  },
  prev: () => {
    const { currentTime, queue, index } = get();
    if (currentTime > 3 || index === 0) {
      set({ seekTo: 0 });
      return;
    }
    const before = [...queue.keys()].filter((i) => i < index && playable(queue[i])).pop();
    if (before === undefined) set({ seekTo: 0 });
    else set((s) => ({ index: before, playing: true, error: null, currentTime: 0, resumeAt: null, playNonce: s.playNonce + 1 }));
  },
  seek: (seconds) => set({ seekTo: Math.max(0, seconds) }),
  setVolume: (v) => set({ volume: Math.min(1, Math.max(0, v)), muted: false }),
  toggleMute: () => set((s) => ({ muted: !s.muted })),
  toggleShuffle: () => set((s) => ({ shuffle: !s.shuffle })),
  cycleRepeat: () => set((s) => ({ repeat: s.repeat === "off" ? "all" : s.repeat === "all" ? "one" : "off" })),
  removeFromQueue: (i) =>
    set((s) => {
      if (!s.queue[i]) return s;
      const queue = s.queue.filter((_, k) => k !== i);
      if (!queue.length) return { ...s, queue: [], index: 0, playing: false, currentTime: 0, duration: 0 };
      if (i < s.index) return { ...s, queue, index: s.index - 1 };
      if (i === s.index) return { ...s, queue, index: Math.min(i, queue.length - 1), currentTime: 0, playNonce: s.playNonce + 1 };
      return { ...s, queue };
    }),
  enqueue: (song) =>
    set((s) => (playable(song) && !s.queue.some((q) => q.id === song.id) ? { queue: [...s.queue, song] } : s)),
  toggleQueue: () => set((s) => ({ queueOpen: !s.queueOpen })),
  clear: () => set({ queue: [], index: 0, playing: false, currentTime: 0, duration: 0, queueOpen: false, error: null, resumeAt: null }),
  patchSong: (id, patch) => set((s) => ({ queue: s.queue.map((q) => (q.id === id ? { ...q, ...patch } : q)) })),
  setProgress: (currentTime, duration) => set({ currentTime, duration }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  restore: ({ queue, index, position, shuffle, repeat, volume, muted }) =>
    set({ queue, index: Math.min(Math.max(0, index), Math.max(0, queue.length - 1)), resumeAt: position > 0 ? position : null, currentTime: position, shuffle, repeat, volume, muted, playing: false }),
  clearSeek: () => set({ seekTo: null }),
  clearResume: () => set({ resumeAt: null }),
}));

export const currentSong = (s: Pick<PlayerState, "queue" | "index">): SongCard | null => s.queue[s.index] ?? null;
