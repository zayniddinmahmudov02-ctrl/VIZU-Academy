"use client";

import { useRef, useState } from "react";
import { Headphones, Pause, Play, SkipBack, SkipForward } from "lucide-react";

import ProgressBar from "@/components/ui/progress-bar";
import { useTranslation } from "@/lib/i18n/use-translation";

interface Props {
  src: string;
}

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return "00:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export default function ListeningPlayer({ src }: Props) {
  const { t } = useTranslation();
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  function togglePlay() {
    const audio = audioRef.current;
    if (!audio) return;
    if (audio.paused) {
      audio.play();
    } else {
      audio.pause();
    }
  }

  function skip(delta: number) {
    const audio = audioRef.current;
    if (!audio) return;
    audio.currentTime = Math.min(Math.max(audio.currentTime + delta, 0), audio.duration || 0);
  }

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="rounded-2xl bg-gradient-to-br from-brand-900 to-brand-700 p-8 text-white sm:p-10">
      <audio
        ref={audioRef}
        src={src}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
        onLoadedMetadata={(e) => setDuration(e.currentTarget.duration)}
        onEnded={() => setIsPlaying(false)}
      />

      <Headphones size={48} className="mx-auto" />

      <div className="mt-6">
        <ProgressBar value={progress} trackClassName="h-2 bg-white/15" />
        <div className="mt-2 flex justify-between text-xs text-white/70">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </div>
      </div>

      <div className="mt-6 flex items-center justify-center gap-5">
        <button
          type="button"
          onClick={() => skip(-10)}
          aria-label={t("lessons.mediaSkipBack")}
          className="flex h-10 w-10 items-center justify-center rounded-full transition hover:bg-white/10"
        >
          <SkipBack size={18} />
        </button>
        <button
          type="button"
          onClick={togglePlay}
          aria-label={isPlaying ? t("lessons.mediaPause") : t("lessons.mediaPlay")}
          className="flex h-14 w-14 items-center justify-center rounded-full bg-white/20 backdrop-blur transition hover:scale-105"
        >
          {isPlaying ? <Pause size={22} /> : <Play size={22} className="ml-0.5" />}
        </button>
        <button
          type="button"
          onClick={() => skip(10)}
          aria-label={t("lessons.mediaSkipForward")}
          className="flex h-10 w-10 items-center justify-center rounded-full transition hover:bg-white/10"
        >
          <SkipForward size={18} />
        </button>
      </div>
    </div>
  );
}
