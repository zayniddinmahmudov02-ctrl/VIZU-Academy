"use client";

import { useEffect, useRef, useState } from "react";

import { activeCues, cueKey, type Cue } from "../lib/subtitles";
import { getCues } from "../services/medien-service";
import type { WatchSubtitle } from "../types";

/** Loads every subtitle track of the film once, as plain cues (small files: a few hundred KB for all languages together). A track that
 * cannot be loaded gives an empty list and is reported in `failed` — the player keeps working without it. */
export function useCueTracks(subtitles: readonly WatchSubtitle[]) {
  const [tracks, setTracks] = useState<Record<string, Cue[]>>({});
  const [failed, setFailed] = useState<Record<string, boolean>>({});
  const requested = useRef(new Set<string>());

  useEffect(() => {
    let alive = true;
    for (const sub of subtitles) {
      if (requested.current.has(sub.id)) continue;
      requested.current.add(sub.id);
      getCues(sub.cues_url)
        .then((list) => { if (alive) setTracks((t) => ({ ...t, [sub.language]: list.cues })); })
        .catch(() => { if (alive) { setTracks((t) => ({ ...t, [sub.language]: [] })); setFailed((f) => ({ ...f, [sub.language]: true })); } });
    }
    return () => { alive = false; };
  }, [subtitles]);

  return { tracks, failed };
}

const NO_CUES: Cue[] = [];

/** The cue(s) shown right now for a track, derived from the VIDEO's own clock — never from timers — so seeking, pausing and every
 * playback speed stay in sync. While the video plays the check runs every frame (a few microseconds: binary search); the overlay re-renders
 * only when the shown cue set changes. */
export function useActiveCues(videoRef: React.RefObject<HTMLVideoElement | null>, cues: readonly Cue[] | undefined): Cue[] {
  // remembers which track the answer belongs to: right after a language switch the old answer is never shown for the new track
  const [state, setState] = useState<{ src: readonly Cue[] | undefined; list: Cue[] }>({ src: undefined, list: NO_CUES });
  const key = useRef("");

  useEffect(() => {
    const video = videoRef.current;
    key.current = ""; // a new track always publishes its first answer, even if it looks like the old one
    if (!video || !cues?.length) {
      setState({ src: cues, list: NO_CUES });
      return;
    }
    let raf = 0;
    const compute = () => {
      const next = activeCues(cues, video.currentTime * 1000);
      const k = `${cues.length}:${cueKey(next)}`;
      if (k !== key.current) { key.current = k; setState({ src: cues, list: next }); }
    };
    const loop = () => { compute(); raf = requestAnimationFrame(loop); };
    const start = () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(loop); };
    const stop = () => { cancelAnimationFrame(raf); compute(); };
    const events: [string, () => void][] = [["play", start], ["playing", start], ["pause", stop], ["ended", stop], ["seeking", compute], ["seeked", compute],
      ["timeupdate", compute], ["loadedmetadata", compute], ["ratechange", compute]];
    events.forEach(([name, fn]) => video.addEventListener(name, fn));
    compute();
    if (!video.paused) start();
    return () => { cancelAnimationFrame(raf); events.forEach(([name, fn]) => video.removeEventListener(name, fn)); };
  }, [videoRef, cues]);

  return state.src === cues ? state.list : NO_CUES;
}
