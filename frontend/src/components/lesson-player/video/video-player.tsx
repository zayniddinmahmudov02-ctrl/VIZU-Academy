"use client";

import { useEffect, useRef, useState } from "react";
import Plyr from "plyr";
import "plyr/dist/plyr.css";
import { AlertTriangle, Loader2 } from "lucide-react";

import { useLessonProgressStore } from "@/store/lesson-progress-store";
import { useTranslation } from "@/lib/i18n/use-translation";

interface Props {
  /** A signed, short-lived streaming URL — never a storage_key or bucket
   *  path. This component has no knowledge of where the file actually
   *  lives; it only ever receives a URL it can hand to <video>. */
  src: string;
  poster?: string;
  /** When provided, the lesson's "video" section is marked complete via
   *  the existing lesson-progress store once playback reaches the end —
   *  the same mechanism QuizSection/WritingSection already use. */
  lessonId?: string;
}

export default function VideoPlayer({ src, poster, lessonId }: Props) {
  const { t } = useTranslation();
  const videoRef = useRef<HTMLVideoElement>(null);
  const playerRef = useRef<Plyr | null>(null);
  const markSectionComplete = useLessonProgressStore((state) => state.markSectionComplete);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    setLoading(true);
    setError(false);

    const player = new Plyr(video, {
      controls: [
        "play-large",
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
      clickToPlay: true,
      disableContextMenu: true,
      keyboard: { focused: true, global: false },
    });

    playerRef.current = player;

    function handleReady() {
      setLoading(false);
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

    function handleEnded() {
      if (lessonId) {
        markSectionComplete(lessonId, "video");
      }
    }

    player.on("ready", handleReady);
    player.on("waiting", handleWaiting);
    player.on("playing", handlePlaying);
    player.on("error", handleError);
    player.on("ended", handleEnded);

    return () => {
      player.off("ready", handleReady);
      player.off("waiting", handleWaiting);
      player.off("playing", handlePlaying);
      player.off("error", handleError);
      player.off("ended", handleEnded);
      player.destroy();
      playerRef.current = null;
    };
    // Re-init whenever the signed URL changes (a fresh 5-minute link) —
    // Plyr doesn't pick up a swapped <source> reliably on its own.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [src, lessonId]);

  return (
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

      <video
        ref={videoRef}
        className={`h-full w-full ${error ? "invisible" : ""}`}
        playsInline
        controlsList="nodownload noremoteplayback"
        disablePictureInPicture
        onContextMenu={(event) => event.preventDefault()}
      >
        <source src={src} type="video/mp4" />
      </video>
    </div>
  );
}
