"use client";

import { createContext, useContext, useEffect, type ReactNode } from "react";
import { usePathname } from "next/navigation";

import { playSfx, setSuspended, setTrack, stopAudio, unlockAudio } from "@/features/battle/audio/battle-audio";
import BattleNav from "@/features/battle/components/battle-nav";
import { useLowFx } from "@/features/battle/hooks/use-low-fx";
import { cn } from "@/lib/utils";

const LowFxContext = createContext(false);

export function useBattleLowFx() {
  return useContext(LowFxContext);
}

/** Immersive frame of every Battle page: own navigation, no dashboard sidebar, low-power class for slow devices.
 * Also owns Battle audio: unlocked by the first gesture, click sound on buttons, home music outside a match,
 * paused in a hidden tab, stopped when the player leaves Battle. */
export default function BattleShell({ children }: { children: ReactNode }) {
  const lowFx = useLowFx();
  const pathname = usePathname();
  const inMatch = pathname?.startsWith("/battle/match/") ?? false;

  useEffect(() => {
    const onGesture = (e: Event) => {
      unlockAudio();
      const el = (e.target as HTMLElement | null)?.closest?.("button, a, [role=button]");
      // answer buttons have their own "select" sound
      if (e.type === "pointerdown" && el && !el.closest("[data-testid^='answer-']")) playSfx("click");
    };
    const onVisibility = () => setSuspended(document.hidden);
    window.addEventListener("pointerdown", onGesture, { passive: true });
    window.addEventListener("keydown", onGesture);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.removeEventListener("pointerdown", onGesture);
      window.removeEventListener("keydown", onGesture);
      document.removeEventListener("visibilitychange", onVisibility);
      stopAudio(); // leaving Battle: no music elsewhere on the site
    };
  }, []);

  useEffect(() => {
    if (!inMatch) setTrack("home"); // match pages choose their own track (use-battle-audio)
  }, [inMatch]);

  return (
    <LowFxContext.Provider value={lowFx}>
      <div className={cn("battle-root relative isolate", lowFx && "bt-lowfx")} data-lowfx={lowFx || undefined}>
        <BattleNav />
        <main className="relative mx-auto w-full max-w-[1440px] px-3 pb-28 pt-4 sm:px-5 md:pb-10">{children}</main>
      </div>
    </LowFxContext.Provider>
  );
}
