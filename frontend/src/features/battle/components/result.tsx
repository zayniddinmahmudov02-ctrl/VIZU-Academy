"use client";

import { useEffect, useState, type CSSProperties } from "react";
import Link from "next/link";
import { Crown, Home, RotateCcw } from "lucide-react";

import { API_URL } from "@/constants/api";
import PlayerAvatar from "@/features/battle/components/player-avatar";
import { GlassPanel, ProgressBar, RankBadge } from "@/features/battle/components/battle-ui";
import { resolveThemeImage } from "@/features/battle/lib/battle-utils";
import type { MatchState, Theme } from "@/features/battle/services/battle-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

function useCountUp(target: number, ms = 1200) {
  const [v, setV] = useState(0);
  useEffect(() => {
    let raf = 0;
    const start = performance.now();
    const step = (now: number) => {
      const p = Math.min(1, (now - start) / ms);
      setV(Math.round(target * (1 - Math.pow(1 - p, 3))));
      if (p < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, ms]);
  return v;
}

export function MatchResult({ match, onAgain, busy }: { match: MatchState; onAgain: () => void; busy: boolean }) {
  const { t } = useTranslation();
  const r = match.result!;
  const delta = useCountUp(Math.abs(r.points_delta));
  const title = r.outcome === "win" ? t("battle.resultWin") : r.outcome === "loss" ? t("battle.resultLoss") : t("battle.resultDraw");
  const correct = match.history.filter((h) => h.me).length;
  return (
    <div className="mx-auto max-w-3xl pt-4 sm:pt-8" data-testid="battle-result" data-outcome={r.outcome}>
      <GlassPanel strong className="overflow-hidden p-5 text-center sm:p-8">
        <p className={cn("bt-display text-5xl sm:text-7xl", r.outcome === "win" ? "bt-gold-text" : r.outcome === "loss" ? "text-[var(--bt-red)]" : "text-white")}>{title}</p>
        {r.reason === "forfeit" && <p className="mt-2 text-sm text-white/70">{t("battle.reasonForfeit")}</p>}
        {r.reason === "afk" && <p className="mt-2 text-sm text-white/70">{t("battle.reasonAfk")}</p>}

        <div className="mt-6 grid grid-cols-[1fr_auto_1fr] items-center gap-3">
          <div className="flex flex-col items-center">
            <PlayerAvatar player={match.me} size={120} accent="#3984E8" />
            <p className="mt-1 truncate text-sm font-black">{t("battle.you")}</p>
            <p className="text-4xl font-black tabular-nums text-[var(--bt-blue)]">{match.me.score}</p>
          </div>
          <p className="bt-display text-3xl text-white/50">:</p>
          <div className="flex flex-col items-center">
            <PlayerAvatar player={match.opponent ?? { avatar: "bot" }} size={120} accent="#D83B43" />
            <p className="mt-1 max-w-full truncate text-sm font-black">{match.opponent?.name}</p>
            <p className="text-4xl font-black tabular-nums text-[var(--bt-red)]">{match.opponent?.score ?? 0}</p>
          </div>
        </div>

        <p className="mt-4 text-sm font-semibold text-white/70">{correct}/{match.rounds} ✓</p>

        {r.ranked ? (
          <div className="mx-auto mt-5 max-w-md">
            <p className={cn("text-3xl font-black", r.points_delta >= 0 ? "text-[var(--bt-gold)]" : "text-[var(--bt-red)]")} data-testid="result-points">
              {r.points_delta >= 0 ? "+" : "−"}{delta} BP
            </p>
            <p className="mt-1 text-xs font-semibold text-white/60">{r.rank_after.title} · {r.points_after} BP</p>
            <ProgressBar value={r.rank_after.progress} className="mt-3" />
          </div>
        ) : <p className="mt-5 text-sm text-white/65">{t("battle.noRating")}</p>}

        <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
          <button type="button" onClick={onAgain} disabled={busy} data-testid="result-again"
                  className="bt-btn-start inline-flex h-14 items-center justify-center gap-2 rounded-2xl px-7 text-base font-black uppercase tracking-wider disabled:opacity-60">
            <RotateCcw size={20} aria-hidden="true" /> {t("battle.playAgain")}
          </button>
          <Link href="/battle" prefetch={false} className="bt-glass inline-flex h-14 items-center justify-center gap-2 rounded-2xl px-6 text-sm font-bold hover:bg-white/10">
            <Home size={18} aria-hidden="true" /> {t("battle.backHome")}
          </Link>
        </div>
      </GlassPanel>
    </div>
  );
}

const SPARKS = Array.from({ length: 36 }, (_, i) => ({
  left: `${(i * 29) % 100}%`, d: `${3 + (i % 5)}s`, delay: `${(i * 0.17) % 3}s`, x: `${((i % 7) - 3) * 30}px`, size: 3 + (i % 4),
}));

/** Full-screen rank-up: golden particles, spinning 3D badge, next city in the background. */
export function RankUpOverlay({ match, theme, onClose }: { match: MatchState; theme: Theme | null; onClose: () => void }) {
  const { t } = useTranslation();
  const r = match.result!;
  const legend = r.stage_up && r.rank_after.stage === "C1+";
  const points = useCountUp(r.points_after, 1600);
  const bg = resolveThemeImage(theme?.desktop_image, API_URL);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => (e.key === "Escape" || e.key === "Enter") && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 grid place-items-center overflow-hidden p-4" role="dialog" aria-modal="true" aria-label={t("battle.rankUp")} data-testid="rank-up">
      {/* eslint-disable-next-line @next/next/no-img-element -- pre-sized WebP background */}
      {bg && <img src={bg} alt="" className="absolute inset-0 h-full w-full scale-110 object-cover" />}
      <div className={cn("absolute inset-0", legend ? "bg-[radial-gradient(circle_at_center,rgba(80,30,120,0.55),rgba(5,8,18,0.94)_70%)]" : "bg-[radial-gradient(circle_at_center,rgba(16,29,53,0.45),rgba(5,8,18,0.92)_70%)]")} />
      <div aria-hidden="true" className="absolute inset-0">
        {SPARKS.map((s, i) => (
          <span key={i} className="bt-particle" style={{ left: s.left, width: s.size, height: s.size, "--d": s.d, "--delay": s.delay, "--x": s.x } as CSSProperties} />
        ))}
      </div>
      <div aria-hidden="true" className="absolute left-1/2 top-1/2 h-[520px] w-[520px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[var(--bt-gold)]/20 blur-3xl" />

      <div className="relative flex max-w-xl flex-col items-center text-center">
        {legend && <Crown className="mb-2 text-[var(--bt-gold)] drop-shadow-[0_0_20px_rgba(242,196,91,0.9)]" size={44} aria-hidden="true" />}
        <div className="bt-badge-spin"><RankBadge stage={r.rank_after.stage} tier={r.rank_after.tier} size={150} /></div>
        {r.stage_up ? (
          <>
            <p className="bt-display bt-gold-text mt-6 text-4xl sm:text-6xl">{legend ? t("battle.legendTitle") : t("battle.rankUpDone")}</p>
            <p className="bt-display mt-3 text-lg text-white sm:text-2xl">{t("battle.stageComplete", { stage: r.rank_before.stage })}</p>
            <p className="mt-4 rounded-full bg-white/10 px-5 py-2 text-base font-black tracking-wider ring-1 ring-[var(--bt-gold)]/50 sm:text-lg">
              {r.rank_after.stage} — {r.rank_after.stage_subtitle.toUpperCase()}
            </p>
          </>
        ) : (
          <>
            <p className="bt-display bt-gold-text mt-6 text-4xl sm:text-5xl">{t("battle.rankUp")}</p>
            <p className="mt-3 text-xl font-black">{r.rank_after.title}</p>
          </>
        )}
        <div className="mt-5 flex items-center gap-3">
          <PlayerAvatar player={match.me} size={84} accent="#F2C45B" />
          <p className="text-3xl font-black tabular-nums text-[var(--bt-gold)]">{points} BP</p>
        </div>
        {r.rank_after.next_title && (
          <p className="mt-2 text-sm text-white/70">{t("battle.nextRank")}: <b className="text-white">{r.rank_after.next_title}</b> · {t("battle.remaining", { n: r.rank_after.remaining ?? 0 })}</p>
        )}
        {theme && <p className="mt-1 text-xs text-white/55">{theme.city} · {theme.title}</p>}
        <button type="button" onClick={onClose} autoFocus data-testid="rank-up-continue"
                className="bt-btn-start mt-7 inline-flex h-13 items-center rounded-2xl px-8 py-3 text-base font-black uppercase tracking-wider">
          {t("battle.continue")}
        </button>
      </div>
    </div>
  );
}
