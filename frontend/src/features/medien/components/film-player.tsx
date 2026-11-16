"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Captions, Gauge, Keyboard, Languages, Loader2, Maximize2, Minimize2, Pause, PictureInPicture2, Play, RotateCcw, RotateCw, SkipBack, SkipForward, Volume2, VolumeX, X } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import { useCueTracks } from "../hooks/use-film-subtitles";
import { clamp, initialSubtitle, normalizePrefs, pickSecondary, SPEEDS, sortByLanguage, stateOf, subtitleLines, type SubtitlePrefs } from "../lib/subtitles";
import { errorCode, mediaUrl, savePlayerPrefs, saveProgress, saveProgressKeepalive, watchFilm } from "../services/medien-service";
import type { VideoSource, WatchInfo, WatchSubtitle } from "../types";
import { formatTime } from "./global-audio-player";
import SubtitleMenu from "./subtitle-menu";
import SubtitleOverlay, { SUBTITLE_WORD_EVENT, type WordPick } from "./subtitle-overlay";
import WordPopup from "./word-popup";

export { SUBTITLE_WORD_EVENT };

const EMPTY_SUBS: WatchSubtitle[] = [];
const PAUSE_KEY = "vizu-film-pause-on-word";
const embedUrl = (url: string): string | null => {
  const yt = url.match(/^https:\/\/(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]{6,})/);
  if (yt) return `https://www.youtube-nocookie.com/embed/${yt[1]}`;
  const vimeo = url.match(/^https:\/\/(?:www\.)?vimeo\.com\/(\d+)/);
  return vimeo ? `https://player.vimeo.com/video/${vimeo[1]}` : null;
};

interface AudioTrackInfo { id: string; label: string; enabled: boolean }
interface AudioTrackLike { id?: string; label?: string; language?: string; enabled: boolean }
type Menu = "speed" | "subs" | "quality" | "audio" | null;

interface Props { filmId: string; title: string; onProgress?: () => void }

/** The film player of VIZU Medienwelt: our own controls (play, ±10 s, previous / next film, volume, speed, quality, audio track, subtitles,
 * Picture-in-Picture, fullscreen, keyboard shortcuts) around one <video> element with HTTP Range streaming. Subtitles are drawn by us from plain
 * cue lists (German / Uzbek / English / off, dual view, the student's look settings); German words open the dictionary popup. Position and the
 * choices of the film (subtitle, dual, speed, quality) are saved and restored. */
