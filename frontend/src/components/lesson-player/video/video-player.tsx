"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertTriangle,
  Check,
  Loader2,
  Maximize,
  Minimize,
  Pause,
  Play,
  RotateCcw,
  RotateCw,
  Settings,
  Volume2,
  VolumeX,
} from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

/** How often (ms) we report the current position to the server while
 *  playing. Free seeking is intentional: the player has no seek
 *  restrictions of any kind, and the server accepts whatever position is
 *  reported (bounded only to the video's real duration) — see
 *  VideoProgressService.update_progress. */
const PROGRESS_REPORT_INTERVAL_MS = 5000;
const SKIP_SECONDS = 15;
const SPEED_OPTIONS = [0.75, 1, 1.25, 1.5, 2];
const CONTROLS_HIDE_DELAY_MS = 3000;

interface Props {
  /** A playback URL, access-gated server-side. This component has no
   *  knowledge of where the file actually lives; it only ever receives
   *  a URL it can hand to <video>. */
  src: string;
  poster?: string;
  /** When provided, the lesson's "video" section is marked complete via
   *  the existing lesson-progress store once playback reaches the end —
   *  the same mechanism QuizSection/WritingSection already use. Purely
   *  local nav-checkmark UX; the real completion state lives server-side. */
  lessonId?: string;
  /** Where to resume playback from (seconds), e.g. after a previous
   *  session — 0 for a fresh start. */
  initialPosition?: number;
  /** Called (throttled while playing, plus once after any seek and once
   *  more with `ended: true` when playback finishes) with the current
   *  playback position. The caller decides completion eligibility. */
  onProgress?: (position: number, ended: boolean) => void;
  /** Shown as a semi-transparent overlay burned into the player chrome
   *  (not the video itself) — e.g. "VIZU Academy · Jane D. · a1b2c3d4".
   *  Doesn't stop screen recording (nothing client-side can), but ties
   *  any recording that does get made back to the account it came from,
   *  which is the practical deterrent available without real DRM. Only
   *  rendered when provided, so a logged-out/loading state just omits it
   *  rather than showing a broken watermark. */
  watermarkText?: string;
  /** Re-requests a freshly-signed stream URL (e.g. the embedded token
   *  expired) — called when the user hits "retry" after a load/stream
   *  error. The new `src` prop this produces re-initializes the player. */
  onRetryLoad?: () => void;
}

function formatTime(totalSeconds: number): string {
  if (!Number.isFinite(totalSeconds) || totalSeconds < 0) return "0:00";
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = Math.floor(totalSeconds % 60);
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}

/** Keyboard shortcuts (Space/←/→/M/F) only act when the event originates
 *  from the player surface itself, not from a focused interactive
 *  control (button, the seek/volume range inputs) — those already have
 *  their own native keyboard behavior, and this avoids double-handling
 *  or hijacking a control's own key response. */
function isPlayerSurfaceTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  return !["BUTTON", "INPUT", "SELECT", "TEXTAREA"].includes(target.tagName);
}

