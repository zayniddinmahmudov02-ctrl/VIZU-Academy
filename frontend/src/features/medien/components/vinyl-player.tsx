"use client";

/* eslint-disable @next/next/no-img-element -- covers come from the API with long cache headers; next/image would proxy them again */

import { Dialog } from "@base-ui/react/dialog";
import { ChevronDown, Heart, Loader2, Pause, Play, Repeat, Repeat1, Shuffle, SkipBack, SkipForward, Volume2, VolumeX, X } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import { songSeconds } from "../lib/player-view";
import { mediaUrl } from "../services/medien-service";
import { currentSong, usePlayerStore, viewOf } from "../store/player-store";
import { formatTime } from "./global-audio-player";
import { usePlayerFavorite } from "./player-favorite";
import VinylDisc from "./vinyl-disc";

const ERRORS = ["PURCHASE_REQUIRED", "NOT_FOUND", "FILE_MISSING", "PLAYBACK_FAILED"];

/** The tone arm: rests beside the record while paused, swings onto it while the music plays. */
function ToneArm({ playing }: { playing: boolean }) {
  return (
    <svg viewBox="0 0 100 230" aria-hidden data-testid="vinyl-arm" data-down={playing ? "1" : "0"}
         className="pointer-events-none absolute -right-[7%] -top-[6%] h-[72%] w-[31%] drop-shadow-[0_6px_10px_rgba(0,0,0,0.55)] transition-transform duration-700 ease-out motion-reduce:transition-none"
         style={{ transformOrigin: "72% 9%", transform: `rotate(${playing ? 0 : -26}deg)` }}>
      <circle cx="72" cy="20" r="17" fill="#a1a1aa" />
      <circle cx="72" cy="20" r="8" fill="#3f3f46" />
      <path d="M72 20 L64 120 L34 196" fill="none" stroke="#d4d4d8" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" />
      <rect x="20" y="190" width="26" height="16" rx="3" transform="rotate(28 33 198)" fill="#e4e4e7" />
    </svg>
  );
}

function RoundBtn({ label, onClick, children, testId, active, className, ...rest }:
  { label: string; onClick: () => void; children: React.ReactNode; testId: string; active?: boolean; className?: string } & Record<string, unknown>) {
  return (
    <button type="button" aria-label={label} title={label} onClick={onClick} data-testid={testId} aria-pressed={active}
            className={cn("flex h-[44px] w-[44px] shrink-0 items-center justify-center rounded-full transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/70",
              active ? "bg-white/20 text-white" : "text-white/80 hover:bg-white/10 hover:text-white", className)} {...(rest as object)}>
      {children}
    </button>
  );
}

/** The large player: a turning vinyl record with the cover, title, artist, progress, play / pause, previous / next, shuffle, repeat,
 * volume, favourite. "Verkleinern" (or Escape / a click outside) only closes the window — the music keeps playing; X stops the music
 * and empties the player. It drives the one global <audio> through the player store, like every other control. */
