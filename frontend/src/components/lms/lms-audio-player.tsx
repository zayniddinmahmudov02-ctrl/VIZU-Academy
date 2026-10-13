"use client";

import { useRef, useState } from "react";
import { AlertTriangle, Loader2, Pause, Play, RotateCcw, SkipBack, SkipForward } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

/** Audio for learning resources: play / pause, a seekable timeline (Range
 * requests are answered by the backend), ±10 s, duration, and a retry that
 * asks for a freshly signed URL when loading fails. */
export default function LmsAudioPlayer({ src, title, onRetry }: { src: string; title: string; onRetry: () => Promise<string | null> }) {
  const { t } = useTranslation();
  const audioRef = useRef<HTMLAudioElement>(null);
  const [url, setUrl] = useState(src);
  const [playing, setPlaying] = useState(false);
  const [current, setCurrent] = useState(0);
  const [duration, setDuration] = useState(0);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);

  function toggle() {
    const audio = audioRef.current;
    if (!audio) return;
    if (audio.paused) {
      audio.play().catch(() => setFailed(true));
    } else {
      audio.pause();
    }
  }

  function seek(to: number) {
    const audio = audioRef.current;
    if (!audio || !Number.isFinite(audio.duration)) return;
    audio.currentTime = Math.min(Math.max(to, 0), audio.duration);
  }

  async function retry() {
    setFailed(false);
    setLoading(true);
    const fresh = await onRetry();
    if (fresh) setUrl(fresh);
    else setFailed(true);
  }

  return (
    <div className="rounded-2xl bg-gradient-to-br from-brand-900 to-brand-700 p-4 text-white sm:p-5" data-testid="lms-audio">
      <audio
        key={url}
        ref={audioRef}
        src={url}
        preload="metadata"
        onLoadedMetadata={(e) => {
          setDuration(e.currentTarget.duration);
          setLoading(false);
        }}
        onCanPlay={() => setLoading(false)}
        onTimeUpdate={(e) => setCurrent(e.currentTarget.currentTime)}
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => setPlaying(false)}
        onError={() => {
          setFailed(true);
          setLoading(false);
          setPlaying(false);
        }}
      />
      <p className="mb-3 truncate text-sm font-semibold">{title}</p>

      {failed ? (
        <div className="flex flex-wrap items-center gap-3 text-sm" role="alert">
          <AlertTriangle size={18} className="text-amber-300" />
          <span className="text-white/85">{t("lms.audioError")}</span>
          <button type="button" onClick={retry} className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1.5 font-semibold hover:bg-white/25">
            <RotateCcw size={14} /> {t("lms.retry")}
          </button>
        </div>
      ) : (
        <div className="flex items-center gap-3">
          <button type="button" onClick={() => seek(current - 10)} aria-label={t("lessons.mediaSkipBack")} className="hidden h-9 w-9 items-center justify-center rounded-full hover:bg-white/10 sm:flex">
            <SkipBack size={16} />
          </button>
          <button
            type="button"
            onClick={toggle}
            disabled={loading && duration === 0}
            aria-label={playing ? t("lessons.mediaPause") : t("lessons.mediaPlay")}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-white/20 transition hover:bg-white/30 disabled:opacity-60"
          >
            {loading && duration === 0 ? <Loader2 size={18} className="animate-spin" /> : playing ? <Pause size={18} /> : <Play size={18} className="ml-0.5" />}
          </button>
          <button type="button" onClick={() => seek(current + 10)} aria-label={t("lessons.mediaSkipForward")} className="hidden h-9 w-9 items-center justify-center rounded-full hover:bg-white/10 sm:flex">
            <SkipForward size={16} />
          </button>
          <span className="w-10 shrink-0 text-right text-xs tabular-nums text-white/80">{formatTime(current)}</span>
          <input
            type="range"
            min={0}
            max={duration || 0}
            step={0.1}
            value={Math.min(current, duration || 0)}
            onChange={(e) => seek(Number(e.target.value))}
            aria-label={t("lms.audioPosition")}
            className="h-1.5 min-w-0 flex-1 cursor-pointer accent-white"
            data-testid="lms-audio-seek"
          />
          <span className="w-10 shrink-0 text-xs tabular-nums text-white/80">{formatTime(duration)}</span>
        </div>
      )}
    </div>
  );
}
