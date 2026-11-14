"use client";

/* eslint-disable @next/next/no-img-element -- covers come from the API with long cache headers; next/image would proxy them again */

import { useCallback, useEffect, useRef } from "react";
import Link from "next/link";
import { useQueryClient } from "@tanstack/react-query";
import { Heart, ListMusic, Loader2, Pause, Play, Repeat, Repeat1, Shuffle, SkipBack, SkipForward, Volume2, VolumeX, X } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import { errorCode, mediaUrl, playSong, setFavorite } from "../services/medien-service";
import { loadPlayer, savePlayer } from "../store/persist";
import { currentSong, usePlayerStore } from "../store/player-store";

// 44-byte silent WAV: played once inside the first user gesture so that mobile browsers allow later programmatic play()
const SILENT = "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YQAAAAA=";

export function formatTime(seconds: number): string {
  const s = Math.max(0, Math.floor(Number.isFinite(seconds) ? seconds : 0));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

/** The one music player of the whole student panel. It lives in the dashboard layout, so the single <audio> element is
 * never recreated when the student changes pages: music keeps playing on Bibliothek, Vorbereitung, Dashboard … The queue,
 * the song, the position, shuffle / repeat and volume are saved and restored after a reload (paused: browsers do not allow
 * autoplay without a click). The Media Session API adds lock-screen / headset controls where the device supports them. */
export default function GlobalAudioPlayer() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const audioRef = useRef<HTMLAudioElement>(null);
  const loadedFor = useRef<string | null>(null);
  const switching = useRef(false);
  const retried = useRef(false);

  const queue = usePlayerStore((s) => s.queue);
  const index = usePlayerStore((s) => s.index);
  const playing = usePlayerStore((s) => s.playing);
  const playNonce = usePlayerStore((s) => s.playNonce);
  const shuffle = usePlayerStore((s) => s.shuffle);
  const repeat = usePlayerStore((s) => s.repeat);
  const volume = usePlayerStore((s) => s.volume);
  const muted = usePlayerStore((s) => s.muted);
  const currentTime = usePlayerStore((s) => s.currentTime);
  const duration = usePlayerStore((s) => s.duration);
  const loading = usePlayerStore((s) => s.loading);
  const error = usePlayerStore((s) => s.error);
  const queueOpen = usePlayerStore((s) => s.queueOpen);
  const seekTo = usePlayerStore((s) => s.seekTo);
  const song = currentSong({ queue, index });
  const store = usePlayerStore.getState;

  // restore queue + position after a reload (paused)
  useEffect(() => {
    const saved = loadPlayer();
    if (saved && !store().queue.length) usePlayerStore.getState().restore(saved);
  }, [store]);

  // first user gesture: unlock the element for programmatic playback (mobile autoplay rules)
  useEffect(() => {
    const unlock = () => {
      const el = audioRef.current;
      if (el && !el.src) {
        el.muted = true;
        el.src = SILENT;
        void el.play().then(() => { el.pause(); el.muted = usePlayerStore.getState().muted; el.removeAttribute("src"); }).catch(() => { el.muted = usePlayerStore.getState().muted; });
      }
    };
    const opts = { once: true, passive: true } as const;
    window.addEventListener("pointerdown", unlock, opts);
    window.addEventListener("keydown", unlock, opts);
    return () => { window.removeEventListener("pointerdown", unlock); window.removeEventListener("keydown", unlock); };
  }, []);

  const load = useCallback(async (id: string, count: boolean, at: number | null) => {
    const el = audioRef.current;
    if (!el) return;
    usePlayerStore.getState().setLoading(true);
    switching.current = true;
    const { url } = await playSong(id, count);
    loadedFor.current = `${id}:${usePlayerStore.getState().playNonce}`;
    el.src = mediaUrl(url);
    if (at && at > 0) usePlayerStore.setState({ resumeAt: at });
    el.load();
    await el.play();
  }, []);

  // load the song's signed URL when it is played (or resumed); pause / play an already loaded one
  useEffect(() => {
    const el = audioRef.current;
    if (!el || !song || !playing) return;
    const key = `${song.id}:${playNonce}`;
    if (loadedFor.current === key) {
      void el.play().catch(() => usePlayerStore.setState({ playing: false }));
      return;
    }
    let cancelled = false;
    retried.current = false;
    const resume = usePlayerStore.getState().resumeAt;
    load(song.id, resume === null, resume).catch((err) => {
      if (cancelled) return;
      const code = errorCode(err);
      switching.current = false;
      usePlayerStore.getState().setLoading(false);
      if (code === "PURCHASE_REQUIRED" || code === "NOT_FOUND" || code === "FILE_MISSING") {
        usePlayerStore.getState().setError(code);
        usePlayerStore.getState().next(true);
      } else if ((err as { name?: string })?.name === "NotAllowedError") {
        usePlayerStore.setState({ playing: false }); // the browser wants a click first
      } else {
        usePlayerStore.getState().setError("PLAYBACK_FAILED");
        usePlayerStore.setState({ playing: false });
      }
    });
    return () => { cancelled = true; };
  }, [song?.id, playNonce, playing, load]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!playing) audioRef.current?.pause();
  }, [playing]);

  useEffect(() => {
    const el = audioRef.current;
    if (el) { el.volume = volume; el.muted = muted; }
  }, [volume, muted]);

  useEffect(() => {
    const el = audioRef.current;
    if (el && seekTo !== null) { el.currentTime = seekTo; usePlayerStore.getState().clearSeek(); }
  }, [seekTo]);

  // persist (every few seconds while playing, and on every change that matters)
  const persist = useCallback(() => {
    const s = usePlayerStore.getState();
    savePlayer({ queue: s.queue, index: s.index, position: audioRef.current?.currentTime ?? s.currentTime, shuffle: s.shuffle, repeat: s.repeat, volume: s.volume, muted: s.muted });
  }, []);
  useEffect(() => { persist(); }, [queue, index, shuffle, repeat, volume, muted, playing, persist]);
  useEffect(() => {
    const id = window.setInterval(() => { if (usePlayerStore.getState().playing) persist(); }, 4000);
    window.addEventListener("beforeunload", persist);
    return () => { window.clearInterval(id); window.removeEventListener("beforeunload", persist); };
  }, [persist]);

  // Media Session: lock screen / headset / notification controls
  useEffect(() => {
    if (typeof navigator === "undefined" || !("mediaSession" in navigator)) return;
    const ms = navigator.mediaSession;
    if (!song) { ms.metadata = null; return; }
    ms.metadata = new MediaMetadata({ title: song.title, artist: song.artist ?? "", album: song.album ?? "VIZU Medienwelt",
      artwork: song.cover_url ? [{ src: mediaUrl(song.cover_url), sizes: "512x512" }] : [] });
    const set = (action: MediaSessionAction, handler: MediaSessionActionHandler | null) => { try { ms.setActionHandler(action, handler); } catch { /* unsupported */ } };
    set("play", () => usePlayerStore.setState({ playing: true }));
    set("pause", () => usePlayerStore.setState({ playing: false }));
    set("previoustrack", () => usePlayerStore.getState().prev());
    set("nexttrack", () => usePlayerStore.getState().next());
    set("seekbackward", () => usePlayerStore.getState().seek((audioRef.current?.currentTime ?? 0) - 10));
    set("seekforward", () => usePlayerStore.getState().seek((audioRef.current?.currentTime ?? 0) + 10));
    set("seekto", (d) => { if (typeof d.seekTime === "number") usePlayerStore.getState().seek(d.seekTime); });
  }, [song]);
  useEffect(() => {
    if (typeof navigator !== "undefined" && "mediaSession" in navigator) navigator.mediaSession.playbackState = !song ? "none" : playing ? "playing" : "paused";
  }, [playing, song]);

  const onTime = () => {
    const el = audioRef.current;
    if (!el) return;
    usePlayerStore.getState().setProgress(el.currentTime, Number.isFinite(el.duration) ? el.duration : 0);
    if ("mediaSession" in navigator && Number.isFinite(el.duration) && el.duration > 0) {
      try { navigator.mediaSession.setPositionState({ duration: el.duration, position: Math.min(el.currentTime, el.duration), playbackRate: el.playbackRate }); } catch { /* ignore */ }
    }
  };

  const onLoadedMetadata = () => {
    const el = audioRef.current;
    const at = usePlayerStore.getState().resumeAt;
    if (el && at !== null) {
      el.currentTime = Math.max(0, Math.min(at, Math.max(0, (el.duration || at) - 0.5)));
      usePlayerStore.getState().clearResume();
    }
    onTime();
  };

  const onError = async () => {
    const el = audioRef.current;
    const s = usePlayerStore.getState();
    const current = currentSong(s);
    if (!el || !current || !loadedFor.current || el.src.startsWith("data:")) return;
    // the signed URL may have expired during a long pause: ask for a new one once and continue at the same second
    if (!retried.current) {
      retried.current = true;
      try { await load(current.id, false, el.currentTime || null); return; } catch { /* fall through */ }
    }
    s.setError("PLAYBACK_FAILED");
    usePlayerStore.setState({ playing: false });
    usePlayerStore.getState().setLoading(false);
  };

  const toggleFavorite = async () => {
    if (!song) return;
    const on = !song.favorite;
    usePlayerStore.getState().patchSong(song.id, { favorite: on });
    try {
      await setFavorite(song.id, on);
      void queryClient.invalidateQueries({ queryKey: ["medien-songs"] });
    } catch {
      usePlayerStore.getState().patchSong(song.id, { favorite: !on });
    }
  };

  return (
    <>
      <audio
        ref={audioRef}
        preload="none"
        data-testid="global-audio"
        onTimeUpdate={onTime}
        onDurationChange={onTime}
        onLoadedMetadata={onLoadedMetadata}
        onCanPlay={() => { switching.current = false; usePlayerStore.getState().setLoading(false); }}
        onPlaying={() => { switching.current = false; usePlayerStore.getState().setLoading(false); usePlayerStore.getState().setError(null); }}
        onPause={() => { const el = audioRef.current; if (el && !el.ended && !switching.current && usePlayerStore.getState().playing) usePlayerStore.setState({ playing: false }); }}
        onPlay={() => { if (!usePlayerStore.getState().playing && loadedFor.current) usePlayerStore.setState({ playing: true }); }}
        onEnded={() => usePlayerStore.getState().next(true)}
        onError={onError}
      />
      {song && (
        <div className="sticky bottom-0 z-40 border-t border-surface-border bg-surface-card/95 shadow-[0_-8px_30px_rgba(0,0,0,0.18)] backdrop-blur" data-testid="player-bar">
          {queueOpen && (
            <div className="absolute inset-x-0 bottom-full max-h-[50vh] overflow-y-auto border-t border-surface-border bg-surface-card p-3 sm:left-auto sm:right-4 sm:w-96 sm:rounded-t-2xl sm:border sm:border-b-0" data-testid="player-queue">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-sm font-bold text-text-primary">{t("medien.playerQueue")} · {queue.length}</p>
                <button className="text-xs font-semibold text-text-muted hover:text-danger" onClick={() => usePlayerStore.getState().clear()} data-testid="player-clear">{t("medien.playerClear")}</button>
              </div>
              <ul className="space-y-1">
                {queue.map((q, i) => (
                  <li key={`${q.id}-${i}`} className={cn("flex items-center gap-2 rounded-lg p-1.5", i === index ? "bg-accent-blue/10" : "hover:bg-surface-hover")}>
                    <button className="min-w-0 flex-1 text-left" onClick={() => usePlayerStore.getState().playIndex(i)} data-testid="player-queue-item">
                      <p className={cn("truncate text-sm font-semibold", i === index ? "text-accent-blue" : "text-text-primary")}>{q.title}</p>
                      <p className="truncate text-xs text-text-muted">{q.artist ?? ""}</p>
                    </button>
                    <button aria-label={t("medien.playerRemove")} className="rounded p-1 text-text-muted hover:text-danger" onClick={() => usePlayerStore.getState().removeFromQueue(i)}><X size={14} /></button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="mx-auto flex max-w-[1440px] flex-wrap items-center gap-x-4 gap-y-1 px-3 py-2 pr-20 sm:px-6 sm:pr-24 lg:flex-nowrap">
            <Link href="/medien/musik" className="flex min-w-0 flex-1 items-center gap-3 lg:w-72 lg:flex-none" aria-label={t("medien.music")}>
              <span className="relative h-11 w-11 shrink-0 overflow-hidden rounded-lg bg-gradient-to-br from-brand-600 to-accent-blue">
                {song.cover_url && <img src={mediaUrl(song.cover_url)} alt="" className="h-full w-full object-cover" />}
              </span>
              <span className="min-w-0">
                <span className="block truncate text-sm font-bold text-text-primary" data-testid="player-title">{song.title}</span>
                <span className="block truncate text-xs text-text-muted">{error ? t(`medien.err.${["PURCHASE_REQUIRED", "NOT_FOUND", "FILE_MISSING", "PLAYBACK_FAILED"].includes(error) ? error : "GENERIC"}`) : song.artist ?? ""}</span>
              </span>
            </Link>

            <div className="flex items-center gap-1 sm:gap-2" data-testid="player-controls">
              <IconBtn label={t("medien.playerShuffle")} active={shuffle} onClick={() => usePlayerStore.getState().toggleShuffle()} testId="player-shuffle" className="hidden sm:flex"><Shuffle size={16} /></IconBtn>
              <IconBtn label={t("medien.playerPrev")} onClick={() => usePlayerStore.getState().prev()} testId="player-prev"><SkipBack size={18} /></IconBtn>
              <button type="button" onClick={() => usePlayerStore.getState().toggle()} aria-label={playing ? t("medien.playerPause") : t("medien.playerPlay")} data-testid="player-play"
                      className="flex h-10 w-10 items-center justify-center rounded-full bg-accent-blue text-white shadow-md transition hover:opacity-90">
                {loading ? <Loader2 size={18} className="animate-spin" /> : playing ? <Pause size={18} /> : <Play size={18} className="translate-x-px" />}
              </button>
              <IconBtn label={t("medien.playerNext")} onClick={() => usePlayerStore.getState().next()} testId="player-next"><SkipForward size={18} /></IconBtn>
              <IconBtn label={t("medien.playerRepeat")} active={repeat !== "off"} onClick={() => usePlayerStore.getState().cycleRepeat()} testId="player-repeat" className="hidden sm:flex" data-mode={repeat}>
                {repeat === "one" ? <Repeat1 size={16} /> : <Repeat size={16} />}
              </IconBtn>
            </div>

            <div className="order-last flex w-full items-center gap-2 lg:order-none lg:w-auto lg:flex-1">
              <span className="w-9 text-right text-[11px] tabular-nums text-text-muted" data-testid="player-time">{formatTime(currentTime)}</span>
              <input type="range" min={0} max={Math.max(1, Math.floor(duration || (song.duration_ms ?? 0) / 1000))} step={1} value={Math.min(Math.floor(currentTime), Math.floor(duration || (song.duration_ms ?? 0) / 1000) || 0)}
                     onChange={(e) => usePlayerStore.getState().seek(Number(e.target.value))} aria-label={t("medien.playerSeek")} data-testid="player-progress" className="h-1.5 flex-1 cursor-pointer accent-[var(--color-accent-blue,#2563eb)]" />
              <span className="w-9 text-[11px] tabular-nums text-text-muted">{formatTime(duration || (song.duration_ms ?? 0) / 1000)}</span>
            </div>

            <div className="flex items-center gap-1">
              <IconBtn label={t("medien.playerFavorite")} active={song.favorite} onClick={toggleFavorite} testId="player-favorite"><Heart size={16} className={song.favorite ? "fill-current" : ""} /></IconBtn>
              <IconBtn label={muted || volume === 0 ? t("medien.playerUnmute") : t("medien.playerMute")} onClick={() => usePlayerStore.getState().toggleMute()} testId="player-mute">
                {muted || volume === 0 ? <VolumeX size={16} /> : <Volume2 size={16} />}
              </IconBtn>
              <input type="range" min={0} max={1} step={0.05} value={muted ? 0 : volume} onChange={(e) => usePlayerStore.getState().setVolume(Number(e.target.value))}
                     aria-label={t("medien.playerVolume")} data-testid="player-volume" className="hidden h-1.5 w-20 cursor-pointer accent-[var(--color-accent-blue,#2563eb)] md:block" />
              <IconBtn label={t("medien.playerQueue")} active={queueOpen} onClick={() => usePlayerStore.getState().toggleQueue()} testId="player-queue-toggle"><ListMusic size={16} /></IconBtn>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function IconBtn({ children, label, onClick, active, testId, className, ...rest }: { children: React.ReactNode; label: string; onClick: () => void; active?: boolean; testId: string; className?: string } & Record<string, unknown>) {
  return (
    <button type="button" aria-label={label} title={label} onClick={onClick} data-testid={testId} aria-pressed={active}
            className={cn("flex h-9 w-9 items-center justify-center rounded-full transition", active ? "bg-accent-blue/15 text-accent-blue" : "text-text-secondary hover:bg-surface-hover", className)} {...(rest as object)}>
      {children}
    </button>
  );
}
