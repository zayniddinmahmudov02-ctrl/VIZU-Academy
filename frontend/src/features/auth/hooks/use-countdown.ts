"use client";

import { useEffect, useState } from "react";

/** Milliseconds left until `until` (epoch ms); 0 when passed or not set. */
export function useCountdown(until: number | null): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!until) return;
    const timer = setInterval(() => setNow(Date.now()), 250);
    return () => clearInterval(timer);
  }, [until]);
  return until ? Math.max(0, until - now) : 0;
}

/** "00:59" for the remaining milliseconds — counts 00:59 … 00:00. */
export function formatCountdown(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  return `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
}
