"use client";

import { Lock } from "lucide-react";

import BattleIcon from "@/components/icons/battle-icon";

import BattleScene from "@/features/battle/components/battle-scene";
import { useBattleLowFx } from "@/features/battle/components/battle-shell";
import { ErrorState, GlassPanel, LoadingState, ProgressBar, RankBadge, SectionTitle } from "@/features/battle/components/battle-ui";
import { useBattleHome } from "@/features/battle/hooks/use-battle-home";
import { winRate } from "@/features/battle/lib/battle-utils";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

export default function AchievementsView() {
  const { t, language } = useTranslation();
  const lowFx = useBattleLowFx();
  const { data, isLoading, isError, refetch } = useBattleHome();
  if (isLoading) return <><BattleScene theme={null} lowFx={lowFx} /><LoadingState /></>;
  if (isError || !data) return <><BattleScene theme={null} lowFx={lowFx} /><ErrorState onRetry={() => refetch()} /></>;
  const unlocked = data.achievements.filter((a) => a.unlocked).length;

  return (
    <>
      <BattleScene theme={data.theme} lowFx={lowFx} />
      <div className="mx-auto max-w-5xl space-y-5" data-testid="battle-erfolge">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <h1 className="bt-display text-4xl sm:text-5xl">{t("battle.navAchievements")}</h1>
          <p className="text-sm font-bold text-white/70">{unlocked}/{data.achievements.length} {t("battle.unlocked")}</p>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {data.achievements.map((a) => (
            <GlassPanel key={a.key} className={cn("p-4", a.unlocked && "shadow-[var(--bt-glow-gold)]")} data-testid={`achievement-${a.key}`}>
              <span className={cn("grid h-12 w-12 place-items-center rounded-2xl", a.unlocked ? "bg-gradient-to-b from-[#fff2c4]/30 to-[#c8901f]/30 ring-1 ring-[var(--bt-gold)]/60" : "bg-white/10 text-white/50")}>
                {a.unlocked ? <BattleIcon size={34} /> : <Lock size={20} />}
              </span>
              <p className="mt-3 text-sm font-black">{language === "uz" ? a.title_uz : a.title_de}</p>
              <ProgressBar value={a.progress / a.goal} className="mt-2 h-2" />
              <p className="mt-1 text-[11px] text-white/60">{a.progress}/{a.goal}</p>
            </GlassPanel>
          ))}
        </div>

        <GlassPanel className="p-5">
          <SectionTitle>{t("battle.statsTitle")}</SectionTitle>
          <dl className="grid grid-cols-2 gap-3 text-center sm:grid-cols-4">
            {[["matchesShort", data.stats.matches], ["wins", data.stats.wins], ["winRate", winRate(data.stats.win_rate)], ["streak", data.stats.best_streak]].map(([k, v]) => (
              <div key={k} className="rounded-2xl bg-white/5 p-3 ring-1 ring-white/10">
                <dt className="text-[11px] font-bold uppercase tracking-wide text-white/60">{t(`battle.${k}`)}</dt>
                <dd className="mt-1 text-2xl font-black text-[var(--bt-gold)]">{v}</dd>
              </div>
            ))}
          </dl>
        </GlassPanel>

        <GlassPanel className="p-5" data-testid="battle-rank-ladder">
          <SectionTitle>{t("battle.ladderTitle")}</SectionTitle>
          <ol className="grid grid-cols-3 gap-2 sm:grid-cols-6">
            {data.ladder.map((r) => {
              const reached = r.index <= data.rank.index;
              return (
                <li key={r.index} className={cn("flex flex-col items-center rounded-2xl p-2 text-center ring-1", r.index === data.rank.index ? "bg-[var(--bt-gold)]/15 ring-[var(--bt-gold)]" : "ring-white/10", !reached && "opacity-50")}>
                  <RankBadge stage={r.stage} tier={r.index % 3} size={44} glow={reached} />
                  <span className="mt-1 text-[11px] font-black leading-tight">{r.title}</span>
                  <span className="text-[10px] text-white/55">{r.at} BP</span>
                </li>
              );
            })}
          </ol>
        </GlassPanel>
      </div>
    </>
  );
}
