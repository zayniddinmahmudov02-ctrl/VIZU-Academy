import { create } from "zustand";

/** The book reader and the film player register what is open here, so the heartbeat can say what the time is spent on.
 * The music player needs nothing: its state lives in the player store. */
export interface RegisteredMedia {
  area: "FILM" | "BOOK";
  refId: string;
  /** current position in seconds (films) */
  getPosition?: () => number | null;
  isPlaying?: () => boolean;
}

interface ActivityState {
  media: RegisteredMedia | null;
  setMedia: (media: RegisteredMedia) => void;
  clearMedia: (refId: string) => void;
}

export const useActivityStore = create<ActivityState>((set, get) => ({
  media: null,
  setMedia: (media) => set({ media }),
  clearMedia: (refId) => {
    if (get().media?.refId === refId) set({ media: null });
  },
}));
