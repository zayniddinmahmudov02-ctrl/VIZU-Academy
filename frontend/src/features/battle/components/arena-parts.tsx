"use client";

import { useState } from "react";
import { Check, Clock3, ImageOff, X } from "lucide-react";

import { API_URL } from "@/constants/api";
import PlayerAvatar from "@/features/battle/components/player-avatar";
import { GermanFlag, PointsChip } from "@/features/battle/components/battle-ui";
import { apiAsset, optionState, type OptionState } from "@/features/battle/lib/battle-utils";
import type { MatchPlayer, MatchState, RoundView } from "@/features/battle/services/battle-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

export function PlayerPanel({ player, side, compact = false, answered }: { player: MatchPlayer | null; side: "me" | "opponent"; compact?: boolean; answered?: boolean }) {
  const { t } = useTranslation();
  const blue = side === "me";
  const ring = blue ? "ring-[var(--bt-blue)]" : "ring-[var(--bt-red)]";
  if (compact) {
    return (
      <div className={cn("flex min-w-0 items-center gap-2", !blue && "flex-row-reverse text-right")} data-testid={`arena-${side}`}>
        <span className={cn("relative grid h-11 w-11 shrink-0 place-items-center overflow-hidden rounded-full bg-[var(--bt-dark)] ring-2", ring)}>
          {player && <PlayerAvatar player={player} size={44} round />}
          {answered && <span className="absolute inset-0 grid place-items-center bg-black/40"><Check size={18} className="text-[var(--bt-gold)]" /></span>}
        </span>
        <span className="min-w-0">
          <span className="block truncate text-xs font-black">{side === "me" ? t("battle.you") : player?.name ?? "…"}</span>
          <span className={cn("block text-lg font-black leading-none", blue ? "text-[var(--bt-blue)]" : "text-[var(--bt-red)]")}>{player?.score ?? 0}</span>
        </span>
      </div>
    );
  }
  return (
    <div className={cn("bt-glass relative flex flex-col items-center rounded-3xl p-4 text-center", blue ? "shadow-[var(--bt-glow-blue)]" : "shadow-[var(--bt-glow-red)]")} data-testid={`arena-${side}`}>
      <span className={cn("absolute inset-x-6 top-0 h-1 rounded-b-full", blue ? "bg-[var(--bt-blue)]" : "bg-[var(--bt-red)]")} aria-hidden="true" />
      {player ? <PlayerAvatar player={player} size={150} accent={blue ? "#3984E8" : "#D83B43"} /> : <div className="h-[165px]" />}
      <p className="mt-1 flex max-w-full items-center gap-2 truncate text-base font-black"><GermanFlag size={18} />{player?.name ?? "…"}</p>
      <p className="text-xs font-bold text-[var(--bt-gold)]">{player?.rank}</p>
      {player && !player.is_bot && <PointsChip points={player.points} className="mt-2" />}
      <p className={cn("mt-3 text-4xl font-black tabular-nums", blue ? "text-[var(--bt-blue)]" : "text-[var(--bt-red)]")}>{player?.score ?? 0}</p>
      {answered !== undefined && side === "opponent" && (
        <p className={cn("mt-1 text-[11px] font-bold", answered ? "text-[var(--bt-gold)]" : "text-white/55")}>{answered ? t("battle.opponentAnswered") : t("battle.opponentThinking")}</p>
      )}
    </div>
  );
}

export function TimerRing({ msLeft, totalMs, size = 64 }: { msLeft: number; totalMs: number; size?: number }) {
  const r = 26;
  const c = 2 * Math.PI * r;
  const frac = Math.max(0, Math.min(1, msLeft / totalMs));
  const urgent = msLeft <= 3000;
  return (
    <div className="relative grid place-items-center" style={{ width: size, height: size }} role="timer" aria-label={`${Math.ceil(msLeft / 1000)} s`} data-testid="arena-timer">
      <svg viewBox="0 0 64 64" width={size} height={size} className="-rotate-90">
        <circle cx="32" cy="32" r={r} fill="rgba(16,29,53,0.7)" stroke="rgba(255,255,255,0.15)" strokeWidth="5" />
        <circle cx="32" cy="32" r={r} fill="none" stroke={urgent ? "#D83B43" : "#F2C45B"} strokeWidth="5" strokeLinecap="round" strokeDasharray={c}
                strokeDashoffset={c * (1 - frac)} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      </svg>
      <span className={cn("absolute text-lg font-black tabular-nums", urgent && "text-[var(--bt-red)]")}>{Math.ceil(msLeft / 1000)}</span>
    </div>
  );
}

