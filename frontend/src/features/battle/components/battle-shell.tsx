"use client";

import { createContext, useContext, type ReactNode } from "react";

import BattleNav from "@/features/battle/components/battle-nav";
import { useLowFx } from "@/features/battle/hooks/use-low-fx";
import { cn } from "@/lib/utils";

const LowFxContext = createContext(false);

export function useBattleLowFx() {
  return useContext(LowFxContext);
}

/** Immersive frame of every Battle page: own navigation, no dashboard sidebar, low-power class for slow devices. */
export default function BattleShell({ children }: { children: ReactNode }) {
  const lowFx = useLowFx();
  return (
    <LowFxContext.Provider value={lowFx}>
      <div className={cn("battle-root relative isolate", lowFx && "bt-lowfx")} data-lowfx={lowFx || undefined}>
        <BattleNav />
        <main className="relative mx-auto w-full max-w-[1440px] px-3 pb-28 pt-4 sm:px-5 md:pb-10">{children}</main>
      </div>
    </LowFxContext.Provider>
  );
}
