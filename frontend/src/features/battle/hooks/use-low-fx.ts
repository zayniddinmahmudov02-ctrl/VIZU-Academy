"use client";

import { useEffect, useState } from "react";

const KEY = "vizu-battle-lowfx";

/**
 * true on devices that should get the simplified arena: reduced motion, data saver, or fewer than
 * ~40 fps measured over the first 1.2 s (remembered for the session).
 */
export function useLowFx(): boolean {
  const [low, setLow] = useState(false);

  useEffect(() => {
    let stored: string | null = null;
    try {
      stored = sessionStorage.getItem(KEY);
    } catch {
      stored = null;
    }
    const nav = navigator as Navigator & { connection?: { saveData?: boolean } };
    if (stored === "1" || window.matchMedia("(prefers-reduced-motion: reduce)").matches || nav.connection?.saveData) {
      const id = requestAnimationFrame(() => setLow(true));
      return () => cancelAnimationFrame(id);
    }
    if (stored === "0") return;
    let frames = 0;
    let raf = 0;
    const start = performance.now();
    const step = (now: number) => {
      frames += 1;
      if (now - start < 1200) {
        raf = requestAnimationFrame(step);
        return;
      }
      const fps = (frames * 1000) / (now - start);
      const slow = fps < 40;
      try {
        sessionStorage.setItem(KEY, slow ? "1" : "0");
      } catch {
        /* private mode */
      }
      setLow(slow);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, []);

  return low;
}
