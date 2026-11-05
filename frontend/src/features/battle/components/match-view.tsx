"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { Flag, Home, WifiOff } from "lucide-react";

import { PlayerPanel, QuestionCard, RoundDots, TimerRing } from "@/features/battle/components/arena-parts";
import BattleScene from "@/features/battle/components/battle-scene";
import { useBattleLowFx } from "@/features/battle/components/battle-shell";
import { GlassPanel, LoadingState, StageChip } from "@/features/battle/components/battle-ui";
import { Matchmaking, VersusCountdown } from "@/features/battle/components/lobby";
import { MatchResult, RankUpOverlay } from "@/features/battle/components/result";
import { useBattleHome } from "@/features/battle/hooks/use-battle-home";
import { playSfx } from "@/features/battle/audio/battle-audio";
import { useMatchAudio } from "@/features/battle/audio/use-battle-audio";
import AudioSettingsButton from "@/features/battle/components/audio-settings";
import { useMatch, useNow } from "@/features/battle/hooks/use-match";
import { msUntil } from "@/features/battle/lib/battle-utils";
import { createRoom, joinQueue, leaveMatch, startPractice, type MatchState } from "@/features/battle/services/battle-service";
import { useTranslation } from "@/lib/i18n/use-translation";

export default function MatchView({ matchId }: { matchId: string }) {
  const { t } = useTranslation();
  const router = useRouter();
  const lowFx = useBattleLowFx();
  const home = useBattleHome();
  const { data: m, isLoading, isError, error, offset, answer, leave, isFetching, failureCount } = useMatch(matchId);
  const live = m?.status === "waiting" || m?.status === "active";
  const now = useNow(live, 100);
  const [pending, setPending] = useState<{ round: number; choice: number } | null>(null);
  const [rankUpSeen, setRankUpSeen] = useState(false);

  // matchmaking may move the player into another waiting player's match
  useEffect(() => {
    if (m && m.id !== matchId) router.replace(`/battle/match/${m.id}`);
  }, [m, matchId, router]);

  const go = (s: MatchState) => router.push(`/battle/match/${s.id}`);
  const again = useMutation({
    mutationFn: () => (m?.mode === "bot" ? startPractice() : m?.mode === "private" ? createRoom() : joinQueue()),
    onSuccess: go,
  });
  const toBot = useMutation({
    mutationFn: async () => {
      await leaveMatch(matchId);
      return startPractice();
    },
    onSuccess: go,
  });

  const round = m?.round ?? null;
  const pendingChoice = pending && round && pending.round === round.no ? pending.choice : null;
  const totalMs = (m?.timing.round_s ?? 12) * 1000;
  const msLeft = round?.phase === "question" ? msUntil(round.deadline, offset.current, now) : 0;

  const countdownMs = m?.status === "active" && !round && m.countdown_ends_at ? msUntil(m.countdown_ends_at, offset.current, now) : null;
  useMatchAudio(m, msLeft, countdownMs);

  const choose = (choice: number) => {
    if (!round || round.phase !== "question" || round.my_answer || pendingChoice !== null || msLeft <= 0) return;
    playSfx("select");
    setPending({ round: round.no, choice });
    answer.mutate({ round: round.no, choice });
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      const i = ["1", "2", "3", "4"].indexOf(e.key) >= 0 ? Number(e.key) - 1 : ["a", "b", "c", "d"].indexOf(e.key.toLowerCase());
      if (i >= 0) choose(i);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const theme = home.data?.themes.find((th) => th.stage === m?.stage) ?? home.data?.theme ?? null;

  if (isLoading) return <><BattleScene theme={theme} arena lowFx={lowFx} /><LoadingState /></>;
  if (isError || !m) {
    const status = (error as { response?: { status?: number } } | null)?.response?.status;
    return (
      <>
        <BattleScene theme={theme} lowFx={lowFx} />
        <GlassPanel className="mx-auto mt-16 max-w-md p-6 text-center" data-testid="battle-match-missing">
          <p className="font-bold">{status === 404 ? t("battle.cancelled") : t("battle.loadError")}</p>
          <Link href="/battle" prefetch={false} className="mt-4 inline-flex items-center gap-2 rounded-xl bg-white/10 px-4 py-2 text-sm font-bold ring-1 ring-white/20"><Home size={15} />{t("battle.backHome")}</Link>
        </GlassPanel>
      </>
    );
  }

  const reconnecting = failureCount > 0 && isFetching;

  return (
    <>
      <BattleScene theme={theme} arena={m.status === "active"} lowFx={lowFx} showCredit={m.status !== "active"} />
      {reconnecting && (
        <p className="fixed left-1/2 top-3 z-50 flex -translate-x-1/2 items-center gap-2 rounded-full bg-[var(--bt-red)] px-4 py-1.5 text-xs font-bold shadow-lg" role="status">
          <WifiOff size={14} /> {t("battle.reconnecting")}
        </p>
      )}

      {m.status === "waiting" && (
        <Matchmaking match={m} offsetMs={offset.current} now={now} busy={leave.isPending || toBot.isPending}
                     onCancel={() => leave.mutate(undefined, { onSuccess: () => router.push("/battle") })} onBot={() => toBot.mutate()} />
      )}

      {m.status === "active" && !round && <VersusCountdown match={m} offsetMs={offset.current} now={now} />}

      {m.status === "active" && round && (
        <div className="mx-auto max-w-[1360px]" data-testid="battle-arena" data-round={round.no} data-phase={round.phase}>
          {/* top HUD */}
          <div className="bt-glass-strong sticky top-2 z-30 mx-auto mb-3 grid max-w-[760px] grid-cols-[1fr_auto_1fr] items-center gap-2 rounded-2xl px-3 py-2 lg:static lg:mb-4 landscape-short:static landscape-short:mb-2 landscape-short:py-1">
            <div className="lg:hidden landscape-short:invisible"><PlayerPanel player={m.me} side="me" compact /></div>
            <div className="hidden text-left lg:block"><StageChip stage={m.stage} /></div>
            <div className="flex items-center gap-3">
              <div className="text-center">
                <p className="text-[10px] font-bold uppercase tracking-widest text-white/60">{t("battle.round")}</p>
                <p className="text-xl font-black tabular-nums" data-testid="arena-round">{String(round.no).padStart(2, "0")}/{String(round.total).padStart(2, "0")}</p>
              </div>
              <TimerRing msLeft={msLeft} totalMs={totalMs} size={58} />
              <p className="hidden text-2xl font-black tabular-nums lg:block" data-testid="arena-score">
                {/* key = score: the number re-mounts and plays the bump animation on every change */}
                <span key={`me-${m.me.score}`} className="bt-score-bump inline-block text-[var(--bt-blue)]">{m.me.score}</span><span className="mx-1 text-white/40">:</span>
                <span key={`op-${m.opponent?.score ?? 0}`} className="bt-score-bump inline-block text-[var(--bt-red)]">{m.opponent?.score ?? 0}</span>
              </p>
            </div>
            <div className="lg:hidden landscape-short:invisible"><PlayerPanel player={m.opponent} side="opponent" compact answered={round.opponent_answered} /></div>
            <div className="hidden justify-end lg:flex">
              <button type="button" onClick={() => window.confirm(t("battle.surrenderConfirm")) && leave.mutate()} data-testid="arena-surrender"
                      className="inline-flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-xs font-bold text-white/70 hover:bg-white/10 hover:text-white">
                <Flag size={14} aria-hidden="true" /> {t("battle.surrender")}
              </button>
            </div>
          </div>

          <div className="grid gap-4 lg:grid-cols-[250px_minmax(0,1fr)_250px] lg:items-start xl:grid-cols-[280px_minmax(0,1fr)_280px] landscape-short:grid-cols-[110px_minmax(0,1fr)_110px] landscape-short:gap-2">
            <aside className="hidden lg:block landscape-short:block">
              <div className="landscape-short:hidden"><PlayerPanel player={m.me} side="me" /></div>
              <div className="hidden landscape-short:block"><PlayerPanel player={m.me} side="me" compact /></div>
              <GlassPanel className="mt-4 hidden p-4 xl:block" as="div">
                <p className="text-[11px] font-extrabold uppercase tracking-widest text-white/60">{t("battle.currentRank")}</p>
                <p className="mt-1 text-sm font-black text-[var(--bt-gold)]">{m.me.rank}</p>
                <p className="mt-3 text-[11px] font-extrabold uppercase tracking-widest text-white/60">{t("battle.rulesTitle")}</p>
                <p className="mt-1 text-xs text-white/70">1–4 / A–D · {m.timing.round_s} s · {m.mode === "ranked" ? "Ranked" : m.mode === "bot" ? "Training" : t("battle.privateRoom")}</p>
              </GlassPanel>
            </aside>

            <div className="min-w-0">
              {/* key = round: each new round slides in (round transition) */}
              <div key={round.no} className="bt-round-in">
                <QuestionCard round={round} stage={m.stage} msLeft={msLeft} totalMs={totalMs} pending={pendingChoice} onAnswer={choose} opponentChoice={round.opponent_choice} />
              </div>
              <div className="mt-4"><RoundDots match={m} /></div>
              <div className="mt-3 flex items-center justify-center gap-2 lg:hidden">
                <AudioSettingsButton />
                <button type="button" onClick={() => window.confirm(t("battle.surrenderConfirm")) && leave.mutate()} data-testid="arena-surrender-mobile"
                        className="inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-bold text-white/70 hover:bg-white/10">
                  <Flag size={14} aria-hidden="true" /> {t("battle.surrender")}
                </button>
              </div>
            </div>

            <aside className="hidden lg:block landscape-short:block">
              <div className="landscape-short:hidden"><PlayerPanel player={m.opponent} side="opponent" answered={round.opponent_answered} /></div>
              <div className="hidden landscape-short:block"><PlayerPanel player={m.opponent} side="opponent" compact answered={round.opponent_answered} /></div>
            </aside>
          </div>
        </div>
      )}

      {m.status === "finished" && m.result && (
        <>
          <MatchResult match={m} onAgain={() => again.mutate()} busy={again.isPending} />
          {m.result.rank_up && !rankUpSeen && (
            <RankUpOverlay match={m} theme={home.data?.themes.find((th) => th.stage === m.result?.rank_after.stage) ?? theme} onClose={() => setRankUpSeen(true)} />
          )}
        </>
      )}

      {m.status === "cancelled" && (
        <GlassPanel className="mx-auto mt-16 max-w-md p-6 text-center" data-testid="battle-cancelled">
          <p className="font-bold">{t("battle.cancelled")}</p>
          <Link href="/battle" prefetch={false} className="mt-4 inline-flex items-center gap-2 rounded-xl bg-white/10 px-4 py-2 text-sm font-bold ring-1 ring-white/20"><Home size={15} />{t("battle.backHome")}</Link>
        </GlassPanel>
      )}
    </>
  );
}
