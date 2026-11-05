"use client";

import { useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Crown } from "lucide-react";

import PlayerAvatar from "@/features/battle/components/player-avatar";
import BattleScene from "@/features/battle/components/battle-scene";
import { useBattleLowFx } from "@/features/battle/components/battle-shell";
import { ErrorState, GermanFlag, GlassPanel, LoadingState, PointsChip, RankBadge } from "@/features/battle/components/battle-ui";
import { useBattleHome } from "@/features/battle/hooks/use-battle-home";
import { getLeaderboard, STAGES, type Stage } from "@/features/battle/services/battle-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

export default function LeaderboardView() {
  const { t } = useTranslation();
  const lowFx = useBattleLowFx();
  const home = useBattleHome();
  const [stage, setStage] = useState<Stage | "">("");
  const [page, setPage] = useState(1);
  const q = useQuery({ queryKey: ["battle-leaderboard", stage, page], queryFn: () => getLeaderboard(stage, page), placeholderData: keepPreviousData });
  const theme = home.data?.themes.find((th) => th.stage === (stage || home.data?.rank.stage)) ?? null;
  const pages = q.data ? Math.max(1, Math.ceil(q.data.total / q.data.page_size)) : 1;
  const podium = page === 1 ? (q.data?.items.slice(0, 3) ?? []) : [];

  return (
    <>
      <BattleScene theme={theme} lowFx={lowFx} />
      <div className="mx-auto max-w-4xl space-y-5" data-testid="battle-leaderboard">
        <h1 className="bt-display text-4xl sm:text-5xl">{t("battle.navLeaderboard")}</h1>
        <div className="flex gap-2 overflow-x-auto pb-1" role="tablist">
          {(["", ...STAGES] as const).map((s) => (
            <button key={s || "all"} type="button" role="tab" aria-selected={stage === s} onClick={() => { setStage(s); setPage(1); }} data-testid={`leaderboard-tab-${s || "all"}`}
                    className={cn("shrink-0 rounded-xl px-4 py-2 text-sm font-black ring-1 transition", stage === s ? "bg-[var(--bt-gold)] text-[var(--bt-navy)] ring-[var(--bt-gold)]" : "bt-glass ring-white/10 hover:bg-white/10")}>
              {s || t("battle.allStages")}
            </button>
          ))}
        </div>

        {q.isLoading ? <LoadingState /> : q.isError || !q.data ? <ErrorState onRetry={() => q.refetch()} /> : (
          <>
            {podium.length > 0 && (
              <div className="grid grid-cols-3 items-end gap-2 sm:gap-4">
                {[podium[1], podium[0], podium[2]].map((p, i) => p && (
                  <GlassPanel key={p.position} className={cn("flex flex-col items-center p-3 text-center sm:p-4", i === 1 && "pb-6 shadow-[var(--bt-glow-gold)]")}>
                    {p.position === 1 && <Crown className="text-[var(--bt-gold)]" size={22} aria-hidden="true" />}
                    <PlayerAvatar player={p} size={i === 1 ? 120 : 90} accent={i === 1 ? "#F2C45B" : "#3984E8"} animated={i === 1} />
                    <p className="mt-1 max-w-full truncate text-sm font-black">{p.name}</p>
                    <p className="text-2xl font-black text-[var(--bt-gold)]">#{p.position}</p>
                    <p className="text-xs font-bold text-white/70">{p.points} BP</p>
                  </GlassPanel>
                ))}
              </div>
            )}

            <GlassPanel className="overflow-hidden">
              {q.data.items.length === 0 ? <p className="p-6 text-center text-sm text-white/65">{t("battle.emptyLeaderboard")}</p> : (
                <ol>
                  {q.data.items.map((row) => (
                    <li key={`${row.position}-${row.name}`} className={cn("flex items-center gap-3 border-b border-white/5 px-3 py-2.5 sm:px-5", row.me && "bg-[var(--bt-blue)]/20")}>
                      <span className={cn("w-8 text-center text-base font-black", row.position <= 3 ? "text-[var(--bt-gold)]" : "text-white/60")}>{row.position}</span>
                      <span className="grid h-10 w-10 shrink-0 place-items-center overflow-hidden rounded-full bg-[var(--bt-dark)] ring-1 ring-white/15">
                        <PlayerAvatar player={row} size={40} round />
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="flex items-center gap-1.5 truncate text-sm font-black"><GermanFlag size={14} />{row.name}</span>
                        <span className="text-[11px] font-semibold text-white/60">{row.rank} · {row.wins} {t("battle.wins")} · {row.matches} {t("battle.matchesShort")}</span>
                      </span>
                      <RankBadge stage={row.stage} tier={0} size={28} glow={false} className="max-sm:hidden" />
                      <span className="text-sm font-black text-[var(--bt-gold)]">{row.points}</span>
                    </li>
                  ))}
                </ol>
              )}
              <div className="flex items-center justify-between gap-2 px-4 py-3 text-sm">
                <button type="button" disabled={page <= 1} onClick={() => setPage((p) => p - 1)} className="rounded-lg px-3 py-1.5 font-bold hover:bg-white/10 disabled:opacity-40">{t("battle.prev")}</button>
                <span className="text-white/65">{page}/{pages}</span>
                <button type="button" disabled={page >= pages} onClick={() => setPage((p) => p + 1)} className="rounded-lg px-3 py-1.5 font-bold hover:bg-white/10 disabled:opacity-40">{t("battle.next")}</button>
              </div>
            </GlassPanel>

            <GlassPanel className="flex items-center gap-3 p-4" data-testid="leaderboard-me">
              <span className="text-sm font-bold text-white/70">{t("battle.yourPosition")}</span>
              <span className="text-2xl font-black">#{q.data.me.position}</span>
              <span className="ml-auto"><PointsChip points={q.data.me.points} /></span>
            </GlassPanel>
          </>
        )}
      </div>
    </>
  );
}
