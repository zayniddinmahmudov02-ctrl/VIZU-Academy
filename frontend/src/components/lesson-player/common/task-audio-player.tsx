"use client";

import { useRef, useState } from "react";
import { Pause, Play, RotateCcw } from "lucide-react";

import {
  getAudioBlobUrl,
  getAudioStatus,
  registerAudioPlay,
} from "@/features/admin/services/assessment-service";
import type { AudioPolicy } from "@/features/admin/types/assessment.types";

interface Props {
  taskId: string;
  policy: AudioPolicy;
}

const SPEEDS = [0.75, 1, 1.25, 1.5];

/** The Hören audio player, respecting server-verified play policy —
 * play_limit / allow_pause / allow_seek / allow_replay / allow_speed_change.
 * The frontend disabling controls is a courtesy; every actual play is
 * still counted and rejected server-side (see registerAudioPlay), so a
 * user poking at devtools can't get more plays than the policy allows. */
export default function TaskAudioPlayer({ taskId, policy }: Props) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const [ended, setEnded] = useState(false);
  const [progress, setProgress] = useState(0);
  const [speed, setSpeed] = useState(1);
  const [playsUsed, setPlaysUsed] = useState(0);
  const [canPlay, setCanPlay] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handlePlayClick() {
    if (playing) {
      if (!policy.allow_pause) return;
      audioRef.current?.pause();
      setPlaying(false);
      return;
    }

    if (ended && !policy.allow_replay) return;
    if (!canPlay) return;

    setError(null);
    setLoading(true);
    try {
      const status = await registerAudioPlay(taskId);
      setPlaysUsed(status.plays_used);
      setCanPlay(status.can_play || status.plays_used <= (status.play_limit ?? Infinity));

      let url = blobUrl;
      if (!url) {
        url = await getAudioBlobUrl(taskId);
        setBlobUrl(url);
      }

      setEnded(false);
      requestAnimationFrame(() => {
        if (audioRef.current) {
          audioRef.current.src = url!;
          audioRef.current.playbackRate = speed;
          audioRef.current.play();
        }
      });
      setPlaying(true);
    } catch {
      setError("Wiedergabelimit erreicht oder Audio nicht verfügbar.");
      const status = await getAudioStatus(taskId).catch(() => null);
      if (status) {
        setCanPlay(status.can_play);
        setPlaysUsed(status.plays_used);
      }
    } finally {
      setLoading(false);
    }
  }

  function handleSpeedChange(value: number) {
    setSpeed(value);
    if (audioRef.current) audioRef.current.playbackRate = value;
  }

  function handleSeek(e: React.ChangeEvent<HTMLInputElement>) {
    if (!policy.allow_seek || !audioRef.current) return;
    const ratio = Number(e.target.value) / 100;
    audioRef.current.currentTime = ratio * audioRef.current.duration;
  }

  const playDisabled = loading || (!canPlay && (!ended || !policy.allow_replay)) || (ended && !policy.allow_replay);

  return (
    <div className="rounded-2xl bg-surface-hover/60 p-5 ring-1 ring-surface-border">
      <audio
        ref={audioRef}
        onTimeUpdate={(e) => {
          const el = e.currentTarget;
          if (el.duration) setProgress((el.currentTime / el.duration) * 100);
        }}
        onEnded={() => {
          setPlaying(false);
          setEnded(true);
          setProgress(0);
        }}
        className="hidden"
      />

      <div className="flex items-center gap-4">
        <button
          type="button"
          onClick={handlePlayClick}
          disabled={playDisabled}
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-accent-blue text-white shadow-md transition disabled:cursor-not-allowed disabled:opacity-40"
          aria-label={playing ? "Pause" : "Abspielen"}
        >
          {playing ? <Pause size={18} /> : ended ? <RotateCcw size={18} /> : <Play size={18} />}
        </button>

        <div className="flex-1">
          <input
            type="range"
            min={0}
            max={100}
            value={progress}
            onChange={handleSeek}
            disabled={!policy.allow_seek}
            className="w-full accent-accent-blue disabled:cursor-not-allowed disabled:opacity-50"
          />
          <div className="mt-1 flex items-center justify-between text-xs text-text-muted">
            <span>
              {policy.audio_play_limit != null
                ? `${playsUsed} / ${policy.audio_play_limit} gehört`
                : "Unbegrenzt hören"}
            </span>
            {policy.allow_speed_change && (
              <select
                value={speed}
                onChange={(e) => handleSpeedChange(Number(e.target.value))}
                className="rounded-md bg-surface-card px-1.5 py-0.5 text-xs ring-1 ring-surface-border"
              >
                {SPEEDS.map((s) => (
                  <option key={s} value={s}>
                    {s}x
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>
      </div>

      {error && <p className="mt-2 text-xs text-danger">{error}</p>}
    </div>
  );
}
