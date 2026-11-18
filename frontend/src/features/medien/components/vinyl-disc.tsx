"use client";

/* eslint-disable @next/next/no-img-element -- covers come from the API with long cache headers; next/image would proxy them again */

import { Music2 } from "lucide-react";

import { cn } from "@/lib/utils";

import { mediaUrl } from "../services/medien-service";

// fine grooves + a darker run-out area; the grooves are round, so the turning is carried by the cover label and the label hole
const GROOVES =
  "radial-gradient(circle at center, transparent 0 31%, rgba(0,0,0,0.85) 31.5% 33%, transparent 33.5%), " +
  "repeating-radial-gradient(circle at center, #141414 0 1.1px, #232323 1.5px 2.4px), #121212";
// the light falling on the record: it does NOT turn (that is what makes a real record look like it is turning)
const SHEEN =
  "conic-gradient(from 20deg, transparent 0deg 18deg, rgba(255,255,255,0.16) 32deg, transparent 52deg 196deg, rgba(255,255,255,0.10) 212deg, transparent 232deg 360deg)";

interface Props {
  cover: string | null | undefined;
  spinning: boolean;
  className?: string;
  /** seconds per turn (33⅓ rpm ≈ 1.8 s; a little slower reads calmer on screen) */
  speed?: number;
  testId?: string;
}

/** A vinyl record with the song's cover as its label. It turns while the music plays and stops where it is on pause (the CSS animation
 * is paused, not removed, so it continues from the same angle). Respects "reduce motion". */
export default function VinylDisc({ cover, spinning, className, speed = 2.4, testId }: Props) {
  return (
    <div className={cn("relative aspect-square select-none", className)} data-testid={testId} data-spinning={spinning ? "1" : "0"}>
      <div
        className="absolute inset-0 animate-spin rounded-full shadow-[0_18px_50px_rgba(0,0,0,0.55)] ring-1 ring-white/10 motion-reduce:animate-none"
        style={{ background: GROOVES, animationDuration: `${speed}s`, animationPlayState: spinning ? "running" : "paused" }}
        data-role="vinyl-spin"
      >
        <div className="absolute inset-[31%] overflow-hidden rounded-full ring-2 ring-black/70">
          {cover ? (
            <img src={mediaUrl(cover)} alt="" draggable={false} className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-fuchsia-600 via-violet-700 to-indigo-800 text-white/90">
              <Music2 className="h-1/2 w-1/2" aria-hidden />
            </div>
          )}
        </div>
        {/* a small mark on the label so the turning is visible even on a plain cover */}
        <div className="absolute left-1/2 top-[33%] h-[3%] w-[3%] -translate-x-1/2 rounded-full bg-white/70 mix-blend-overlay" />
        {/* spindle hole */}
        <div className="absolute left-1/2 top-1/2 h-[4%] w-[4%] -translate-x-1/2 -translate-y-1/2 rounded-full bg-zinc-300 ring-2 ring-black/80" />
      </div>
      <div className="pointer-events-none absolute inset-0 rounded-full" style={{ background: SHEEN }} />
      <div className="pointer-events-none absolute inset-[3%] rounded-full ring-1 ring-white/5" />
    </div>
  );
}
