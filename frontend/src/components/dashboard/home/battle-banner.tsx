"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ChevronRight, Coins, Play, Trophy } from "lucide-react";

import BattleIcon from "@/components/icons/battle-icon";
import PlayerAvatar from "@/features/battle/components/player-avatar";
import { getBattleSummary } from "@/features/battle/services/battle-service";
import { useTranslation } from "@/lib/i18n/use-translation";

import "@/features/battle/battle.css";

/** Compact Battle tile for all logged-in dashboard users. */
export default function BattleBanner() {
  const { t } = useTranslation();
  const { data } = useQuery({ queryKey: ["battle-summary"], queryFn: getBattleSummary, staleTime: 30_000, retry: 1 });
  const rank = data?.rank;
  const href = data?.open_match_id ? `/battle/match/${data.open_match_id}` : "/battle";
  const pct = Math.round((rank?.progress ?? 0) * 100);

  return (
    <article
      className="battle-root relative isolate flex h-full min-h-[204px] flex-col overflow-hidden rounded-card text-white shadow-[0_20px_44px_-24px_rgba(16,29,53,0.9)] ring-1 ring-[#F2C45B]/30"
      style={{ minHeight: "204px" }}
      aria-labelledby="battle-banner-title"
      data-testid="dashboard-battle-banner"
    >
      <picture>
        <source media="(max-width: 767px)" srcSet="/battle/themes/berlin-mobile.webp" />
        <img src="/battle/themes/berlin-desktop.webp" alt="" decoding="async" className="bt-scene-img absolute inset-0 -z-10 h-full w-full object-cover object-[50%_40%]" />
      </picture>
      <div aria-hidden="true" className="absolute inset-0 -z-10 bg-[linear-gradient(100deg,rgba(11,20,38,0.96)_0%,rgba(16,29,53,0.82)_45%,rgba(16,29,53,0.35)_100%)] max-md:bg-[linear-gradient(180deg,rgba(11,20,38,0.55)_0%,rgba(16,29,53,0.92)_55%,rgba(11,20,38,0.98)_100%)]" />
      <div aria-hidden="true" className="bt-flag-line absolute inset-x-0 top-0 h-1" />
      <div aria-hidden="true" className="bt-beam absolute -top-1/3 right-[22%] h-[170%] w-24" />

      <div className="relative flex h-full flex-1 flex-col gap-2.5 p-3.5 sm:p-4">
        <div className="flex items-center gap-2">
          <BattleIcon size={34} className="shrink-0 drop-shadow-[0_5px_12px_rgba(242,196,91,0.45)]" />
          <div className="min-w-0">
            <p className="text-[9px] font-extrabold uppercase tracking-[0.15em] text-[#F2C45B]">1 vs 1 · A1 → C1+</p>
            <h2 id="battle-banner-title" className="bt-display text-base leading-tight sm:text-lg">
              VIZU <span className="text-[#3984E8]">DEUTSCH</span> <span className="bt-gold-text">BATTLE</span>
            </h2>
          </div>
        </div>
        <p className="text-xs font-bold leading-snug text-white/90">{t("battle.bannerSlogan")}</p>
        {!data?.played && <p className="text-[11px] font-semibold leading-snug text-[#F2C45B]" data-testid="battle-banner-first">{t("battle.bannerFirst")}</p>}

        <div className="mt-auto flex min-w-0 items-center gap-2" data-testid="battle-banner-stats">
          {data ? (
            <span className="grid h-8 w-8 shrink-0 place-items-center overflow-hidden rounded-full bg-[#172A46] ring-1 ring-[#3984E8]">
              <PlayerAvatar player={data.player} size={32} round />
            </span>
          ) : <span className="h-8 w-8 shrink-0 animate-pulse rounded-full bg-white/10" />}
          <div className="min-w-0 flex-1">
            <p className="text-[9px] font-bold uppercase tracking-wider text-white/60">{t("battle.currentRank")}</p>
            <p className="break-words text-xs font-black leading-tight" data-testid="battle-banner-rank">{rank?.title ?? "A1-Einsteiger"}</p>
            <p className="truncate text-[9px] font-semibold text-white/70">
              <Coins size={10} aria-hidden="true" className="mr-0.5 inline" />{data?.player.points ?? 0}
              <span className="px-1">·</span>
              <Trophy size={10} aria-hidden="true" className="mr-0.5 inline" />{data?.wins ?? 0} {t("battle.wins")}
            </p>
          </div>
        </div>

        <div className="h-1.5 overflow-hidden rounded-full bg-white/10" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label={t("battle.nextRank")}>
          <div className="h-full rounded-full bg-gradient-to-r from-[#c8901f] via-[#F2C45B] to-[#fff2c4] transition-[width] duration-700" style={{ width: `${pct}%` }} />
        </div>

        {/* wraps on narrow phone tiles: the CTA keeps its full text, "Rangliste" moves below */}
        <div className="flex flex-wrap items-center justify-between gap-x-2 gap-y-1">
          <Link
            href={href}
            prefetch={false}
            data-testid="battle-banner-cta"
            className="bt-btn-start inline-flex min-h-10 items-center gap-1.5 whitespace-nowrap rounded-xl px-3 text-[11px] font-black uppercase tracking-wide"
          >
            <Play size={14} aria-hidden="true" className="shrink-0 fill-current" />
            <span>{data?.open_match_id ? t("battle.resume") : t("battle.bannerCta")}</span>
          </Link>
          <Link href="/battle/rangliste" prefetch={false} className="inline-flex shrink-0 items-center gap-0.5 text-[10px] font-bold text-[#F2C45B] hover:underline">
            {t("battle.navLeaderboard")} <ChevronRight size={12} aria-hidden="true" />
          </Link>
        </div>
      </div>
    </article>
  );
}
