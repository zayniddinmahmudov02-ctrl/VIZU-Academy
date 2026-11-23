"use client";

import { useEffect, type RefObject } from "react";

import { mediaUrl } from "../services/medien-service";
import { usePlayerStore } from "../store/player-store";
import type { SongCard } from "../types";

interface Listener {
  remove: () => Promise<void> | void;
}

interface MediaPlugin {
  update: (state: Record<string, unknown>) => Promise<unknown>;
  stop: () => Promise<unknown>;
  addListener: (event: "action", cb: (e: { action: string; position?: number }) => void) => Promise<Listener> | Listener;
}

function plugin(): MediaPlugin | null {
  const cap = (window as unknown as { Capacitor?: { isNativePlatform?: () => boolean; Plugins?: { VizuMedia?: MediaPlugin } } }).Capacitor;
  return cap?.isNativePlatform?.() ? cap.Plugins?.VizuMedia ?? null : null;
}

/** Android app only: mirrors the music player into the app's MediaSession (lock screen, notification, headset) and maps its
 * buttons back to the player. The browser's own Media Session (global-audio-player.tsx) stays for the web. Starts only for
 * playback the user started (playing = true); X / an empty queue ends it. */
export function useNativeMediaControls(song: SongCard | null, playing: boolean, audioRef: RefObject<HTMLAudioElement | null>) {
  useEffect(() => {
    const p = typeof window !== "undefined" ? plugin() : null;
    if (!p) return;
    let handle: Listener | null = null;
    Promise.resolve(p.addListener("action", ({ action, position }) => {
      const s = usePlayerStore.getState();
      if (action === "play") usePlayerStore.setState({ playing: true });
      else if (action === "pause") usePlayerStore.setState({ playing: false });
      else if (action === "next") s.next();
      else if (action === "previous") s.prev();
      else if (action === "stop") s.stop();
      else if (action === "seekto" && typeof position === "number") s.seek(position);
    })).then((h) => { handle = h; }).catch(() => undefined);
    return () => { void handle?.remove(); };
  }, []);

  useEffect(() => {
    const p = typeof window !== "undefined" ? plugin() : null;
    if (!p) return;
    if (!song) {
      void p.stop().catch(() => undefined);
      return;
    }
    const send = () => {
      const el = audioRef.current;
      const s = usePlayerStore.getState();
      void p.update({
        title: song.title, artist: song.artist ?? "", album: song.album ?? "VIZU Medienwelt",
        artwork: song.cover_url ? mediaUrl(song.cover_url) : null, playing,
        position: el && Number.isFinite(el.currentTime) ? el.currentTime : 0,
        duration: el && Number.isFinite(el.duration) ? el.duration : (song.duration_ms ?? 0) / 1000,
        hasPrev: s.queue.length > 1 || (el?.currentTime ?? 0) > 3, hasNext: s.queue.length > 1,
      }).catch(() => undefined);
    };
    send();
    if (!playing) return;
    const id = window.setInterval(send, 15_000); // keeps the lock-screen progress close to the real position
    return () => window.clearInterval(id);
  }, [song, playing, audioRef]);
}
