"use client";

import { useState } from "react";

import { API_URL } from "@/constants/api";
import BattleAvatar from "@/features/battle/components/battle-avatar";
import { apiAsset } from "@/features/battle/lib/battle-utils";
import { cn } from "@/lib/utils";

export interface AvatarSource {
  avatar: string;
  photo?: string | null;
  name?: string;
}

/**
 * A player's picture everywhere in Battle: the uploaded profile photo (round, in a holographic frame) or,
 * without one — or if it fails to load — the chosen game avatar. `round` = small circle for lists / HUD.
 */
export default function PlayerAvatar({ player, size = 160, accent = "#3984E8", round = false, animated = true, className }: {
  player: AvatarSource;
  size?: number;
  accent?: string;
  round?: boolean;
  animated?: boolean;
  className?: string;
}) {
  const [failed, setFailed] = useState<string | null>(null);
  const src = player.photo ? apiAsset(player.photo, API_URL) : null;
  const usePhoto = src !== null && failed !== src;

  if (!usePhoto) {
    return <BattleAvatar avatar={player.avatar} size={size} accent={accent} animated={animated && !round} portrait={round} title={player.name} className={className} />;
  }
  // eslint-disable-next-line @next/next/no-img-element -- user photo from /uploads, already 512×512 WebP
  const img = <img src={src} alt={player.name ?? ""} loading="lazy" decoding="async" onError={() => setFailed(src)} className="h-full w-full rounded-full object-cover" data-testid="player-photo" />;

  if (round) {
    return <span className={cn("inline-block overflow-hidden rounded-full", className)} style={{ width: size, height: size }}>{img}</span>;
  }
  const d = Math.round(size * 0.78);
  return (
    <div className={cn("relative inline-flex flex-col items-center", animated && "bt-avatar", className)} style={{ width: size, height: size * 1.1 }} role="img" aria-label={player.name}>
      <span aria-hidden="true" className="absolute bottom-0 h-[14%] w-[86%] rounded-[50%] blur-md" style={{ background: `radial-gradient(closest-side, ${accent}cc, transparent)` }} />
      <span aria-hidden="true" className="absolute bottom-[3%] h-[8%] w-[64%] rounded-[50%] border-2" style={{ borderColor: `${accent}cc` }} />
      <span className="relative mt-[4%] rounded-full p-[3px] shadow-[0_18px_40px_-14px_rgba(0,0,0,0.8)]"
            style={{ width: d, height: d, background: `conic-gradient(from 210deg, ${accent}, #F2C45B, #ffffff, ${accent})` }}>
        <span className="block h-full w-full overflow-hidden rounded-full bg-[#101D35]">{img}</span>
        <span aria-hidden="true" className="pointer-events-none absolute inset-[3px] rounded-full bg-[linear-gradient(140deg,rgba(255,255,255,0.28),transparent_45%)]" />
      </span>
    </div>
  );
}