export default function VideoPlayer({
  src,
  poster,
  lessonId,
  initialPosition = 0,
  onProgress,
  watermarkText,
  onRetryLoad,
}: Props) {
  const { t } = useTranslation();
  const containerRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const settingsRef = useRef<HTMLDivElement>(null);
  const hideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const restoredPositionRef = useRef(false);
  const onProgressRef = useRef(onProgress);

  const [buffering, setBuffering] = useState(true);
  const [error, setError] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [ended, setEnded] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [muted, setMuted] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [fullscreen, setFullscreen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [controlsVisible, setControlsVisible] = useState(true);
  const [isDragging, setIsDragging] = useState(false);
  const [dragValue, setDragValue] = useState(0);

  useEffect(() => {
    onProgressRef.current = onProgress;
  }, [onProgress]);

  // Reset per-video state whenever the source actually changes (a fresh
  // lesson, or a retry that produced a newly-signed stream URL).
  useEffect(() => {
    setBuffering(true);
    setError(false);
    setRetrying(false);
    setPlaying(false);
    setEnded(false);
    setCurrentTime(0);
    setDuration(0);
    restoredPositionRef.current = false;
  }, [src]);

  // Periodic progress reporting while playing — reads the live DOM
  // position directly rather than React state, so it's never stale.
  useEffect(() => {
    const interval = setInterval(() => {
      const video = videoRef.current;
      if (video && !video.paused && !video.ended) {
        onProgressRef.current?.(Math.floor(video.currentTime), false);
      }
    }, PROGRESS_REPORT_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [src]);

  // Fullscreen state is tracked via the document-level event, since the
  // browser (Esc key, etc.) can exit fullscreen without going through
  // our own toggle handler.
  useEffect(() => {
    function handleFullscreenChange() {
      setFullscreen(document.fullscreenElement === containerRef.current);
    }
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", handleFullscreenChange);
  }, []);

  useEffect(() => {
    if (!settingsOpen) return;
    function handleClickOutside(event: MouseEvent) {
      if (settingsRef.current && !settingsRef.current.contains(event.target as Node)) {
        setSettingsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [settingsOpen]);

  useEffect(() => {
    return () => {
      if (hideTimerRef.current) clearTimeout(hideTimerRef.current);
    };
  }, []);

  // A stalled stream (dead connection, network interruption) would
  // otherwise leave the buffering spinner showing forever — after 20s of
  // continuous buffering with no progress, surface the retry UI instead.
  useEffect(() => {
    if (!buffering) return;
    const timeout = setTimeout(() => {
      setBuffering(false);
      setError(true);
    }, 20000);
    return () => clearTimeout(timeout);
  }, [buffering, src]);

  const revealControls = useCallback(() => {
    setControlsVisible(true);
    if (hideTimerRef.current) clearTimeout(hideTimerRef.current);
    hideTimerRef.current = setTimeout(() => setControlsVisible(false), CONTROLS_HIDE_DELAY_MS);
  }, []);

  function togglePlay() {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused || video.ended) {
      if (video.ended) video.currentTime = 0;
      video.play().catch(() => {});
    } else {
      video.pause();
    }
    revealControls();
  }

  function seekTo(position: number) {
    const video = videoRef.current;
    if (!video || !duration) return;
    video.currentTime = Math.min(Math.max(position, 0), duration);
  }

  function skip(deltaSeconds: number) {
    const video = videoRef.current;
    if (!video || !duration) return;
    video.currentTime = Math.min(Math.max(video.currentTime + deltaSeconds, 0), duration);
    revealControls();
  }

  function toggleMute() {
    const video = videoRef.current;
    if (!video) return;
    video.muted = !video.muted;
  }

  function handleVolumeChange(next: number) {
    const video = videoRef.current;
    if (!video) return;
    video.volume = next;
    video.muted = next === 0;
    revealControls();
  }

  function setPlaybackSpeed(next: number) {
    const video = videoRef.current;
    if (video) video.playbackRate = next;
    setSpeed(next);
    setSettingsOpen(false);
  }

  async function toggleFullscreen() {
    const container = containerRef.current;
    const video = videoRef.current;
    if (!container) return;

    if (document.fullscreenElement) {
      await document.exitFullscreen?.().catch(() => {});
      return;
    }

    if (container.requestFullscreen) {
      await container.requestFullscreen().catch(() => {});
    } else {
      // iOS Safari has no element-level Fullscreen API — only the
      // <video> itself can go fullscreen there, using native controls.
      const iosVideo = video as HTMLVideoElement & { webkitEnterFullscreen?: () => void };
      iosVideo?.webkitEnterFullscreen?.();
    }
    revealControls();
  }

  function handleRetry() {
    setError(false);
    setRetrying(true);
    onRetryLoad?.();
  }

  function handleSurfaceClick(event: React.MouseEvent) {
    if (event.target !== event.currentTarget && !(event.target instanceof HTMLVideoElement)) return;
    togglePlay();
  }

  function handleKeyDown(event: React.KeyboardEvent) {
    if (!isPlayerSurfaceTarget(event.target)) return;

    switch (event.key) {
      case " ":
      case "Spacebar":
        event.preventDefault();
        togglePlay();
        break;
      case "ArrowLeft":
        event.preventDefault();
        skip(-5);
        break;
      case "ArrowRight":
        event.preventDefault();
        skip(5);
        break;
      case "m":
      case "M":
        toggleMute();
        break;
      case "f":
      case "F":
        toggleFullscreen();
        break;
    }
  }

  const displayedTime = isDragging ? dragValue : currentTime;
  const progressPercent = duration > 0 ? (displayedTime / duration) * 100 : 0;
  const showBigPlayButton = !buffering && !error && !playing && !ended;
  const showControlsBar = controlsVisible || !playing || settingsOpen || buffering || ended;

  return (
    <div
      ref={containerRef}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      onMouseMove={revealControls}
      onTouchStart={revealControls}
      onContextMenu={(event) => event.preventDefault()}
      // Capture phase, so it runs before any inner control's own onClick —
      // keeps keyboard focus on the player itself after any interaction,
      // even one whose target element (e.g. the big center play button)
      // immediately unmounts. Without this, focus falls back to
      // document.body once that element disappears and every keyboard
      // shortcut silently stops working until the player is re-clicked.
      onClickCapture={() => containerRef.current?.focus()}
      className="group relative mx-auto w-full max-w-[960px] overflow-hidden rounded-card bg-black shadow-[var(--shadow-lg)] outline-none focus-visible:ring-2 focus-visible:ring-accent-blue/50"
    >
      <div className="relative isolate aspect-video" onClick={handleSurfaceClick}>
        <video
          key={src}
          ref={videoRef}
          className="h-full w-full"
          poster={poster}
          preload="metadata"
          playsInline
          controlsList="nodownload noremoteplayback"
          disablePictureInPicture
          onLoadedMetadata={(event) => {
            const video = event.currentTarget;
            setDuration(video.duration || 0);
            video.volume = volume;
            video.playbackRate = speed;
            if (!restoredPositionRef.current && initialPosition > 0) {
              video.currentTime = initialPosition;
              restoredPositionRef.current = true;
            }
          }}
          onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)}
          onPlay={() => {
            setPlaying(true);
            setEnded(false);
            revealControls();
          }}
          onPause={() => {
            setPlaying(false);
            setControlsVisible(true);
            if (hideTimerRef.current) clearTimeout(hideTimerRef.current);
          }}
          onWaiting={() => setBuffering(true)}
          onPlaying={() => setBuffering(false)}
          onCanPlay={() => setBuffering(false)}
          onVolumeChange={(event) => {
            setVolume(event.currentTarget.volume);
            setMuted(event.currentTarget.muted);
          }}
          onSeeked={(event) => {
            const video = event.currentTarget;
            onProgressRef.current?.(Math.floor(video.currentTime), video.ended);
          }}
          onEnded={() => {
            setPlaying(false);
            setEnded(true);
            setControlsVisible(true);
            const video = videoRef.current;
            onProgressRef.current?.(Math.floor(video?.currentTime ?? duration), true);
          }}
          onError={() => {
            setBuffering(false);
            setError(true);
            setRetrying(false);
          }}
        >
          <source src={src} type="video/mp4" />
        </video>

        {buffering && !error && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/40">
            <Loader2 size={36} className="animate-spin text-white/90" />
          </div>
        )}

        {error && (
          <div className="absolute inset-0 z-20 flex flex-col items-center justify-center gap-3 bg-black text-center">
            <AlertTriangle size={28} className="text-danger" />
            <p className="px-6 text-sm text-white/80">{t("lessons.videoStreamError")}</p>
            <button
              type="button"
              onClick={handleRetry}
              disabled={retrying}
              className="flex items-center gap-2 rounded-full bg-white/10 px-5 py-2.5 text-sm font-semibold text-white backdrop-blur transition-colors hover:bg-white/20 disabled:opacity-50"
            >
              {retrying ? <Loader2 size={16} className="animate-spin" /> : <RotateCcw size={16} />}
              {t("lessons.videoRetry")}
            </button>
          </div>
        )}

        {showBigPlayButton && (
          <button
            type="button"
            aria-label={t("lessons.mediaPlay")}
            onClick={togglePlay}
            className="absolute inset-0 z-10 flex items-center justify-center"
          >
            <span className="flex h-16 w-16 items-center justify-center rounded-full bg-white/15 backdrop-blur transition-transform hover:scale-105 hover:bg-white/25">
              <Play size={28} className="ml-1 text-white" />
            </span>
          </button>
        )}

        {ended && !error && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/60">
            <button
              type="button"
              onClick={() => {
                seekTo(0);
                videoRef.current?.play().catch(() => {});
              }}
              className="flex items-center gap-2 rounded-full bg-white/10 px-5 py-2.5 text-sm font-semibold text-white backdrop-blur transition-colors hover:bg-white/20"
            >
              <RotateCcw size={16} />
              {t("lessons.mediaReplay")}
            </button>
          </div>
        )}

        {watermarkText && !buffering && !error && (
          <div className="pointer-events-none absolute inset-0 z-[5] select-none">
            <span className="absolute right-3 top-3 rounded bg-black/35 px-2 py-1 text-[11px] font-medium tracking-wide text-white/80">
              {watermarkText}
            </span>
            <span className="absolute bottom-14 left-3 rounded bg-black/35 px-2 py-1 text-[11px] font-medium tracking-wide text-white/60">
              {watermarkText}
            </span>
          </div>
        )}
      </div>

      {!error && (
        <div
          className={`absolute inset-x-0 bottom-0 z-10 bg-gradient-to-t from-black/90 via-black/70 to-transparent px-3 pb-2 pt-8 transition-opacity duration-300 sm:px-4 ${
            showControlsBar ? "opacity-100" : "opacity-0"
          }`}
        >
          <input
            type="range"
            aria-label={t("lessons.videoSeek")}
            min={0}
            max={duration || 0}
            step={0.1}
            value={displayedTime}
            disabled={!duration}
            onKeyDown={(event) => event.stopPropagation()}
            onPointerDown={() => {
              setDragValue(currentTime);
              setIsDragging(true);
            }}
            onPointerUp={(event) => {
              setIsDragging(false);
              seekTo(Number((event.target as HTMLInputElement).value));
            }}
            onChange={(event) => {
              const next = Number(event.target.value);
              setDragValue(next);
              if (!isDragging) seekTo(next);
            }}
            className="h-1.5 w-full cursor-pointer appearance-none rounded-full bg-white/25 disabled:cursor-default [&::-moz-range-thumb]:h-3.5 [&::-moz-range-thumb]:w-3.5 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:border-0 [&::-moz-range-thumb]:bg-white [&::-moz-range-thumb]:shadow-[0_1px_4px_rgba(0,0,0,0.4)] [&::-webkit-slider-thumb]:h-3.5 [&::-webkit-slider-thumb]:w-3.5 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:shadow-[0_1px_4px_rgba(0,0,0,0.4)]"
            style={{
              background: `linear-gradient(to right, var(--accent-blue) ${progressPercent}%, rgba(255,255,255,0.25) ${progressPercent}%)`,
            }}
          />

          <div className="mt-1.5 flex items-center justify-between gap-1 sm:gap-2">
            <div className="flex items-center gap-0.5 sm:gap-1.5">
              <button
                type="button"
                onClick={togglePlay}
                aria-label={playing ? t("lessons.mediaPause") : t("lessons.mediaPlay")}
                className="flex h-11 w-11 items-center justify-center rounded-full text-white transition-colors hover:bg-white/15"
              >
                {playing ? <Pause size={19} /> : <Play size={19} className="ml-0.5" />}
              </button>

              <button
                type="button"
                onClick={() => skip(-SKIP_SECONDS)}
                aria-label={t("lessons.videoSkipBack15")}
                className="relative flex h-11 w-11 items-center justify-center rounded-full text-white transition-colors hover:bg-white/15"
              >
                <RotateCcw size={18} />
                <span className="absolute inset-0 flex items-center justify-center pt-[3px] text-[8px] font-bold">
                  {SKIP_SECONDS}
                </span>
              </button>

              <button
                type="button"
                onClick={() => skip(SKIP_SECONDS)}
                aria-label={t("lessons.videoSkipForward15")}
                className="relative flex h-11 w-11 items-center justify-center rounded-full text-white transition-colors hover:bg-white/15"
              >
                <RotateCw size={18} />
                <span className="absolute inset-0 flex items-center justify-center pt-[3px] text-[8px] font-bold">
                  {SKIP_SECONDS}
                </span>
              </button>

              <span className="ml-1 hidden shrink-0 whitespace-nowrap text-xs font-medium text-white/85 sm:inline">
                {formatTime(displayedTime)} / {formatTime(duration)}
              </span>
              <span className="ml-0.5 shrink-0 whitespace-nowrap text-[11px] font-medium text-white/85 sm:hidden">
                {formatTime(displayedTime)}
              </span>
            </div>

            <div className="flex items-center gap-0.5 sm:gap-1.5">
              <div className="hidden items-center gap-1.5 sm:flex">
                <button
                  type="button"
                  onClick={toggleMute}
                  aria-label={muted || volume === 0 ? t("lessons.mediaUnmute") : t("lessons.mediaMute")}
                  className="flex h-10 w-10 items-center justify-center rounded-full text-white transition-colors hover:bg-white/15"
                >
                  {muted || volume === 0 ? <VolumeX size={17} /> : <Volume2 size={17} />}
                </button>
                <input
                  type="range"
                  aria-label={t("lessons.videoVolume")}
                  min={0}
                  max={1}
                  step={0.05}
                  value={muted ? 0 : volume}
                  onKeyDown={(event) => event.stopPropagation()}
                  onChange={(event) => handleVolumeChange(Number(event.target.value))}
                  className="h-1 w-16 cursor-pointer appearance-none rounded-full bg-white/25 [&::-moz-range-thumb]:h-2.5 [&::-moz-range-thumb]:w-2.5 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:border-0 [&::-moz-range-thumb]:bg-white [&::-webkit-slider-thumb]:h-2.5 [&::-webkit-slider-thumb]:w-2.5 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white"
                  style={{
                    background: `linear-gradient(to right, #fff ${(muted ? 0 : volume) * 100}%, rgba(255,255,255,0.25) ${(muted ? 0 : volume) * 100}%)`,
                  }}
                />
              </div>

              <button
                type="button"
                onClick={toggleMute}
                aria-label={muted || volume === 0 ? t("lessons.mediaUnmute") : t("lessons.mediaMute")}
                className="flex h-10 w-10 items-center justify-center rounded-full text-white transition-colors hover:bg-white/15 sm:hidden"
              >
                {muted || volume === 0 ? <VolumeX size={17} /> : <Volume2 size={17} />}
              </button>

              <div className="relative" ref={settingsRef}>
                <button
                  type="button"
                  onClick={() => setSettingsOpen((open) => !open)}
                  aria-label={t("lessons.videoSettings")}
                  className="flex h-10 w-10 items-center justify-center rounded-full text-white transition-colors hover:bg-white/15"
                >
                  <Settings size={17} />
                </button>

                {settingsOpen && (
                  <div className="absolute bottom-full right-0 z-20 mb-2 w-32 overflow-hidden rounded-xl bg-black/95 p-1.5 shadow-[var(--shadow-lg)] ring-1 ring-white/10 backdrop-blur">
                    <p className="px-2.5 pb-1 pt-1 text-[10px] font-semibold uppercase tracking-wide text-white/50">
                      {t("lessons.videoSpeed")}
                    </p>
                    {SPEED_OPTIONS.map((option) => (
                      <button
                        key={option}
                        type="button"
                        onClick={() => setPlaybackSpeed(option)}
                        className={`flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 text-sm transition-colors ${
                          option === speed ? "bg-white/15 text-white" : "text-white/75 hover:bg-white/10"
                        }`}
                      >
                        {option}x
                        {option === speed && <Check size={13} />}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <button
                type="button"
                onClick={toggleFullscreen}
                aria-label={t("lessons.mediaFullscreen")}
                className="flex h-10 w-10 items-center justify-center rounded-full text-white transition-colors hover:bg-white/15"
              >
                {fullscreen ? <Minimize size={17} /> : <Maximize size={17} />}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
