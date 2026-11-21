"use client";

import { useConnectionQualityIndicator, useConnectionState } from "@livekit/components-react";
import { ConnectionQuality, ConnectionState, type Participant } from "livekit-client";
import { Loader2, WifiOff } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

const BARS: Record<ConnectionQuality, number> = {
  [ConnectionQuality.Excellent]: 3,
  [ConnectionQuality.Good]: 2,
  [ConnectionQuality.Poor]: 1,
  [ConnectionQuality.Lost]: 0,
  [ConnectionQuality.Unknown]: 0,
};

/** Signal bars of one participant's connection (LiveKit's own measurement). */
export function QualityBars({ participant, className }: { participant?: Participant; className?: string }) {
  const { t } = useTranslation();
  const { quality } = useConnectionQualityIndicator(participant ? { participant } : undefined);
  const bars = BARS[quality] ?? 0;
  const label = t(`videoRoom.quality_${quality}`);
  return (
    <span role="img" aria-label={label} title={label} data-quality={quality} className={cn("inline-flex h-3.5 items-end gap-0.5", className)}>
      {[1, 2, 3].map((n) => (
        <span key={n} className={cn("w-1 rounded-sm", n === 1 ? "h-1.5" : n === 2 ? "h-2.5" : "h-3.5",
          n <= bars ? (bars === 1 ? "bg-amber-400" : "bg-emerald-400") : quality === ConnectionQuality.Lost ? "bg-red-500/70" : "bg-white/30")} />
      ))}
    </span>
  );
}

/** Banner while the connection to the SFU is being re-established (LiveKit reconnects on its own). */
export default function ConnectionStatus() {
  const { t } = useTranslation();
  const state = useConnectionState();
  if (state === ConnectionState.Reconnecting || state === ConnectionState.SignalReconnecting) {
    return (
      <div role="status" data-testid="video-reconnecting"
           className="pointer-events-none absolute inset-x-0 top-2 z-20 mx-auto flex w-fit items-center gap-2 rounded-full bg-amber-500/90 px-4 py-1.5 text-xs font-semibold text-black shadow">
        <Loader2 size={14} className="animate-spin" /> {t("videoRoom.reconnecting")}
      </div>
    );
  }
  if (state === ConnectionState.Disconnected) {
    return (
      <div role="status" className="pointer-events-none absolute inset-x-0 top-2 z-20 mx-auto flex w-fit items-center gap-2 rounded-full bg-red-600/90 px-4 py-1.5 text-xs font-semibold text-white shadow">
        <WifiOff size={14} /> {t("videoRoom.disconnected")}
      </div>
    );
  }
  return null;
}