export function RoundDots({ match }: { match: MatchState }) {
  const { t } = useTranslation();
  return (
    <div className="flex items-center justify-center gap-1.5" aria-label={t("battle.matchProgress")} data-testid="arena-progress">
      {Array.from({ length: match.rounds }, (_, i) => {
        const h = match.history[i];
        const current = match.round?.no === i + 1;
        return (
          <span key={i} className={cn("h-2.5 rounded-full transition-all", current ? "w-6 bg-white" : "w-2.5",
            !current && (h?.me === true ? "bg-[var(--bt-blue)]" : h?.me === false ? "bg-[var(--bt-red)]" : "bg-white/20"))} />
        );
      })}
    </div>
  );
}

const OPTION_STYLE: Record<OptionState, string> = {
  idle: "bg-white text-[var(--bt-navy)] ring-[#dfe5f0] hover:ring-[var(--bt-blue)] hover:shadow-[0_10px_24px_-12px_rgba(57,132,232,0.8)]",
  selected: "bg-[var(--bt-blue)] text-white ring-[var(--bt-blue)] shadow-[var(--bt-glow-blue)]",
  correct: "bg-[#1fae6b] text-white ring-[#1fae6b] shadow-[0_0_0_1px_rgba(31,174,107,0.5),0_10px_30px_-10px_rgba(31,174,107,0.9)] bt-pop",
  wrong: "bg-[var(--bt-red)] text-white ring-[var(--bt-red)] bt-shake",
  missed: "bg-white text-[#178a55] ring-2 ring-[#1fae6b]",
  dimmed: "bg-white/70 text-[var(--bt-navy)]/50 ring-transparent",
};

