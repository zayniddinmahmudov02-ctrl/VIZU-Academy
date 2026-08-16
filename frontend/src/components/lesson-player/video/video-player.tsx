"use client";

import { useEffect, useRef, useState } from "react";
import Plyr from "plyr";
import "plyr/dist/plyr.css";
import { AlertTriangle, Loader2, RotateCcw } from "lucide-react";

import { useLessonProgressStore } from "@/store/lesson-progress-store";
import { useTranslation } from "@/lib/i18n/use-translation";

/** How often (ms) we report the current position to the server while
 *  playing. Free seeking is intentional: the player has no seek
 *  restrictions of any kind, and the server accepts whatever position is
 *  reported (bounded only to the video's real duration) — see
 *  VideoProgressService.update_progress. */
const PROGRESS_REPORT_INTERVAL_MS = 5000;

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
  /** Called (throttled) with the current playback position as the user
   *  watches, and once more with `ended: true` when playback finishes. */
  onProgress?: (position: number, ended: boolean) => void;
  /** Shown as a semi-transparent overlay burned into the player chrome
   *  (not the video itself) — e.g. "VIZU Academy · Jane D. · a1b2c3d4".
   *  Doesn't stop screen recording (nothing client-side can), but ties
   *  any recording that does get made back to the account it came from,
   *  which is the practical deterrent available without real DRM. Only
   *  rendered when provided, so a logged-out/loading state just omits it
   *  rather than showing a broken watermark. */
  watermarkText?: string;
}

export default function VideoPlayer({ src, poster, lessonId, initialPosition = 0, onProgress, watermarkText }: Props) {
  const { t } = useTranslation();
  const videoRef = useRef<HTMLVideoElement>(null);
  const playerRef = useRef<Plyr | null>(null);
  const markSectionComplete = useLessonProgressStore((state) => state.markSectionComplete);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [ended, setEnded] = useState(false);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    setLoading(true);
    setError(false);
    setEnded(false);

    const player = new Plyr(video, {
      controls: [
        "play-large",
        "rewind",
        "play",
        "progress",
        "current-time",
        "duration",
        "mute",
        "volume",
        "settings",
        "fullscreen",
      ],
      settings: ["speed"],
      speed: { selected: 1, options: [1, 1.25, 1.5] },
      seekTime: 10,
      clickToPlay: true,
      disableContextMenu: true,
      keyboard: { focused: true, global: false },
    });

    playerRef.current = player;

    let reportTimer: ReturnType<typeof setInterval> | null = null;

    function handleReady() {
      setLoading(false);

      if (initialPosition > 0) {
        player.currentTime = initialPosition;
      }
    }

    function handleWaiting() {
      setLoading(true);
    }

    function handlePlaying() {
      setLoading(false);
    }

    function handleError() {
      setLoading(false);
      setError(true);
    }

    function reportProgress(isEnded: boolean) {
      onProgress?.(Math.floor(player.currentTime), isEnded);
    }

    function handleEnded() {
      setEnded(true);
      reportProgress(true);

      if (lessonId) {
        markSectionComplete(lessonId, "video");
      }
    }

    player.on("ready", handleReady);
    player.on("waiting", handleWaiting);
    player.on("playing", handlePlaying);
    player.on("error", handleError);
    player.on("ended", handleEnded);

    if (onProgress) {
      reportTimer = setInterval(() => {
        if (!player.paused && !player.ended) {
          reportProgress(false);
        }
      }, PROGRESS_REPORT_INTERVAL_MS);
    }

    return () => {
      if (reportTimer) clearInterval(reportTimer);
      player.off("ready", handleReady);
      player.off("waiting", handleWaiting);
      player.off("playing", handlePlaying);
      player.off("error", handleError);
      player.off("ended", handleEnded);
      player.destroy();
      playerRef.current = null;
    };
    // Re-init whenever the URL changes — Plyr doesn't pick up a swapped
    // <source> reliably on its own.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [src, lessonId]);

  function handleReplay() {
    const player = playerRef.current;
    if (!player) return;

    setEnded(false);
    player.restart();
    player.play();
  }

  return (
    <div className="mx-auto w-full max-w-[960px]">
      <div
        className="relative aspect-video overflow-hidden rounded-card bg-black shadow-[var(--shadow-lg)]"
        onContextMenu={(event) => event.preventDefault()}
      >
        {loading && !error && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-black">
            <Loader2 size={32} className="animate-spin text-white/80" />
          </div>
        )}

        {error && (
          <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-2 bg-black text-center">
            <AlertTriangle size={28} className="text-danger" />
            <p className="px-6 text-sm text-white/80">{t("lessons.videoNotAvailable")}</p>
          </div>
        )}

        {ended && !loading && !error && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/60">
            <button
              type="button"
              onClick={handleReplay}
              className="flex items-center gap-2 rounded-full bg-white/10 px-5 py-2.5 text-sm font-semibold text-white backdrop-blur transition-colors hover:bg-white/20"
            >
              <RotateCcw size={16} />
              {t("lessons.mediaReplay")}
            </button>
          </div>
        )}

        <video
          ref={videoRef}
          className={`h-full w-full ${error ? "invisible" : ""}`}
          poster={poster}
          playsInline
          controlsList="nodownload noremoteplayback"
          disablePictureInPicture
          onContextMenu={(event) => event.preventDefault()}
        >
          <source src={src} type="video/mp4" />
        </video>

        {watermarkText && !loading && !error && (
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
    </div>
  );
}