export default function VinylPlayer() {
  const { t } = useTranslation();
  const open = usePlayerStore((s) => viewOf(s).large);
  const song = usePlayerStore((s) => currentSong(s));
  const playing = usePlayerStore((s) => s.playing);
  const loading = usePlayerStore((s) => s.loading);
  const error = usePlayerStore((s) => s.error);
  const currentTime = usePlayerStore((s) => s.currentTime);
  const duration = usePlayerStore((s) => s.duration);
  const volume = usePlayerStore((s) => s.volume);
  const muted = usePlayerStore((s) => s.muted);
  const shuffle = usePlayerStore((s) => s.shuffle);
  const repeat = usePlayerStore((s) => s.repeat);
  const toggleFavorite = usePlayerFavorite();
  const store = usePlayerStore.getState;

  if (!song) return null;
  const total = songSeconds(duration, song.duration_ms);

  return (
    <Dialog.Root open={open} onOpenChange={(next) => { if (!next) store().closeLargePlayer(); }}>
      <Dialog.Portal>
        <Dialog.Backdrop className="fixed inset-0 z-[70] bg-black/70 backdrop-blur-sm" />
        <Dialog.Popup
          data-testid="vinyl-player" data-playing={playing ? "1" : "0"}
          className="fixed inset-0 z-[71] flex flex-col overflow-y-auto overflow-x-hidden bg-zinc-950 text-white outline-none sm:inset-auto sm:left-1/2 sm:top-1/2 sm:max-h-[94vh] sm:w-[min(94vw,58rem)] sm:-translate-x-1/2 sm:-translate-y-1/2 sm:rounded-[2rem] sm:shadow-[0_30px_90px_rgba(0,0,0,0.6)] sm:ring-1 sm:ring-white/10">
          {/* the cover, blurred, as the room light */}
          <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
            {song.cover_url && <img src={mediaUrl(song.cover_url)} alt="" className="h-full w-full scale-125 object-cover opacity-40 blur-3xl" />}
            <div className="absolute inset-0 bg-gradient-to-b from-fuchsia-900/40 via-zinc-950/70 to-zinc-950" />
          </div>

          <div className="relative flex items-center justify-between gap-3 px-3 pb-1 pt-[calc(0.75rem+env(safe-area-inset-top))] sm:px-5 sm:pt-5">
            <RoundBtn label={t("medien.playerMinimize")} onClick={() => store().closeLargePlayer()} testId="vinyl-minimize"><ChevronDown size={24} /></RoundBtn>
            <Dialog.Title className="truncate text-xs font-bold uppercase tracking-[0.2em] text-white/70">
              {playing ? t("medien.playerNowPlaying") : t("medien.playerPaused")}
            </Dialog.Title>
            <RoundBtn label={t("medien.playerStop")} onClick={() => store().stop()} testId="vinyl-close"><X size={22} /></RoundBtn>
          </div>

          <div className="relative flex flex-1 flex-col items-center justify-center gap-7 px-6 pb-[calc(1.5rem+env(safe-area-inset-bottom))] pt-3 sm:px-10 sm:pb-10 lg:grid lg:grid-cols-2 lg:items-center lg:gap-12">
            <div className="relative w-[min(74vw,21rem)] sm:w-[22rem] lg:w-full lg:max-w-[25rem] lg:justify-self-center">
              <VinylDisc cover={song.cover_url} spinning={playing && !loading} className="w-full" testId="vinyl-disc" />
              <ToneArm playing={playing} />
            </div>

            <div className="flex w-full max-w-md flex-col gap-5 lg:max-w-none">
              <div className="flex items-start gap-3">
                <div className="min-w-0 flex-1">
                  <h2 className="line-clamp-2 text-2xl font-extrabold leading-tight sm:text-3xl" data-testid="vinyl-title">{song.title}</h2>
                  <p className="mt-1 truncate text-sm text-white/70 sm:text-base" data-testid="vinyl-artist">
                    {error ? t(`medien.err.${ERRORS.includes(error) ? error : "GENERIC"}`) : [song.artist, song.album].filter(Boolean).join(" · ")}
                  </p>
                </div>
                <RoundBtn label={t("medien.playerFavorite")} active={song.favorite} onClick={toggleFavorite} testId="vinyl-favorite" className={song.favorite ? "text-pink-400" : ""}>
                  <Heart size={20} className={song.favorite ? "fill-current" : ""} />
                </RoundBtn>
              </div>

              <div>
                <input type="range" min={0} max={Math.max(1, Math.floor(total))} step={1} value={Math.min(Math.floor(currentTime), Math.floor(total) || 0)}
                       onChange={(e) => store().seek(Number(e.target.value))} aria-label={t("medien.playerSeek")} data-testid="vinyl-progress"
                       className="h-1.5 w-full cursor-pointer accent-white" />
                <div className="mt-1 flex justify-between text-xs tabular-nums text-white/60">
                  <span data-testid="vinyl-time">{formatTime(currentTime)}</span>
                  <span data-testid="vinyl-duration">{formatTime(total)}</span>
                </div>
              </div>

              <div className="flex items-center justify-between gap-1 sm:justify-center sm:gap-4" data-testid="vinyl-controls">
                <RoundBtn label={t("medien.playerShuffle")} active={shuffle} onClick={() => store().toggleShuffle()} testId="vinyl-shuffle"><Shuffle size={18} /></RoundBtn>
                <RoundBtn label={t("medien.playerPrev")} onClick={() => store().prev()} testId="vinyl-prev" className="h-[52px] w-[52px]"><SkipBack size={26} className="fill-current" /></RoundBtn>
                <button type="button" onClick={() => store().toggle()} aria-label={playing ? t("medien.playerPause") : t("medien.playerPlay")} data-testid="vinyl-play"
                        className="flex h-[68px] w-[68px] shrink-0 items-center justify-center rounded-full bg-white text-zinc-900 shadow-lg transition hover:scale-105 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-white/40">
                  {loading ? <Loader2 size={28} className="animate-spin" /> : playing ? <Pause size={30} className="fill-current" /> : <Play size={30} className="translate-x-0.5 fill-current" />}
                </button>
                <RoundBtn label={t("medien.playerNext")} onClick={() => store().next()} testId="vinyl-next" className="h-[52px] w-[52px]"><SkipForward size={26} className="fill-current" /></RoundBtn>
                <RoundBtn label={t("medien.playerRepeat")} active={repeat !== "off"} onClick={() => store().cycleRepeat()} testId="vinyl-repeat" data-mode={repeat}>
                  {repeat === "one" ? <Repeat1 size={18} /> : <Repeat size={18} />}
                </RoundBtn>
              </div>

              <div className="flex items-center gap-2">
                <RoundBtn label={muted || volume === 0 ? t("medien.playerUnmute") : t("medien.playerMute")} onClick={() => store().toggleMute()} testId="vinyl-mute">
                  {muted || volume === 0 ? <VolumeX size={18} /> : <Volume2 size={18} />}
                </RoundBtn>
                <input type="range" min={0} max={1} step={0.05} value={muted ? 0 : volume} onChange={(e) => store().setVolume(Number(e.target.value))}
                       aria-label={t("medien.playerVolume")} data-testid="vinyl-volume" className="h-1.5 flex-1 cursor-pointer accent-white" />
              </div>
            </div>
          </div>
        </Dialog.Popup>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
