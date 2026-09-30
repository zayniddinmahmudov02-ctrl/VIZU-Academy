"use client";

import { useEffect, useRef, useState } from "react";
import { Clock } from "lucide-react";

import { cn } from "@/lib/utils";

interface Props {
  minutes: number;
  className?: string;
  /** Fires exactly once, the instant the countdown reaches 0. */
  onExpire?: () => void;
}

/** Simple client-side countdown — purely a UX affordance for this
 * placeholder flow (nothing submits or locks when it hits zero, since
 * there's no real content/grading yet to enforce a hard cutoff against).
 * No shared Timer component existed anywhere in the app yet, so this one
 * is new, but it deliberately mirrors the existing Clock3/duration
 * styling already used on the Vorbereitung Teil cards rather than
 * inventing a new look. The caller remounts this (via `key`) whenever
 * the countdown should restart — e.g. one `key` per skill step, see
 * step-shell.tsx — rather than this component resetting itself. */
export default function VizuMockTimer({ minutes, className, onExpire }: Props) {
  const [remaining, setRemaining] = useState(() => minutes * 60);
  const expiredRef = useRef(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setRemaining((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (remaining === 0 && !expiredRef.current) {
      expiredRef.current = true;
      onExpire?.();
    }
  }, [remaining, onExpire]);

  const mm = String(Math.floor(remaining / 60)).padStart(2, "0");
  const ss = String(remaining % 60).padStart(2, "0");
  const low = remaining <= 60 && remaining > 0;
  const expired = remaining === 0;

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-bold tabular-nums ring-1",
        expired
          ? "bg-danger/10 text-danger ring-danger/20"
          : low
            ? "bg-warning/10 text-warning ring-warning/20"
            : "bg-surface-hover text-text-primary ring-surface-border",
        className,
      )}
    >
      <Clock size={14} />
      {mm}:{ss}
    </div>
  );
}