export function QuestionCard({ round, stage, msLeft, totalMs, pending, onAnswer, opponentChoice }: {
  round: RoundView;
  stage: string;
  msLeft: number;
  totalMs: number;
  pending: number | null;
  onAnswer: (choice: number) => void;
  opponentChoice: number | null;
}) {
  const { t, language } = useTranslation();
  const [loaded, setLoaded] = useState<string | null>(null);
  const [failed, setFailed] = useState<string | null>(null);
  const src = apiAsset(round.image_url, API_URL);
  const imgKey = `${round.no}`;
  const myChoice = round.my_answer?.choice ?? pending;
  const answered = round.my_answer !== null || pending !== null;
  const timedOut = round.phase === "reveal" && round.my_answer?.choice === null;

  return (
    <article className="bt-card-light relative mx-auto w-full max-w-[640px] overflow-hidden rounded-[28px] p-3 sm:p-5 landscape-short:max-w-none landscape-short:p-2.5" data-testid="question-card" aria-live="polite">
      <div className="mb-3 flex items-center justify-between gap-2 landscape-short:mb-2">
        <span className="rounded-full bg-[var(--bt-navy)] px-3 py-1 text-[11px] font-extrabold uppercase tracking-wider text-white">
          {round.category ? (language === "uz" ? round.category.uz : round.category.de) : "Wortschatz"}
        </span>
        <span className="rounded-full bg-[var(--bt-gold)] px-3 py-1 text-[11px] font-black text-[var(--bt-navy)]">CEFR {stage}</span>
      </div>

      <div className="landscape-short:grid landscape-short:grid-cols-2 landscape-short:items-center landscape-short:gap-3">
      <div className="relative aspect-[4/3] w-full overflow-hidden rounded-2xl bg-[#e9eef6] ring-1 ring-[#dfe5f0] max-sm:aspect-[5/4]">
        {loaded !== imgKey && failed !== imgKey && <div className="bt-skeleton absolute inset-0" />}
        {failed === imgKey ? (
          <div className="absolute inset-0 grid place-items-center text-center text-sm font-semibold text-[var(--bt-navy)]/60" data-testid="question-image-error">
            <span className="flex flex-col items-center gap-2"><ImageOff size={28} />{t("battle.imageError")}</span>
          </div>
        ) : (
          // eslint-disable-next-line @next/next/no-img-element -- signed, short-lived URL from the battle server
          <img key={imgKey} src={src} alt="" draggable={false} onLoad={() => setLoaded(imgKey)} onError={() => setFailed(imgKey)} data-testid="question-image"
               className={cn("absolute inset-0 h-full w-full select-none object-contain transition-opacity duration-300", loaded === imgKey ? "opacity-100" : "opacity-0")} />
        )}
        {round.phase === "reveal" && round.my_answer && (
          <div className={cn("absolute inset-x-0 bottom-0 flex items-center justify-center gap-2 py-2 text-sm font-black text-white bt-pop",
            round.my_answer.correct ? "bg-[#1fae6b]/90" : "bg-[var(--bt-red)]/90")} data-testid="question-feedback">
            {timedOut ? <><Clock3 size={16} />{t("battle.timeUp")}</> : round.my_answer.correct ? <><Check size={16} />{t("battle.correct")} +{round.my_answer.score}</> : <><X size={16} />{t("battle.wrong")}</>}
          </div>
        )}
        {round.phase === "question" && round.my_answer?.correct && (
          <span className="bt-float-up absolute right-3 top-3 rounded-full bg-[#1fae6b] px-3 py-1 text-sm font-black text-white">+{round.my_answer.score}</span>
        )}
      </div>

      <div>
      <div className="my-3 text-center sm:my-4 landscape-short:mt-0 landscape-short:mb-2">
        <h2 className="text-xl font-black tracking-tight sm:text-2xl">{t("battle.question")}</h2>
        {language === "uz" && <p className="text-xs font-semibold text-[var(--bt-navy)]/55">{t("battle.questionUz")}</p>}
      </div>

      <div className="grid grid-cols-2 gap-2 sm:gap-3">
        {round.options.map((label, i) => {
          const state = optionState(i, round.phase, myChoice, round.correct);
          return (
            <button key={`${round.no}-${i}`} type="button" disabled={answered || round.phase !== "question" || msLeft <= 0} onClick={() => onAnswer(i)}
                    data-testid={`answer-${i}`} data-state={state} aria-pressed={myChoice === i}
                    className={cn("bt-option relative flex min-h-[58px] items-center gap-2 rounded-2xl px-3 py-3 text-left text-[15px] font-extrabold ring-1 sm:min-h-[66px] sm:px-4 sm:text-lg landscape-short:min-h-[46px] landscape-short:py-2 landscape-short:text-[15px]", OPTION_STYLE[state])}>
              <span className={cn("grid h-7 w-7 shrink-0 place-items-center rounded-lg text-xs font-black max-sm:hidden",
                state === "idle" ? "bg-[var(--bt-navy)]/8 text-[var(--bt-navy)]/60" : "bg-white/25")}>{"ABCD"[i]}</span>
              <span className="min-w-0 break-words leading-tight">{label}</span>
              {round.phase === "reveal" && opponentChoice === i && (
                <span className="absolute -right-1 -top-2 rounded-full bg-[var(--bt-red)] px-1.5 text-[10px] font-black text-white ring-2 ring-white" title="Gegner">VS</span>
              )}
            </button>
          );
        })}
      </div>

      {round.phase === "reveal" && round.translation && (
        <p className="mt-3 text-center text-sm font-semibold text-[var(--bt-navy)]/70" data-testid="question-translation">
          {t("battle.meaning")}: <b className="text-[var(--bt-navy)]">{round.translation}</b>
        </p>
      )}
      </div>
      </div>
      <span className="sr-only">{Math.ceil(msLeft / 1000)} s / {Math.round(totalMs / 1000)} s</span>
    </article>
  );
}
