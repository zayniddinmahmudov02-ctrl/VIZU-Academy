"use client";

import { useState } from "react";
import { Bot, Copy, Radar, X } from "lucide-react";

import BattleAvatar from "@/features/battle/components/battle-avatar";
import { GermanFlag, GlassPanel, PointsChip, StageChip } from "@/features/battle/components/battle-ui";
import { msUntil } from "@/features/battle/lib/battle-utils";
import type { MatchPlayer, MatchState } from "@/features/battle/services/battle-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

function Fighter({ player, side, searching = false }: { player: MatchPlayer | null; side: "me" | "opponent"; searching?: boolean }) {
  const blue = side === "me";
  return (
    <div className={cn("flex flex-col items-center text-center", blue ? "animate-[bt-in-left_0.6s_ease-out]" : "animate-[bt-in-right_0.6s_ease-out]")}>
      <div className="relative grid place-items-center">
        <span aria-hidden="true" className={cn("absolute h-40 w-40 rounded-full blur-3xl sm:h-56 sm:w-56", blue ? "bg-[var(--bt-blue)]/40" : "bg-[var(--bt-red)]/40")} />
        {searching ? (
          <div className="relative grid h-[170px] w-[150px] place-items-center overflow-hidden rounded-[40%] bg-[var(--bt-dark)]/80 ring-2 ring-[var(--bt-red)]/60 sm:h-[220px] sm:w-[190px]" data-testid="lobby-searching">
            <Radar className="text-[var(--bt-red)]" size={54} aria-hidden="true" />
            <span aria-hidden="true" className="bt-scan absolute inset-x-0 top-0 h-1/3" />
            <span aria-hidden="true" className="bt-pulse-ring absolute h-24 w-24 rounded-full border-2 border-[var(--bt-red)]" />
          </div>
        ) : (
          <BattleAvatar avatar={player?.avatar ?? "student"} size={190} accent={blue ? "#3984E8" : "#D83B43"} className="relative max-sm:!w-[150px] max-sm:!h-[165px]" title={player?.name} />
        )}
      </div>
      <p className="mt-2 flex items-center gap-2 text-lg font-black"><GermanFlag size={18} />{searching ? "???" : player?.name}</p>
      {!searching && player && (
        <>
          <p className="text-xs font-bold text-[var(--bt-gold)]">{player.rank}</p>
          {!player.is_bot && <PointsChip points={player.points} className="mt-1.5" />}
        </>
      )}
    </div>
  );
}

function VsMark({ big = false }: { big?: boolean }) {
  return (
    <div className={cn("relative grid place-items-center", big ? "h-28 w-28 sm:h-36 sm:w-36" : "h-20 w-20 sm:h-28 sm:w-28")} aria-hidden="true">
      <span className="bt-holo-ring absolute inset-0 rounded-full border-2 border-dashed border-[var(--bt-gold)]/60" />
      <span className="absolute inset-3 rounded-full bg-gradient-to-br from-[var(--bt-blue)] via-[#5a2a6e] to-[var(--bt-red)] shadow-[var(--bt-glow-gold)]" />
      <span className={cn("relative bt-display bt-gold-text", big ? "text-5xl sm:text-6xl" : "text-4xl sm:text-5xl")}>VS</span>
    </div>
  );
}

export function Matchmaking({ match, offsetMs, now, onCancel, onBot, busy }: { match: MatchState; offsetMs: number; now: number; onCancel: () => void; onBot: () => void; busy: boolean }) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  const waited = match.waiting_since ? Math.max(0, Math.floor((now + offsetMs - Date.parse(match.waiting_since)) / 1000)) : 0;
  const isPrivate = match.mode === "private";

  return (
    <div className="mx-auto max-w-5xl pt-2 sm:pt-6" data-testid="battle-matchmaking">
      <div className="text-center">
        <StageChip stage={match.stage} />
        <h1 className="bt-display mt-3 text-3xl sm:text-5xl">{isPrivate ? t("battle.waitingFriend") : t("battle.searching")}</h1>
        {!isPrivate && <p className="mx-auto mt-2 max-w-lg text-sm text-white/70">{t("battle.searchingHint")}</p>}
        <p className="mt-2 font-mono text-lg font-black tabular-nums text-[var(--bt-gold)]" aria-live="off">{String(Math.floor(waited / 60)).padStart(2, "0")}:{String(waited % 60).padStart(2, "0")}</p>
      </div>

      <div className="mt-6 grid grid-cols-[1fr_auto_1fr] items-center gap-2 sm:gap-6">
        <Fighter player={match.me} side="me" />
        <VsMark />
        <Fighter player={match.opponent} side="opponent" searching />
      </div>

      {isPrivate && match.room_code && (
        <GlassPanel className="mx-auto mt-6 max-w-sm p-4 text-center" data-testid="lobby-room">
          <p className="text-sm text-white/70">{t("battle.shareCode")}</p>
          <p className="mt-1 font-mono text-4xl font-black tracking-[0.35em] text-[var(--bt-gold)]" data-testid="lobby-room-code">{match.room_code}</p>
          <button type="button" onClick={() => { navigator.clipboard?.writeText(match.room_code ?? "").then(() => setCopied(true)).catch(() => undefined); }}
                  className="mt-2 inline-flex items-center gap-1.5 rounded-lg bg-white/10 px-3 py-1.5 text-xs font-bold hover:bg-white/15">
            <Copy size={13} aria-hidden="true" /> {copied ? t("battle.copied") : t("battle.copy")}
          </button>
        </GlassPanel>
      )}

      <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
        {!isPrivate && waited >= 15 && (
          <button type="button" onClick={onBot} disabled={busy} data-testid="lobby-bot"
                  className="inline-flex h-12 items-center gap-2 rounded-2xl bg-[var(--bt-blue)] px-5 text-sm font-black shadow-[var(--bt-glow-blue)] disabled:opacity-50">
            <Bot size={18} aria-hidden="true" /> {t("battle.botInstead")}
          </button>
        )}
        <button type="button" onClick={onCancel} disabled={busy} data-testid="lobby-cancel"
                className="bt-glass inline-flex h-12 items-center gap-2 rounded-2xl px-5 text-sm font-bold hover:bg-white/10 disabled:opacity-50">
          <X size={18} aria-hidden="true" /> {t("battle.cancel")}
        </button>
      </div>
    </div>
  );
}

/** "Opponent found" → VS → 3 · 2 · 1 · LOS! */
export function VersusCountdown({ match, offsetMs, now }: { match: MatchState; offsetMs: number; now: number }) {
  const { t } = useTranslation();
  const left = msUntil(match.countdown_ends_at, offsetMs, now);
  const n = Math.ceil(left / 1000);
  return (
    <div className="mx-auto max-w-5xl pt-4 sm:pt-10" data-testid="battle-countdown">
      <p className="bt-display text-center text-2xl text-[var(--bt-gold)] sm:text-4xl">{t("battle.opponentFound")}</p>
      <div className="mt-6 grid grid-cols-[1fr_auto_1fr] items-center gap-2 sm:gap-6">
        <Fighter player={match.me} side="me" />
        <VsMark big />
        <Fighter player={match.opponent} side="opponent" />
      </div>
      <p key={n} className="bt-display bt-pop mt-6 text-center text-7xl text-white drop-shadow-[0_0_30px_rgba(242,196,91,0.8)] sm:text-8xl" aria-live="assertive">
        {n > 0 ? n : t("battle.go")}
      </p>
    </div>
  );
}