export default function FilmPlayer({ filmId, title, onProgress }: Props) {
  const { t } = useTranslation();
  const router = useRouter();
  const boxRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const hideTimer = useRef<number | null>(null);
  const last = useRef({ time: 0, duration: 0 });
  const resume = useRef<{ time: number; play: boolean } | null>(null);
  const initialSeek = useRef(false);
  const wasPlaying = useRef(false);
  const prefTimer = useRef<number | null>(null);
  const pendingPrefs = useRef<Partial<SubtitlePrefs>>({});

  const [info, setInfo] = useState<WatchInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const [time, setTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [buffering, setBuffering] = useState(true);
  const [volume, setVolume] = useState(1);
  const [muted, setMuted] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [prefs, setPrefs] = useState<SubtitlePrefs>(() => normalizePrefs(null));
  const [subtitle, setSubtitle] = useState<string>("off");
  const [dual, setDual] = useState(false);
  const [secondary, setSecondary] = useState<string | null>(null);
  const [sourceId, setSourceId] = useState("main");
  const [audioTracks, setAudioTracks] = useState<AudioTrackInfo[]>([]);
  const [menu, setMenu] = useState<Menu>(null);
  const [help, setHelp] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [pseudoFs, setPseudoFs] = useState(false);
  const [pip, setPip] = useState(false);
  const [controls, setControls] = useState(true);
  const barRef = useRef<HTMLDivElement>(null);
  const [barH, setBarH] = useState(0);
  const [pick, setPick] = useState<WordPick | null>(null);
  const [pauseOnWord, setPauseOnWordState] = useState(() => {
    try { return typeof window === "undefined" || localStorage.getItem(PAUSE_KEY) !== "0"; } catch { return true; } // storage blocked: the default (on)
  });

  const { tracks } = useCueTracks(info?.subtitles ?? EMPTY_SUBS);
  const available = useMemo(() => (info?.subtitles ?? EMPTY_SUBS).map((s) => s.language), [info]);
  const secondaryEff = pickSecondary(available, subtitle, secondary ?? undefined);
  const dualOn = dual && available.length > 1;
  const lines = useMemo(() => subtitleLines(available, subtitle, dualOn, secondary ?? undefined), [available, subtitle, dualOn, secondary]);
  const sources: VideoSource[] = useMemo(() => (info?.sources?.length ? info.sources : info ? [{ id: "main", label: "Original", height: null, url: info.source.url }] : []), [info]);
  const source = sources.find((s) => s.id === sourceId) ?? sources[0];
  const canPip = typeof document !== "undefined" && !!document.pictureInPictureEnabled;

  // what "continue watching" restores for this film
  const stateRef = useRef(stateOf({ subtitle, dual: dualOn, secondary: secondaryEff, speed, quality: source?.label ?? null }));
  useEffect(() => { stateRef.current = stateOf({ subtitle, dual: dualOn, secondary: secondaryEff, speed, quality: source?.label ?? null }); });


  useEffect(() => {
    let cancelled = false;
    watchFilm(filmId).then((w) => {
      if (cancelled) return;
      const p = normalizePrefs(w.prefs);
      const st = w.progress?.state ?? null;
      const langs = w.subtitles.map((s) => s.language);
      setPrefs(p);
      setSubtitle(initialSubtitle(langs, st, p));
      setDual(typeof st?.dual === "boolean" ? st.dual : p.dual);
      setSecondary(st?.secondary ?? p.secondary);
      if (st?.speed && SPEEDS.includes(st.speed)) setSpeed(st.speed);
      const wanted = st?.quality ? (w.sources ?? []).find((s) => s.label === st.quality) : null;
      setSourceId(wanted?.id ?? "main");
      setInfo({ ...w, subtitles: sortByLanguage(w.subtitles) });
    }).catch((err) => { if (!cancelled) setError(errorCode(err) ?? "GENERIC"); });
    return () => { cancelled = true; };
  }, [filmId]);

  /** Saves the position the video is at right now (the element when it still exists, else the last timeupdate) with the film's player state.
   * `final`: the page is going away (closed / reloaded / hidden) — a keepalive request that survives it. */
  const save = useCallback((final = false) => {
    const v = videoRef.current;
    const pos = v && Number.isFinite(v.currentTime) && v.currentTime > 0 ? v.currentTime : last.current.time;
    const total = (v && Number.isFinite(v.duration) ? v.duration : 0) || last.current.duration;
    if (!(pos > 0)) return;
    if (final) saveProgressKeepalive("FILM", filmId, pos, total || null, stateRef.current);
    else void saveProgress("FILM", filmId, pos, total || null, stateRef.current).then(() => onProgress?.()).catch(() => undefined);
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

  // the student's look settings are saved on the server (profile) a moment after the last change
  const flushPrefs = useCallback(() => {
    if (prefTimer.current) window.clearTimeout(prefTimer.current);
    prefTimer.current = null;
    const patch = pendingPrefs.current;
    pendingPrefs.current = {};
    if (Object.keys(patch).length) void savePlayerPrefs(patch).catch(() => undefined);
  }, []);
  useEffect(() => flushPrefs, [flushPrefs]);
  const updatePrefs = useCallback((patch: Partial<SubtitlePrefs>) => {
    setPrefs((p) => ({ ...p, ...patch }));
    pendingPrefs.current = { ...pendingPrefs.current, ...patch };
    if (prefTimer.current) window.clearTimeout(prefTimer.current);
    prefTimer.current = window.setTimeout(flushPrefs, 600);
  }, [flushPrefs]);

  useEffect(() => {
    const onChange = () => setFullscreen(document.fullscreenElement === boxRef.current);
    document.addEventListener("fullscreenchange", onChange);
    return () => document.removeEventListener("fullscreenchange", onChange);
  }, []);
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    const on = () => setPip(true);
    const off = () => setPip(false);
    v.addEventListener("enterpictureinpicture", on);
    v.addEventListener("leavepictureinpicture", off);
    return () => { v.removeEventListener("enterpictureinpicture", on); v.removeEventListener("leavepictureinpicture", off); };
  }, [info]);

  // the control bar's real height (one row on a desktop, two on a phone): the subtitles sit above it
  useEffect(() => {
    const el = barRef.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const measure = () => setBarH(Math.max(0, Math.round(el.getBoundingClientRect().height - parseFloat(getComputedStyle(el).paddingTop))));
    const observer = new ResizeObserver(measure);
    observer.observe(el);
    return () => observer.disconnect();
  }, [info]);

  const wake = () => {
    setControls(true);
    if (hideTimer.current) window.clearTimeout(hideTimer.current);
    hideTimer.current = window.setTimeout(() => { if (!videoRef.current?.paused) { setControls(false); setMenu(null); } }, 3000);
  };

  const toggle = () => { const v = videoRef.current; if (!v) return; if (v.paused) void v.play(); else v.pause(); };
  const seek = (s: number) => { const v = videoRef.current; if (v) v.currentTime = clamp(s, 0, v.duration || s); };
  const skip = (delta: number) => seek((videoRef.current?.currentTime ?? 0) + delta);
  const toggleFullscreen = () => {
    const box = boxRef.current;
    if (!box) return;
    if (document.fullscreenElement) { void document.exitFullscreen(); return; }
    if (pseudoFs) { setPseudoFs(false); return; }
    if (document.fullscreenEnabled && box.requestFullscreen) void box.requestFullscreen().catch(() => setPseudoFs(true));
    else setPseudoFs(true); // phones without element fullscreen: the player fills the screen itself
  };
  const togglePip = async () => {
    const v = videoRef.current;
    if (!v) return;
    try { if (document.pictureInPictureElement) await document.exitPictureInPicture(); else await v.requestPictureInPicture(); } catch { /* not allowed right now */ }
  };
  const go = (film: { id: string } | null | undefined) => { if (film) router.push(`/medien/filme/${film.id}`); };
  const nextFilm = info?.neighbors.next ?? null;
  const prevFilm = info?.neighbors.prev ?? null;

  const chooseSubtitle = (language: string) => { setSubtitle(language); setMenu(null); updatePrefs({ enabled: language !== "off" }); };
  const toggleSubtitles = () => chooseSubtitle(subtitle === "off" ? initialSubtitle(available, null, { ...prefs, enabled: true }) : "off");
  const changeDual = (on: boolean) => { setDual(on); updatePrefs({ dual: on }); };
  const changeSecondary = (language: string) => { setSecondary(language); updatePrefs({ secondary: language }); };
  const setPauseOnWord = (on: boolean) => { setPauseOnWordState(on); try { localStorage.setItem(PAUSE_KEY, on ? "1" : "0"); } catch { /* ignore */ } };
  const chooseSpeed = (s: number) => { setSpeed(s); setMenu(null); };
  const chooseQuality = (id: string) => {
    const v = videoRef.current;
    if (v && id !== sourceId) resume.current = { time: v.currentTime, play: !v.paused }; // the new file continues where the old one was
    setSourceId(id);
    setMenu(null);
  };
  const chooseAudio = (id: string) => {
    const list = (videoRef.current as unknown as { audioTracks?: ArrayLike<AudioTrackLike> } | null)?.audioTracks;
    if (!list) return;
    Array.from(list).forEach((tr, i) => { tr.enabled = (tr.id || String(i)) === id; });
    setAudioTracks((all) => all.map((a) => ({ ...a, enabled: a.id === id })));
    setMenu(null);
  };

  const pickWord = (p: WordPick) => {
    window.dispatchEvent(new CustomEvent(SUBTITLE_WORD_EVENT, { detail: { word: p.word, language: p.language, time: p.time, filmId } }));
    const v = videoRef.current;
    if (!pick) wasPlaying.current = !!v && !v.paused && pauseOnWord;
    if (pauseOnWord && v && !v.paused) v.pause();
    setPick(p);
  };
  const closePick = useCallback(() => {
    setPick(null);
    window.getSelection()?.removeAllRanges(); // a phrase selection must not swallow the next click on a word
    if (wasPlaying.current) { wasPlaying.current = false; void videoRef.current?.play(); }
  }, []);

  // keyboard shortcuts (the whole film page; not while typing in a field)
  const keyRef = useRef<(e: KeyboardEvent) => void>(() => undefined);
  useEffect(() => {
    keyRef.current = (e: KeyboardEvent) => {
      const el = e.target as HTMLElement | null;
      if (el && (["INPUT", "TEXTAREA", "SELECT"].includes(el.tagName) || el.isContentEditable)) return;
      if (e.ctrlKey || e.metaKey || e.altKey || !info) return;
      if ((e.key === " " || e.key === "Enter") && el?.closest("button, a, [role='button']")) return; // the focused control handles it itself
      const v = videoRef.current;
      const key = e.key;
      const idx = SPEEDS.indexOf(speed);
      const actions: Record<string, () => void> = {
        " ": toggle, k: toggle, K: toggle,
        ArrowRight: () => skip(5), ArrowLeft: () => skip(-5), l: () => skip(10), L: () => skip(10), j: () => skip(-10), J: () => skip(-10),
        ArrowUp: () => setVolume((x) => clamp(Math.round((x + 0.1) * 10) / 10, 0, 1)), ArrowDown: () => setVolume((x) => clamp(Math.round((x - 0.1) * 10) / 10, 0, 1)),
        m: () => setMuted((x) => !x), M: () => setMuted((x) => !x), f: toggleFullscreen, F: toggleFullscreen,
        c: toggleSubtitles, C: toggleSubtitles, d: () => { if (available.length > 1) changeDual(!dualOn); }, D: () => { if (available.length > 1) changeDual(!dualOn); },
        p: () => { void togglePip(); }, i: () => { void togglePip(); },
        "<": () => idx > 0 && chooseSpeed(SPEEDS[idx - 1]), ">": () => idx < SPEEDS.length - 1 && chooseSpeed(SPEEDS[idx + 1]),
        Home: () => seek(0), End: () => seek((v?.duration ?? 0) - 1),
        N: () => go(nextFilm), P: () => go(prevFilm),
        "?": () => setHelp((x) => !x), h: () => setHelp((x) => !x),
        Escape: () => { if (pick) closePick(); else if (menu) setMenu(null); else if (help) setHelp(false); else if (pseudoFs) setPseudoFs(false); },
      };
      if (/^[0-9]$/.test(key) && v?.duration) { e.preventDefault(); seek((Number(key) / 10) * v.duration); wake(); return; }
      const action = actions[key];
      if (!action) return;
      if (key === "Escape" && !pick && !menu && !help && !pseudoFs) return; // native fullscreen exit etc.
      e.preventDefault();
      action();
      wake();
    };
  });
  useEffect(() => {
    const handler = (e: KeyboardEvent) => keyRef.current(e);
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);

  if (error) {
    return <div role="alert" className="flex aspect-video items-center justify-center rounded-2xl bg-black px-4 text-center text-sm text-white" data-testid="film-error">{t(`medien.err.${["PURCHASE_REQUIRED", "NOT_FOUND", "FILE_MISSING"].includes(error) ? error : "GENERIC"}`)}</div>;
  }
  if (!info) return <div className="flex aspect-video items-center justify-center rounded-2xl bg-black text-white"><Loader2 className="animate-spin" /></div>;

  if (info.source.type === "external") {
    const embed = embedUrl(info.source.url);
    if (embed) return <iframe src={embed} title={title} allow="fullscreen; picture-in-picture; encrypted-media" allowFullScreen className="aspect-video w-full rounded-2xl bg-black" data-testid="film-embed" />;
  }

  const full = fullscreen || pseudoFs;
  const subLines = lines.map((language) => ({ language, cues: tracks[language] }));
  const shown = controls || !playing || !!menu;
  return (
    <div ref={boxRef} tabIndex={0} onMouseMove={wake} onTouchStart={wake} data-testid="film-player" data-playing={playing ? "1" : "0"} data-fullscreen={full ? "1" : "0"}
         className={cn("group relative w-full overflow-hidden bg-black outline-none", pseudoFs ? "fixed inset-0 z-[90] h-[100dvh] w-screen" : "aspect-video", full ? "" : "rounded-2xl shadow-[var(--shadow-md)]")}>
      <video ref={videoRef} src={mediaUrl(source.url)} playsInline preload="metadata" data-testid="film-video" data-source={source.id} className="h-full w-full bg-black"
             onClick={() => { if (pick) closePick(); else if (menu) setMenu(null); else toggle(); }}
             onPlay={() => { setPlaying(true); wake(); }} onPause={() => { setPlaying(false); setControls(true); save(); }}
             onEnded={() => { setPlaying(false); const v = videoRef.current; if (v) { last.current = { time: v.duration, duration: v.duration }; save(); } }}
             onWaiting={() => setBuffering(true)} onCanPlay={() => setBuffering(false)} onPlaying={() => setBuffering(false)}
             onLoadedMetadata={() => {
               const v = videoRef.current!;
               setDuration(v.duration);
               v.playbackRate = speed; // a new source starts at 1x
               const tracksList = (v as unknown as { audioTracks?: ArrayLike<AudioTrackLike> }).audioTracks;
               if (tracksList && tracksList.length > 1) {
                 setAudioTracks(Array.from(tracksList).map((tr, i) => ({ id: tr.id || String(i), label: tr.label || tr.language || t("medien.fp.audioTrack", { n: i + 1 }), enabled: tr.enabled })));
               } else setAudioTracks([]);
               const r = resume.current;
               if (r) { resume.current = null; v.currentTime = Math.min(r.time, v.duration || r.time); if (r.play) void v.play(); return; }
               if (initialSeek.current) return;
               initialSeek.current = true;
               const at = info.progress && !info.progress.completed ? info.progress.position : 0;
               if (at >= 3 && at < v.duration - 5) v.currentTime = at; // positions are whole seconds; not within the first 3 s or the last 5 s
             }}
             onTimeUpdate={() => { const v = videoRef.current!; setTime(v.currentTime); last.current = { time: v.currentTime, duration: v.duration || 0 }; }}
             onVolumeChange={() => { const v = videoRef.current!; setVolume(v.volume); setMuted(v.muted); }} />
      <VolumeSync videoRef={videoRef} volume={volume} muted={muted} speed={speed} />

      {buffering && <div className="pointer-events-none absolute inset-0 flex items-center justify-center"><Loader2 className="animate-spin text-white/80" size={36} /></div>}
      {!playing && !buffering && !pick && (
        <button type="button" onClick={toggle} aria-label={t("medien.playerPlay")} className="absolute left-1/2 top-1/2 flex h-16 w-16 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-accent-blue/90 text-white shadow-xl"><Play size={28} className="translate-x-0.5" /></button>
      )}

      <SubtitleOverlay videoRef={videoRef} lines={subLines} prefs={prefs} barHeight={shown ? barH : 0} activeWord={pick && !pick.phrase ? pick.word : null} onPick={pickWord} />
      {pick && <WordPopup key={`${pick.word}-${pick.time}`} pick={pick} onClose={closePick} />}

      {help && (
        <div className="absolute inset-0 z-30 flex items-center justify-center bg-black/85 p-4 text-white" data-testid="film-shortcuts" onClick={() => setHelp(false)}>
          <div className="max-h-full w-full max-w-md overflow-y-auto rounded-2xl bg-black/60 p-4 ring-1 ring-white/15" onClick={(e) => e.stopPropagation()}>
            <div className="mb-3 flex items-center justify-between"><h3 className="font-bold">{t("medien.fp.shortcuts")}</h3><button type="button" aria-label={t("medien.wp.close")} onClick={() => setHelp(false)} className="flex h-9 w-9 items-center justify-center rounded-lg hover:bg-white/15"><X size={18} /></button></div>
            <dl className="grid grid-cols-[auto,1fr] gap-x-4 gap-y-1.5 text-sm">
              {([["Space / K", "play"], ["← →", "seek5"], ["J / L", "seek10"], ["↑ ↓", "volume"], ["M", "mute"], ["F", "fullscreen"], ["C", "subtitles"], ["D", "dual"], ["P", "pip"], ["< >", "speed"], ["0–9", "percent"], ["Shift+N / Shift+P", "film"], ["?", "help"]] as const)
                .map(([k, id]) => <div key={id} className="contents"><dt><kbd className="rounded bg-white/15 px-1.5 py-0.5 font-mono text-xs">{k}</kbd></dt><dd className="text-white/85">{t(`medien.fp.sc.${id}`)}</dd></div>)}
            </dl>
          </div>
        </div>
      )}

      <div ref={barRef} className={cn("absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/85 to-transparent px-2 pb-1.5 pt-10 text-white transition-opacity sm:px-3 sm:pb-2", shown ? "pointer-events-none opacity-100 [&>*]:pointer-events-auto" : "pointer-events-none opacity-0")} data-testid="film-controls">
        <input type="range" min={0} max={Math.max(1, Math.floor(duration))} step={1} value={Math.floor(time)} onChange={(e) => seek(Number(e.target.value))} aria-label={t("medien.playerSeek")} data-testid="film-progress" className="mb-1 h-2 w-full cursor-pointer accent-[var(--color-accent-blue,#2563eb)]" />
        <div className="flex flex-wrap items-center justify-between gap-x-1 gap-y-0.5">
          <div className="flex items-center gap-0.5 sm:gap-1">
            <Ctl label={t("medien.fp.prevFilm")} onClick={() => go(prevFilm)} testId="film-prev" disabled={!prevFilm}><SkipBack size={18} /></Ctl>
            <Ctl label={t("medien.fp.back10")} onClick={() => skip(-10)} testId="film-back10"><RotateCcw size={17} /></Ctl>
            <Ctl label={playing ? t("medien.playerPause") : t("medien.playerPlay")} onClick={toggle} testId="film-play">{playing ? <Pause size={20} /> : <Play size={20} />}</Ctl>
            <Ctl label={t("medien.fp.fwd10")} onClick={() => skip(10)} testId="film-fwd10"><RotateCw size={17} /></Ctl>
            <Ctl label={t("medien.fp.nextFilm")} onClick={() => go(nextFilm)} testId="film-next" disabled={!nextFilm}><SkipForward size={18} /></Ctl>
            <Ctl label={muted || volume === 0 ? t("medien.playerUnmute") : t("medien.playerMute")} onClick={() => setMuted((m) => !m)} testId="film-mute">{muted || volume === 0 ? <VolumeX size={18} /> : <Volume2 size={18} />}</Ctl>
            <input type="range" min={0} max={1} step={0.05} value={muted ? 0 : volume} onChange={(e) => { setVolume(Number(e.target.value)); setMuted(false); }} aria-label={t("medien.playerVolume")} data-testid="film-volume" className="hidden h-1 w-20 cursor-pointer accent-[var(--color-accent-blue,#2563eb)] sm:block" />
            <span className="ml-1 text-[11px] tabular-nums sm:text-xs" data-testid="film-time">{formatTime(time)} / {formatTime(duration)}</span>
          </div>
          <div className="flex items-center gap-0.5 sm:gap-1">
            <Ctl label={t("medien.speed")} onClick={() => setMenu(menu === "speed" ? null : "speed")} testId="film-speed" wide expanded={menu === "speed"}>{speed}×</Ctl>
            <Ctl label={t("medien.subtitles")} onClick={() => setMenu(menu === "subs" ? null : "subs")} testId="film-subtitles" active={subtitle !== "off"} expanded={menu === "subs"}><Captions size={19} /></Ctl>
            {sources.length > 1 && (
              <Ctl label={t("medien.fp.quality")} onClick={() => setMenu(menu === "quality" ? null : "quality")} testId="film-quality" wide expanded={menu === "quality"}><Gauge size={17} className="mr-1" /><span className="hidden text-xs sm:inline">{source.label === "Original" ? t("medien.fp.qualityOriginal") : source.label}</span></Ctl>
            )}
            {audioTracks.length > 1 && (
              <Ctl label={t("medien.fp.audio")} onClick={() => setMenu(menu === "audio" ? null : "audio")} testId="film-audio" expanded={menu === "audio"}><Languages size={18} /></Ctl>
            )}
            {canPip && <Ctl label={t("medien.fp.pip")} onClick={() => void togglePip()} testId="film-pip" active={pip}><PictureInPicture2 size={18} /></Ctl>}
            <Ctl label={t("medien.fp.shortcuts")} onClick={() => setHelp((x) => !x)} testId="film-help" active={help} hideOnPhone><Keyboard size={18} /></Ctl>
            <Ctl label={t("medien.readerFullscreen")} onClick={toggleFullscreen} testId="film-fullscreen">{full ? <Minimize2 size={18} /> : <Maximize2 size={18} />}</Ctl>
          </div>
        </div>
      </div>

      {menu === "speed" && (
        <MenuSheet testId="film-speed-menu" width="sm:w-28" label={t("medien.wp.close")} onClose={() => setMenu(null)}>
          <ul>{SPEEDS.map((s) => <li key={s}><button className={cn("block min-h-[44px] w-full rounded-lg px-3 py-1.5 text-left hover:bg-white/15 sm:min-h-9", s === speed && "font-bold text-accent-blue")} onClick={() => chooseSpeed(s)} data-testid="film-speed-option">{s}×</button></li>)}</ul>
        </MenuSheet>
      )}
      {menu === "subs" && (
        <MenuSheet testId="film-subtitle-menu" width="sm:w-[19rem]" label={t("medien.wp.close")} onClose={() => setMenu(null)}>
          <SubtitleMenu subtitles={info.subtitles} subtitle={subtitle} dual={dualOn} secondary={secondaryEff} prefs={prefs} pauseOnWord={pauseOnWord}
                        onSubtitle={chooseSubtitle} onDual={changeDual} onSecondary={changeSecondary} onPrefs={updatePrefs} onPauseOnWord={setPauseOnWord} />
        </MenuSheet>
      )}
      {menu === "quality" && (
        <MenuSheet testId="film-quality-menu" width="sm:w-36" label={t("medien.wp.close")} onClose={() => setMenu(null)}>
          <ul>{sources.map((s) => <li key={s.id}><button className={cn("block min-h-[44px] w-full rounded-lg px-3 py-1.5 text-left hover:bg-white/15 sm:min-h-9", s.id === source.id && "font-bold text-accent-blue")} onClick={() => chooseQuality(s.id)} data-testid="film-quality-option" data-source={s.id}>{s.label === "Original" ? t("medien.fp.qualityOriginal") : s.label}</button></li>)}</ul>
        </MenuSheet>
      )}
      {menu === "audio" && (
        <MenuSheet testId="film-audio-menu" width="sm:w-48" label={t("medien.wp.close")} onClose={() => setMenu(null)}>
          <ul>{audioTracks.map((a) => <li key={a.id}><button className={cn("block min-h-[44px] w-full rounded-lg px-3 py-1.5 text-left hover:bg-white/15 sm:min-h-9", a.enabled && "font-bold text-accent-blue")} onClick={() => chooseAudio(a.id)} data-testid="film-audio-option">{a.label}</button></li>)}</ul>
        </MenuSheet>
      )}
    </div>
  );
}

/** A menu of the player: on a desktop a panel at the right above the control bar, on a phone the whole player area (a menu above a 230 px
 * high picture would be cut off) with its own close button and scrolling. */
function MenuSheet({ children, width, testId, label, onClose }: { children: React.ReactNode; width: string; testId: string; label: string; onClose: () => void }) {
  return (
    <div className={cn("absolute z-40 overflow-y-auto rounded-xl bg-black/92 p-1 text-sm text-white ring-1 ring-white/10 backdrop-blur max-sm:inset-2 sm:bottom-[4.75rem] sm:right-3 sm:max-h-[min(60vh,24rem)]", width)}
         data-testid={testId} onClick={(e) => e.stopPropagation()}>
      <button type="button" aria-label={label} onClick={onClose} data-testid="film-menu-close" className="sticky top-0 z-10 ml-auto flex h-[44px] w-[44px] items-center justify-center rounded-lg bg-black/70 hover:bg-white/15 sm:hidden"><X size={18} /></button>
      {children}
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

function Ctl({ children, label, onClick, testId, active, wide, disabled, expanded, hideOnPhone }: {
  children: React.ReactNode; label: string; onClick: () => void; testId: string; active?: boolean; wide?: boolean; disabled?: boolean; expanded?: boolean; hideOnPhone?: boolean;
}) {
  return (
    <button type="button" aria-label={label} title={label} onClick={onClick} data-testid={testId} aria-pressed={active} aria-expanded={expanded} disabled={disabled}
            className={cn("flex h-[44px] items-center justify-center rounded-lg text-sm font-semibold transition hover:bg-white/15 disabled:cursor-not-allowed disabled:opacity-35 disabled:hover:bg-transparent sm:h-9",
                          wide ? "min-w-[44px] px-2" : "w-[40px] sm:w-9", hideOnPhone && "hidden sm:flex", active && "text-accent-blue")}>{children}</button>
  );
}
