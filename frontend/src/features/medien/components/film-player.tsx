"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Captions, Loader2, Maximize2, Minimize2, Pause, Play, Volume2, VolumeX } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import { errorCode, mediaUrl, saveProgress, saveProgressKeepalive, watchFilm } from "../services/medien-service";
import type { WatchInfo } from "../types";
import { formatTime } from "./global-audio-player";

const SPEEDS = [0.5, 0.75, 1, 1.25, 1.5, 2];
const embedUrl = (url: string): string | null => {
  const yt = url.match(/^https:\/\/(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]{6,})/);
  if (yt) return `https://www.youtube-nocookie.com/embed/${yt[1]}`;
  const vimeo = url.match(/^https:\/\/(?:www\.)?vimeo\.com\/(\d+)/);
  return vimeo ? `https://player.vimeo.com/video/${vimeo[1]}` : null;
};

/** Fired when the student clicks a word of the subtitle. The dictionary (Wörterbuch) can listen to it later — the player
 * already delivers the word, the language of the subtitle and the film second. Nothing else depends on it. */
export const SUBTITLE_WORD_EVENT = "medien:subtitle-word";

interface Props { filmId: string; title: string; onProgress?: () => void }

export default function FilmPlayer({ filmId, title, onProgress }: Props) {
  const { t } = useTranslation();
  const boxRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const hideTimer = useRef<number | null>(null);
  const last = useRef({ time: 0, duration: 0 });
  const [info, setInfo] = useState<WatchInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const [time, setTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [buffering, setBuffering] = useState(true);
  const [volume, setVolume] = useState(1);
  const [muted, setMuted] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [subtitle, setSubtitle] = useState<string>("off");
  const [cue, setCue] = useState("");
  const [menu, setMenu] = useState<"speed" | "subs" | null>(null);
  const [fullscreen, setFullscreen] = useState(false);
  const [controls, setControls] = useState(true);

  useEffect(() => {
    let cancelled = false;
    watchFilm(filmId).then((w) => {
      if (cancelled) return;
      setInfo(w);
      const de = w.subtitles.find((s) => s.language === "de");
      if (de) setSubtitle("de"); // German subtitles on by default when the film has them
    }).catch((err) => { if (!cancelled) setError(errorCode(err) ?? "GENERIC"); });
    return () => { cancelled = true; };
  }, [filmId]);

  /** Saves the position the video is at right now (the element when it still exists, else the last timeupdate). `final`:
   * the page is going away (closed / reloaded / hidden) — a keepalive request that survives it. */
  const save = useCallback((final = false) => {
    const v = videoRef.current;
    const pos = v && Number.isFinite(v.currentTime) && v.currentTime > 0 ? v.currentTime : last.current.time;
    const total = (v && Number.isFinite(v.duration) ? v.duration : 0) || last.current.duration;
    if (!(pos > 0)) return;
    if (final) saveProgressKeepalive("FILM", filmId, pos, total || null);
    else void saveProgress("FILM", filmId, pos, total || null).then(() => onProgress?.()).catch(() => undefined);
  }, [filmId, onProgress]);

  // save every 10 s while watching, on pause, when the tab is hidden or the page is left, and when the player closes
  useEffect(() => {
    const id = window.setInterval(() => { if (videoRef.current && !videoRef.current.paused) save(); }, 10_000);
    const hidden = () => { if (document.visibilityState === "hidden") save(true); };
    const leave = () => save(true);
    document.addEventListener("visibilitychange", hidden);
    window.addEventListener("pagehide", leave);
    return () => { window.clearInterval(id); document.removeEventListener("visibilitychange", hidden); window.removeEventListener("pagehide", leave); save(); };
  }, [save]);

  // subtitle track -> overlay text (the native track stays hidden; the overlay is ours so every word is clickable)
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !info) return;
    const tracks = Array.from(video.textTracks);
    tracks.forEach((tr) => { tr.mode = "disabled"; });
    setCue("");
    if (subtitle === "off") return;
    const track = tracks.find((tr) => tr.language === subtitle);
    if (!track) return;
    track.mode = "hidden";
    const update = () => setCue(Array.from(track.activeCues ?? []).map((c) => (c as VTTCue).text.replace(/<[^>]+>/g, "")).join("\n"));
    track.addEventListener("cuechange", update);
    update();
    return () => track.removeEventListener("cuechange", update);
  }, [subtitle, info]);

  useEffect(() => {
    const onChange = () => setFullscreen(document.fullscreenElement === boxRef.current);
    document.addEventListener("fullscreenchange", onChange);
    return () => document.removeEventListener("fullscreenchange", onChange);
  }, []);

  const wake = () => {
    setControls(true);
    if (hideTimer.current) window.clearTimeout(hideTimer.current);
    hideTimer.current = window.setTimeout(() => { if (!videoRef.current?.paused) { setControls(false); setMenu(null); } }, 3000);
  };

  const toggle = () => { const v = videoRef.current; if (!v) return; if (v.paused) void v.play(); else v.pause(); };
  const seek = (s: number) => { const v = videoRef.current; if (v) v.currentTime = Math.min(Math.max(0, s), v.duration || s); };
  const toggleFullscreen = () => { if (document.fullscreenElement) void document.exitFullscreen(); else void boxRef.current?.requestFullscreen?.(); };

  const onKey = (e: React.KeyboardEvent) => {
    if ((e.target as HTMLElement).tagName === "INPUT") return;
    const keys: Record<string, () => void> = {
      " ": toggle, k: toggle, ArrowRight: () => seek((videoRef.current?.currentTime ?? 0) + 10), ArrowLeft: () => seek((videoRef.current?.currentTime ?? 0) - 10),
      ArrowUp: () => setVolume((v) => Math.min(1, v + 0.1)), ArrowDown: () => setVolume((v) => Math.max(0, v - 0.1)), m: () => setMuted((m) => !m), f: toggleFullscreen,
    };
    if (keys[e.key]) { e.preventDefault(); keys[e.key](); wake(); }
  };

  if (error) {
    return <div role="alert" className="flex aspect-video items-center justify-center rounded-2xl bg-black px-4 text-center text-sm text-white" data-testid="film-error">{t(`medien.err.${["PURCHASE_REQUIRED", "NOT_FOUND", "FILE_MISSING"].includes(error) ? error : "GENERIC"}`)}</div>;
  }
  if (!info) return <div className="flex aspect-video items-center justify-center rounded-2xl bg-black text-white"><Loader2 className="animate-spin" /></div>;

  if (info.source.type === "external") {
    const embed = embedUrl(info.source.url);
    if (embed) return <iframe src={embed} title={title} allow="fullscreen; picture-in-picture; encrypted-media" allowFullScreen className="aspect-video w-full rounded-2xl bg-black" data-testid="film-embed" />;
  }

  const words = cue.split("\n");
  return (
    <div ref={boxRef} tabIndex={0} onKeyDown={onKey} onMouseMove={wake} onTouchStart={wake} data-testid="film-player" data-playing={playing ? "1" : "0"}
         className={cn("group relative aspect-video w-full overflow-hidden bg-black outline-none", fullscreen ? "" : "rounded-2xl shadow-[var(--shadow-md)]")}>
      <video ref={videoRef} src={info.source.type === "file" ? mediaUrl(info.source.url) : info.source.url} crossOrigin="anonymous" playsInline preload="metadata" data-testid="film-video"
             className="h-full w-full bg-black" onClick={toggle}
             onPlay={() => { setPlaying(true); wake(); }} onPause={() => { setPlaying(false); setControls(true); save(); }}
             onEnded={() => { setPlaying(false); const v = videoRef.current; if (v) { last.current = { time: v.duration, duration: v.duration }; save(); } }}
             onWaiting={() => setBuffering(true)} onCanPlay={() => setBuffering(false)} onPlaying={() => setBuffering(false)}
             onLoadedMetadata={() => {
               const v = videoRef.current!;
               setDuration(v.duration);
               const at = info.progress && !info.progress.completed ? info.progress.position : 0;
               if (at >= 3 && at < v.duration - 5) v.currentTime = at; // positions are whole seconds; not within the first 3 s or the last 5 s
             }}
             onTimeUpdate={() => { const v = videoRef.current!; setTime(v.currentTime); last.current = { time: v.currentTime, duration: v.duration || 0 }; }}
             onVolumeChange={() => { const v = videoRef.current!; setVolume(v.volume); setMuted(v.muted); }}>
        {info.subtitles.map((s) => <track key={s.id} kind="subtitles" srcLang={s.language} label={s.label} src={mediaUrl(s.url)} />)}
      </video>
      <VolumeSync videoRef={videoRef} volume={volume} muted={muted} speed={speed} />

      {buffering && <div className="pointer-events-none absolute inset-0 flex items-center justify-center"><Loader2 className="animate-spin text-white/80" size={36} /></div>}
      {!playing && !buffering && (
        <button type="button" onClick={toggle} aria-label={t("medien.playerPlay")} className="absolute left-1/2 top-1/2 flex h-16 w-16 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-accent-blue/90 text-white shadow-xl"><Play size={28} className="translate-x-0.5" /></button>
      )}

      {cue && (
        <div className={cn("pointer-events-none absolute inset-x-0 flex justify-center px-4 transition-all", controls ? "bottom-20" : "bottom-6")} data-testid="film-cue" data-language={subtitle}>
          <p className="max-w-3xl rounded-lg bg-black/75 px-3 py-1.5 text-center text-base font-medium leading-snug text-white sm:text-xl">
            {words.map((line, li) => (
              <span key={li} className="block">
                {line.split(/(\s+)/).map((w, wi) => /\S/.test(w)
                  ? <span key={wi} role="button" tabIndex={-1} data-word={w.replace(/[^\p{L}\p{N}'’-]/gu, "")} className="pointer-events-auto cursor-pointer rounded px-px hover:bg-white/20"
                          onClick={(e) => { e.stopPropagation(); window.dispatchEvent(new CustomEvent(SUBTITLE_WORD_EVENT, { detail: { word: w.replace(/[^\p{L}\p{N}'’-]/gu, ""), language: subtitle, time: videoRef.current?.currentTime ?? 0, filmId } })); }}>{w}</span>
                  : <span key={wi}>{w}</span>)}
              </span>
            ))}
          </p>
        </div>
      )}

      <div className={cn("absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/85 to-transparent px-3 pb-2 pt-10 text-white transition-opacity", controls ? "opacity-100" : "pointer-events-none opacity-0")} data-testid="film-controls">
        <input type="range" min={0} max={Math.max(1, Math.floor(duration))} step={1} value={Math.floor(time)} onChange={(e) => seek(Number(e.target.value))} aria-label={t("medien.playerSeek")} data-testid="film-progress" className="mb-1 h-1.5 w-full cursor-pointer accent-[var(--color-accent-blue,#2563eb)]" />
        <div className="flex items-center gap-1 sm:gap-2">
          <Ctl label={playing ? t("medien.playerPause") : t("medien.playerPlay")} onClick={toggle} testId="film-play">{playing ? <Pause size={20} /> : <Play size={20} />}</Ctl>
          <Ctl label={muted || volume === 0 ? t("medien.playerUnmute") : t("medien.playerMute")} onClick={() => setMuted((m) => !m)} testId="film-mute">{muted || volume === 0 ? <VolumeX size={18} /> : <Volume2 size={18} />}</Ctl>
          <input type="range" min={0} max={1} step={0.05} value={muted ? 0 : volume} onChange={(e) => { setVolume(Number(e.target.value)); setMuted(false); }} aria-label={t("medien.playerVolume")} data-testid="film-volume" className="hidden h-1 w-20 cursor-pointer accent-[var(--color-accent-blue,#2563eb)] sm:block" />
          <span className="ml-1 text-xs tabular-nums" data-testid="film-time">{formatTime(time)} / {formatTime(duration)}</span>
          <span className="flex-1" />
          <div className="relative">
            <Ctl label={t("medien.speed")} onClick={() => setMenu(menu === "speed" ? null : "speed")} testId="film-speed" wide>{speed}×</Ctl>
            {menu === "speed" && (
              <ul className="absolute bottom-full right-0 mb-2 w-24 rounded-xl bg-black/90 p-1 text-sm ring-1 ring-white/10" data-testid="film-speed-menu">
                {SPEEDS.map((s) => <li key={s}><button className={cn("block w-full rounded-lg px-3 py-1.5 text-left hover:bg-white/15", s === speed && "font-bold text-accent-blue")} onClick={() => { setSpeed(s); setMenu(null); }} data-testid="film-speed-option">{s}×</button></li>)}
              </ul>
            )}
          </div>
          <div className="relative">
            <Ctl label={t("medien.subtitles")} onClick={() => setMenu(menu === "subs" ? null : "subs")} testId="film-subtitles" active={subtitle !== "off"}><Captions size={19} /></Ctl>
            {menu === "subs" && (
              <ul className="absolute bottom-full right-0 mb-2 w-44 rounded-xl bg-black/90 p-1 text-sm ring-1 ring-white/10" data-testid="film-subtitle-menu">
                <li><button className={cn("block w-full rounded-lg px-3 py-1.5 text-left hover:bg-white/15", subtitle === "off" && "font-bold text-accent-blue")} onClick={() => { setSubtitle("off"); setMenu(null); }} data-testid="film-subtitle-off">{t("medien.subtitlesOff")}</button></li>
                {info.subtitles.map((s) => <li key={s.id}><button className={cn("block w-full rounded-lg px-3 py-1.5 text-left hover:bg-white/15", subtitle === s.language && "font-bold text-accent-blue")} onClick={() => { setSubtitle(s.language); setMenu(null); }} data-testid="film-subtitle-option" data-language={s.language}>{s.label}</button></li>)}
                {!info.subtitles.length && <li className="px-3 py-1.5 text-xs text-white/60">{t("medien.noSubtitles")}</li>}
              </ul>
            )}
          </div>
          <Ctl label={t("medien.readerFullscreen")} onClick={toggleFullscreen} testId="film-fullscreen">{fullscreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}</Ctl>
        </div>
      </div>
    </div>
  );
}

/** Applies volume / mute / speed to the element (kept out of the element's own event handlers to avoid feedback loops). */
function VolumeSync({ videoRef, volume, muted, speed }: { videoRef: React.RefObject<HTMLVideoElement | null>; volume: number; muted: boolean; speed: number }) {
  useEffect(() => {
    const v = videoRef.current;
    if (v) { v.volume = volume; v.muted = muted; v.playbackRate = speed; }
  }, [videoRef, volume, muted, speed]);
  return null;
}

function Ctl({ children, label, onClick, testId, active, wide }: { children: React.ReactNode; label: string; onClick: () => void; testId: string; active?: boolean; wide?: boolean }) {
  return (
    <button type="button" aria-label={label} title={label} onClick={onClick} data-testid={testId} aria-pressed={active}
            className={cn("flex h-9 items-center justify-center rounded-lg text-sm font-semibold transition hover:bg-white/15", wide ? "min-w-[3rem] px-2" : "w-9", active && "text-accent-blue")}>{children}</button>
  );
}
