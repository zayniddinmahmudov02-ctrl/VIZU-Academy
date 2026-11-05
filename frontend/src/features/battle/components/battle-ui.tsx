"use client";

import { useId, type ReactNode } from "react";
import { Coins, Loader2, RefreshCw } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

export function GlassPanel({ className, children, strong = false, as: Tag = "section", ...rest }: {
  className?: string;
  children: ReactNode;
  strong?: boolean;
  as?: "section" | "div" | "article" | "aside";
} & Record<`data-${string}`, string>) {
  return (
    <Tag className={cn(strong ? "bt-glass-strong" : "bt-glass", "rounded-3xl", className)} {...rest}>
      {children}
    </Tag>
  );
}

export function FlagStripe({ className }: { className?: string }) {
  return <span aria-hidden="true" className={cn("bt-flag-line block h-1 rounded-full", className)} />;
}

export function GermanFlag({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={(size * 3) / 5} viewBox="0 0 5 3" aria-label="Deutschland" role="img" className="shrink-0 rounded-[2px] shadow">
      <rect width="5" height="1" y="0" fill="#000" />
      <rect width="5" height="1" y="1" fill="#D83B43" />
      <rect width="5" height="1" y="2" fill="#F2C45B" />
    </svg>
  );
}

export function SectionTitle({ children, action }: { children: ReactNode; action?: ReactNode }) {
  return (
    <div className="mb-4 flex items-center justify-between gap-3">
      <h2 className="flex items-center gap-2 text-sm font-extrabold uppercase tracking-[0.18em] text-white/90">
        <span className="h-4 w-1 rounded-full bg-[var(--bt-gold)]" aria-hidden="true" />
        {children}
      </h2>
      {action}
    </div>
  );
}

export function StageChip({ stage, city, className }: { stage: string; city?: string; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full bg-[var(--bt-blue)]/20 px-3 py-1 text-xs font-extrabold tracking-wider text-white ring-1 ring-[var(--bt-blue)]/60", className)}>
      <span className="text-[var(--bt-gold)]">{stage}</span>
      {city && <span className="font-semibold text-white/80">· {city}</span>}
    </span>
  );
}

export function PointsChip({ points, className }: { points: number; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full bg-[var(--bt-gold)]/15 px-3 py-1 text-xs font-extrabold text-[var(--bt-gold)] ring-1 ring-[var(--bt-gold)]/40", className)}>
      <Coins size={13} aria-hidden="true" /> {points.toLocaleString("de-DE")} BP
    </span>
  );
}

export function ProgressBar({ value, className, tone = "gold", label }: { value: number; className?: string; tone?: "gold" | "blue"; label?: string }) {
  const pct = Math.max(0, Math.min(100, Math.round(value * 100)));
  return (
    <div className={cn("h-3 w-full overflow-hidden rounded-full bg-white/10 ring-1 ring-white/10", className)} role="progressbar" aria-valuenow={pct}
         aria-valuemin={0} aria-valuemax={100} aria-label={label}>
      <div
        className={cn("h-full rounded-full transition-[width] duration-700", tone === "gold"
          ? "bg-gradient-to-r from-[#c8901f] via-[var(--bt-gold)] to-[#fff2c4] shadow-[0_0_16px_rgba(242,196,91,0.7)]"
          : "bg-gradient-to-r from-[#1f4e9a] to-[var(--bt-blue)] shadow-[0_0_16px_rgba(57,132,232,0.7)]")}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

/** Hexagonal 3D rank badge: stage in the centre, tier as stars. */
export function RankBadge({ stage, tier, size = 72, className, glow = true }: { stage: string; tier: number; size?: number; className?: string; glow?: boolean }) {
  const id = useId().replace(/:/g, "");
  const legend = stage === "C1+";
  return (
    <svg width={size} height={size * 1.12} viewBox="0 0 100 112" className={cn(glow && "drop-shadow-[0_8px_24px_rgba(242,196,91,0.45)]", className)} role="img" aria-label={`${stage} Rang ${tier + 1}`}>
      <defs>
        <linearGradient id={`rb${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={legend ? "#ffe9a8" : "#fff2c4"} />
          <stop offset="45%" stopColor="#f2c45b" />
          <stop offset="100%" stopColor="#a8700f" />
        </linearGradient>
        <linearGradient id={`rf${id}`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor={legend ? "#3b1d5e" : "#1f4e9a"} />
          <stop offset="100%" stopColor="#101d35" />
        </linearGradient>
      </defs>
      <path d="M50 4 L92 28 L92 78 L50 102 L8 78 L8 28 Z" fill={`url(#rb${id})`} />
      <path d="M50 14 L83 33 L83 73 L50 92 L17 73 L17 33 Z" fill={`url(#rf${id})`} />
      <path d="M50 14 L83 33 L50 52 L17 33 Z" fill="#fff" opacity="0.08" />
      <text x="50" y={stage.length > 2 ? 62 : 64} textAnchor="middle" fontSize={stage.length > 2 ? 22 : 28} fontWeight="900" fill="#fff" letterSpacing="1">
        {stage}
      </text>
      <g fill="#f2c45b">
        {[0, 1, 2].map((i) => (
          <path key={i} transform={`translate(${36 + i * 14} 104)`} d="M0 -6 L1.8 -1.8 L6 -1.6 L2.7 1.2 L3.7 5.6 L0 3.2 L-3.7 5.6 L-2.7 1.2 L-6 -1.6 L-1.8 -1.8 Z"
                opacity={i <= tier ? 1 : 0.25} />
        ))}
      </g>
    </svg>
  );
}

export function LoadingState() {
  const { t } = useTranslation();
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 text-white/80" data-testid="battle-loading">
      <Loader2 className="animate-spin text-[var(--bt-gold)]" size={32} aria-hidden="true" />
      <p className="text-sm font-semibold tracking-wide">{t("battle.loading")}</p>
    </div>
  );
}

export function ErrorState({ onRetry }: { onRetry: () => void }) {
  const { t } = useTranslation();
  return (
    <GlassPanel className="mx-auto mt-16 max-w-md p-6 text-center" data-testid="battle-error">
      <p className="font-bold">{t("battle.loadError")}</p>
      <button type="button" onClick={onRetry} className="mx-auto mt-4 inline-flex items-center gap-2 rounded-xl bg-white/10 px-4 py-2 text-sm font-bold ring-1 ring-white/20 hover:bg-white/15">
        <RefreshCw size={15} aria-hidden="true" /> {t("battle.retry")}
      </button>
    </GlassPanel>
  );
}
