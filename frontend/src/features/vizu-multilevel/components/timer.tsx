"use client";

import { useEffect, useRef, useState } from "react";
import { Clock } from "lucide-react";

import { cn } from "@/lib/utils";

interface Props {
  /** Seconds left, as computed by the SERVER when the section was opened. */
  initialSeconds: number;
  className?: string;
  /** Fires exactly once, the instant the countdown reaches 0. */
  onExpire?: () => void;
}

/** Display-only countdown. The authority is the backend: `initialSeconds`
 * comes from the server's own clock and the server independently rejects
 * late input (deadline + grace), so tampering with this component cannot
 * extend the real time limit. The end time is fixed once on mount and the
 * remaining time is derived from the clock on every tick, so background-tab
 * throttling cannot make the display drift. */
export default function VizuMultilevelTimer({ initialSeconds, className, onExpire }: Props) {
  const [endAt] = useState(() => Date.now() + initialSeconds * 1000);
  const [remaining, setRemaining] = useState(initialSeconds);
  const expiredRef = useRef(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setRemaining(Math.max(0, Math.ceil((endAt - Date.now()) / 1000)));
    }, 500);
    return () => clearInterval(interval);
  }, [endAt]);

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
