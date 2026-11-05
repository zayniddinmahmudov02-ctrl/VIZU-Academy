import { useId } from "react";

import { cn } from "@/lib/utils";

/**
 * VIZU DEUTSCH BATTLE mark: navy hex shield with a gold rim, two crossed gold swords and a
 * black-red-gold medallion in the centre. Same props as a lucide icon (size / className), so it drops
 * into the sidebar, the mobile navigation and notification rows. Public copy: /battle/battle-icon.svg.
 */
export default function BattleIcon({ size = 24, className, title }: { size?: number; className?: string; strokeWidth?: number; title?: string }) {
  const id = useId().replace(/:/g, "");
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" className={cn("shrink-0", className)} role={title ? "img" : undefined}
         aria-hidden={title ? undefined : true} aria-label={title} data-icon="battle">
      <defs>
        <linearGradient id={`bg${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#24406E" />
          <stop offset="100%" stopColor="#0B1426" />
        </linearGradient>
        <linearGradient id={`au${id}`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#FFF2C4" />
          <stop offset="45%" stopColor="#F2C45B" />
          <stop offset="100%" stopColor="#B07A16" />
        </linearGradient>
        <clipPath id={`md${id}`}>
          <circle cx="32" cy="32" r="8.5" />
        </clipPath>
      </defs>
      <path d="M32 2.5 58 17.5v29L32 61.5 6 46.5v-29Z" fill={`url(#bg${id})`} stroke={`url(#au${id})`} strokeWidth="3" strokeLinejoin="round" />
      <path d="M32 7.5 53.5 20" stroke="#fff" strokeOpacity=".25" strokeWidth="2" strokeLinecap="round" />
      {[0, 1].map((i) => (
        <g key={i} transform={i ? "translate(64 0) scale(-1 1)" : undefined}>
          <path d="M14.5 14.5 41 41" stroke={`url(#au${id})`} strokeWidth="4.6" strokeLinecap="round" />
          <path d="M15.5 14.2 40 38.7" stroke="#fff" strokeOpacity=".55" strokeWidth="1.2" strokeLinecap="round" />
          <path d="M37 45.5 45.5 37" stroke="#F2C45B" strokeWidth="4" strokeLinecap="round" />
          <path d="M44 44l6.5 6.5" stroke="#D83B43" strokeWidth="4.2" strokeLinecap="round" />
          <circle cx="51.5" cy="51.5" r="2.6" fill={`url(#au${id})`} />
        </g>
      ))}
      <circle cx="32" cy="32" r="10.5" fill="#0B1426" stroke={`url(#au${id})`} strokeWidth="2.2" />
      <g clipPath={`url(#md${id})`}>
        <rect x="22" y="23.5" width="20" height="5.67" fill="#111" />
        <rect x="22" y="29.17" width="20" height="5.67" fill="#D83B43" />
        <rect x="22" y="34.83" width="20" height="5.67" fill="#F2C45B" />
      </g>
    </svg>
  );
}
