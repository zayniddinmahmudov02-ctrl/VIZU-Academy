"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ChevronRight, Coins, Play, Trophy } from "lucide-react";

import BattleIcon from "@/components/icons/battle-icon";
import PlayerAvatar from "@/features/battle/components/player-avatar";
import { getBattleSummary } from "@/features/battle/services/battle-service";
import { useTranslation } from "@/lib/i18n/use-translation";

import "@/features/battle/battle.css";

/**
 * Top-of-dashboard VIZU DEUTSCH BATTLE banner (every logged-in user — no course or premium condition).
 * Without data (loading / error) it still shows the call to action.
 */
export default function BattleBanner() {
  const { t } = useTranslation();
  const { data } = useQuery({ queryKey: ["battle-summary"], queryFn: getBattleSummary, staleTime: 30_000, retry: 1 });
  const rank = data?.rank;
  const href = data?.open_match_id ? `/battle/match/${data.open_match_id}` : "/battle";
  const pct = Math.round((rank?.progress ?? 0) * 100);

  return (
    <section className="battle-root relative isolate overflow-hidden rounded-card text-white shadow-[0_24px_60px_-28px_rgba(16,29,53,0.9)] ring-1 ring-[#F2C45B]/30"
             style={{ minHeight: 0 }} aria-labelledby="battle-banner-title" data-testid="dashboard-battle-banner">
      <picture>
        <source media="(max-width: 767px)" srcSet="/battle/themes/berlin-mobile.webp" />
        <img src="/battle/themes/berlin-desktop.webp" alt="" decoding="async" className="bt-scene-img absolute inset-0 -z-10 h-full w-full object-cover object-[50%_40%]" />
      </picture>
      <div aria-hidden="true" className="absolute inset-0 -z-10 bg-[linear-gradient(100deg,rgba(11,20,38,0.96)_0%,rgba(16,29,53,0.82)_45%,rgba(16,29,53,0.35)_100%)] max-md:bg-[linear-gradient(180deg,rgba(11,20,38,0.55)_0%,rgba(16,29,53,0.92)_55%,rgba(11,20,38,0.98)_100%)]" />
      <div aria-hidden="true" className="bt-flag-line absolute inset-x-0 top-0 h-1" />
      <div aria-hidden="true" className="bt-beam absolute -top-1/3 right-[22%] h-[170%] w-24" />

      <div className="relative grid gap-5 p-5 sm:p-7 md:grid-cols-[1.2fr_0.8fr] md:items-center lg:p-8">
        <div>
          <div className="flex items-center gap-3">
            <BattleIcon size={56} className="drop-shadow-[0_8px_20px_rgba(242,196,91,0.45)]" />
            <div>
              <p className="text-[11px] font-extrabold uppercase tracking-[0.25em] text-[#F2C45B]">1 vs 1 · A1 → C1+</p>
              <h2 id="battle-banner-title" className="bt-display text-2xl sm:text-4xl">
                VIZU <span className="text-[#3984E8]">DEUTSCH</span> <span className="bt-gold-text">BATTLE</span>
              </h2>
            </div>
          </div>
          <p className="mt-3 max-w-xl text-base font-bold sm:text-lg">{t("battle.bannerSlogan")}</p>
          {!data?.played && <p className="mt-1 text-sm font-semibold text-[#F2C45B]" data-testid="battle-banner-first">{t("battle.bannerFirst")}</p>}
          <Link href={href} prefetch={false} data-testid="battle-banner-cta"
                className="bt-btn-start mt-5 inline-flex h-14 items-center gap-3 rounded-2xl px-7 text-base font-black uppercase tracking-wider sm:text-lg">
            <Play size={20} aria-hidden="true" className="fill-current" /> {data?.open_match_id ? t("battle.resume") : t("battle.bannerCta")}
          </Link>
        </div>

        <div className="bt-glass rounded-3xl p-4 sm:p-5" data-testid="battle-banner-stats">
          <div className="flex items-center gap-3">
            {data ? (
              <span className="grid h-14 w-14 shrink-0 place-items-center overflow-hidden rounded-full bg-[#172A46] ring-2 ring-[#3984E8]">
                <PlayerAvatar player={data.player} size={56} round />
              </span>
            ) : <span className="h-14 w-14 shrink-0 animate-pulse rounded-full bg-white/10" />}
            <div className="min-w-0 flex-1">
              <p className="text-[11px] font-bold uppercase tracking-wider text-white/60">{t("battle.currentRank")}</p>
              <p className="truncate text-lg font-black" data-testid="battle-banner-rank">{rank?.title ?? "A1-Einsteiger"}</p>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-2 text-center">
            <div className="rounded-2xl bg-white/5 py-2 ring-1 ring-white/10">
              <p className="flex items-center justify-center gap-1 text-xl font-black text-[#F2C45B]"><Coins size={16} aria-hidden="true" />{data?.player.points ?? 0}</p>
              <p className="text-[10px] font-bold uppercase tracking-wide text-white/60">Battle Points</p>
            </div>
            <div className="rounded-2xl bg-white/5 py-2 ring-1 ring-white/10">
              <p className="flex items-center justify-center gap-1 text-xl font-black text-[#3984E8]"><Trophy size={16} aria-hidden="true" />{data?.wins ?? 0}</p>
              <p className="text-[10px] font-bold uppercase tracking-wide text-white/60">{t("battle.wins")}</p>
            </div>
          </div>
          <div className="mt-4 h-2.5 overflow-hidden rounded-full bg-white/10" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label={t("battle.nextRank")}>
            <div className="h-full rounded-full bg-gradient-to-r from-[#c8901f] via-[#F2C45B] to-[#fff2c4] transition-[width] duration-700" style={{ width: `${pct}%` }} />
          </div>
          <p className="mt-1.5 flex items-center justify-between gap-2 text-[11px] font-semibold text-white/70">
            <span>{rank?.next_title ? `${t("battle.nextRank")}: ${rank.next_title}` : t("battle.maxRank")}</span>
            {rank?.remaining != null && <span className="shrink-0">{t("battle.remaining", { n: rank.remaining })}</span>}
          </p>
          <Link href="/battle/rangliste" prefetch={false} className="mt-3 flex items-center justify-end text-xs font-bold text-[#F2C45B] hover:underline">
            {t("battle.navLeaderboard")} <ChevronRight size={14} aria-hidden="true" />
          </Link>
        </div>
      </div>
    </section>
  );
}
