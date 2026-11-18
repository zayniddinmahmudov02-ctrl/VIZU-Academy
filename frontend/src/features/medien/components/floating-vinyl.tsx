"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import { Loader2, Maximize2, Pause, Play, SkipBack, SkipForward, X } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import { isExamPath, ringOffset, songSeconds } from "../lib/player-view";
import { currentSong, isFloatingPlayerVisible, usePlayerStore } from "../store/player-store";
import { formatTime } from "./global-audio-player";
import VinylDisc from "./vinyl-disc";

const RING_R = 47;
const RING_C = 2 * Math.PI * RING_R;

function PanelBtn({ label, onClick, children, testId, primary }: { label: string; onClick: () => void; children: React.ReactNode; testId: string; primary?: boolean }) {
  return (
    <button type="button" aria-label={label} title={label} onClick={onClick} data-testid={testId}
            className={cn("flex h-[44px] w-[44px] shrink-0 items-center justify-center rounded-full transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-blue/60",
              primary ? "bg-accent-blue text-white shadow-md hover:opacity-90" : "text-text-secondary hover:bg-surface-hover")}>
      {children}
    </button>
  );
}

/** The floating vinyl disc on every student page except Medien → Musik: bottom right, above the Global Chat button (and, on a phone, above
 * the Hören dock of a running Multilevel exam). It turns while the music plays and stops on pause; a ring shows the progress. A tap opens
 * a small panel (title, artist, progress, previous / play-pause / next, the large player, X). X stops the music for good. */
export default function FloatingVinyl() {
  const { t } = useTranslation();
  const pathname = usePathname();
  const ref = useRef<HTMLDivElement>(null);
  const visible = usePlayerStore(isFloatingPlayerVisible);
  const song = usePlayerStore((s) => currentSong(s));
  const playing = usePlayerStore((s) => s.playing);
  const loading = usePlayerStore((s) => s.loading);
  const currentTime = usePlayerStore((s) => s.currentTime);
  const duration = usePlayerStore((s) => s.duration);
  const panelOpen = usePlayerStore((s) => s.isFloatingPanelOpen);
  const store = usePlayerStore.getState;

  // a tap outside or Escape closes the panel (the music goes on)
  useEffect(() => {
    if (!panelOpen) return;
    const onDown = (e: PointerEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) store().setFloatingPanel(false); };
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") store().setFloatingPanel(false); };
    document.addEventListener("pointerdown", onDown);
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("pointerdown", onDown); document.removeEventListener("keydown", onKey); };
  }, [panelOpen, store]);

  if (!visible || !song) return null;
  const total = songSeconds(duration, song.duration_ms);

  return (
    <div ref={ref} data-testid="floating-vinyl" data-playing={playing ? "1" : "0"}
         className={cn("fixed right-4 z-40 sm:right-6",
           isExamPath(pathname) ? "bottom-[calc(13.5rem+env(safe-area-inset-bottom))] sm:bottom-[calc(5.25rem+env(safe-area-inset-bottom))]" : "bottom-[calc(5.25rem+env(safe-area-inset-bottom))]")}>
      {panelOpen && (
        <div role="dialog" aria-label={t("medien.playerControls")} data-testid="floating-panel"
             className="absolute bottom-full right-0 mb-3 w-[min(20rem,calc(100vw-2rem))] rounded-2xl bg-surface-card p-3 shadow-[var(--shadow-lg)] ring-1 ring-surface-border">
          <div className="flex items-center gap-3">
            <button type="button" onClick={() => store().openLargePlayer()} aria-label={t("medien.playerExpand")} data-testid="floating-cover"
                    className="h-12 w-12 shrink-0 rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-blue/60">
              <VinylDisc cover={song.cover_url} spinning={playing && !loading} className="h-full w-full" />
            </button>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-bold text-text-primary" data-testid="floating-title">{song.title}</p>
              <p className="truncate text-xs text-text-muted" data-testid="floating-artist">{song.artist ?? ""}</p>
            </div>
            <PanelBtn label={t("medien.playerStop")} onClick={() => store().stop()} testId="floating-close"><X size={18} /></PanelBtn>
          </div>
          <div className="mt-2">
            <input type="range" min={0} max={Math.max(1, Math.floor(total))} step={1} value={Math.min(Math.floor(currentTime), Math.floor(total) || 0)}
                   onChange={(e) => store().seek(Number(e.target.value))} aria-label={t("medien.playerSeek")} data-testid="floating-progress"
                   className="h-1.5 w-full cursor-pointer accent-[var(--color-accent-blue,#2563eb)]" />
            <div className="flex justify-between text-[11px] tabular-nums text-text-muted">
              <span data-testid="floating-time">{formatTime(currentTime)}</span>
              <span>{formatTime(total)}</span>
            </div>
          </div>
          <div className="mt-1 flex items-center justify-center gap-2">
            <PanelBtn label={t("medien.playerPrev")} onClick={() => store().prev()} testId="floating-prev"><SkipBack size={20} /></PanelBtn>
            <PanelBtn label={playing ? t("medien.playerPause") : t("medien.playerPlay")} onClick={() => store().toggle()} testId="floating-play" primary>
              {loading ? <Loader2 size={20} className="animate-spin" /> : playing ? <Pause size={20} /> : <Play size={20} className="translate-x-px" />}
            </PanelBtn>
            <PanelBtn label={t("medien.playerNext")} onClick={() => store().next()} testId="floating-next"><SkipForward size={20} /></PanelBtn>
            <PanelBtn label={t("medien.playerExpand")} onClick={() => store().openLargePlayer()} testId="floating-expand"><Maximize2 size={18} /></PanelBtn>
          </div>
        </div>
      )}

      <button type="button" onClick={() => store().setFloatingPanel(!panelOpen)} onDoubleClick={() => store().openLargePlayer()}
              aria-label={`${t("medien.playerControls")}: ${song.title}`} aria-expanded={panelOpen} data-testid="floating-disc"
              className="relative block h-14 w-14 rounded-full focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-accent-blue/40 sm:h-16 sm:w-16">
        <svg viewBox="0 0 100 100" className="pointer-events-none absolute -inset-1.5 h-[calc(100%+0.75rem)] w-[calc(100%+0.75rem)] -rotate-90" aria-hidden>
          <circle cx="50" cy="50" r={RING_R} fill="none" stroke="currentColor" strokeWidth="4" className="text-surface-card" />
          <circle cx="50" cy="50" r={RING_R} fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="round" className="text-accent-blue"
                  strokeDasharray={RING_C} strokeDashoffset={ringOffset(currentTime, total, RING_C)} data-testid="floating-ring" />
        </svg>
        <VinylDisc cover={song.cover_url} spinning={playing && !loading} className="h-full w-full" testId="floating-disc-art" />
        {!playing && (
          <span className="pointer-events-none absolute inset-0 flex items-center justify-center" aria-hidden>
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-black/60 text-white"><Play size={13} className="translate-x-px fill-current" /></span>
          </span>
        )}
      </button>
    </div>
  );
}
