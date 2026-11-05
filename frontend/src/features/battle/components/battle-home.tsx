"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { Bot, ChevronRight, DoorOpen, Flame, Lock, Minus, Play, Trophy, UserRound, X as XIcon } from "lucide-react";

import BattleIcon from "@/components/icons/battle-icon";

import { API_URL } from "@/constants/api";
import AvatarPicker from "@/features/battle/components/avatar-picker";
import PlayerAvatar from "@/features/battle/components/player-avatar";
import BattleScene from "@/features/battle/components/battle-scene";
import { useBattleLowFx } from "@/features/battle/components/battle-shell";
import { ErrorState, FlagStripe, GermanFlag, GlassPanel, LoadingState, PointsChip, ProgressBar, RankBadge, SectionTitle, StageChip } from "@/features/battle/components/battle-ui";
import { useBattleHome } from "@/features/battle/hooks/use-battle-home";
import { resolveThemeImage, winRate } from "@/features/battle/lib/battle-utils";
import { battleError, createRoom, joinQueue, joinRoom, startPractice, type BattleHome as Home, type MatchState } from "@/features/battle/services/battle-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

function errorKey(code: string) {
  if (code === "MATCH_ALREADY_OPEN") return "battle.errorAlreadyOpen";
  if (code === "ROOM_NOT_FOUND") return "battle.errorRoom";
  if (code === "BATTLE_NOT_ENOUGH_WORDS") return "battle.notPlayable";
  return "battle.errorGeneric";
}

export default function BattleHome() {
  const { t, language } = useTranslation();
  const router = useRouter();
  const params = useSearchParams();
  const lowFx = useBattleLowFx();
  const { data, isLoading, isError, refetch } = useBattleHome();
  const [picker, setPicker] = useState(false);
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const showPicker = picker || params.get("avatar") === "1";

  const go = (m: MatchState) => router.push(`/battle/match/${m.id}`);
  const fail = (e: unknown) => setError(t(errorKey(battleError(e))));
  const queue = useMutation({ mutationFn: joinQueue, onSuccess: go, onError: fail });
  const practice = useMutation({ mutationFn: startPractice, onSuccess: go, onError: fail });
  const room = useMutation({ mutationFn: createRoom, onSuccess: go, onError: fail });
  const join = useMutation({ mutationFn: joinRoom, onSuccess: go, onError: fail });
  const busy = queue.isPending || practice.isPending || room.isPending || join.isPending;

  // warm the next stage's city picture so the rank-up screen opens instantly
  useEffect(() => {
    if (!data) return;
    const next = data.themes[Math.min(data.themes.length - 1, data.themes.findIndex((th) => th.stage === data.rank.stage) + 1)];
    const src = resolveThemeImage(next?.desktop_image, API_URL);
    if (!src) return;
    const id = window.setTimeout(() => { const img = new Image(); img.src = src; }, 2500);
    return () => window.clearTimeout(id);
  }, [data]);

  if (isLoading) return <><BattleScene theme={null} lowFx={lowFx} /><LoadingState /></>;
  if (isError || !data) return <><BattleScene theme={null} lowFx={lowFx} /><ErrorState onRetry={() => refetch()} /></>;

  const { player, rank, stats, theme } = data;
  const closePicker = () => {
    setPicker(false);
    if (params.get("avatar")) router.replace("/battle");
  };
  const onJoin = (e: FormEvent) => {
    e.preventDefault();
    if (code.trim().length >= 4) join.mutate(code.trim());
  };

  return (
    <>
      <BattleScene theme={theme} lowFx={lowFx} />
      <div className="space-y-5 sm:space-y-6" data-testid="battle-home">
        {/* HERO */}
        <section className="relative grid items-center gap-6 pt-2 lg:min-h-[480px] lg:grid-cols-[1.15fr_0.85fr]">
          <div className="order-2 lg:order-1">
            <div className="flex flex-wrap items-center gap-2">
              <StageChip stage={rank.stage} city={theme.city} />
              <span className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1 text-xs font-bold text-white/85 ring-1 ring-white/15">
                <GermanFlag size={16} /> {theme.title}
              </span>
            </div>
            <h1 className="bt-display mt-4 text-[clamp(2.4rem,7vw,5.2rem)] drop-shadow-[0_6px_30px_rgba(0,0,0,0.6)]">
              VIZU <span className="text-[var(--bt-blue)]">DEUTSCH</span>
              <br />
              <span className="bt-gold-text">BATTLE</span>
            </h1>
            <FlagStripe className="mt-4 w-40" />
            <p className="mt-4 max-w-xl text-lg font-bold text-white sm:text-xl">{t("battle.slogan")}</p>
            <p className="mt-2 max-w-xl text-sm text-white/75 sm:text-base">{t("battle.heroLead")}</p>

            {!data.playable && (
              <p className="mt-4 max-w-xl rounded-2xl bg-[var(--bt-red)]/20 px-4 py-3 text-sm font-semibold ring-1 ring-[var(--bt-red)]/50" data-testid="battle-not-playable">
                {t("battle.notPlayable")} ({data.pool}/{data.min_pool})
              </p>
            )}
            {error && <p role="alert" className="mt-4 max-w-xl rounded-2xl bg-[var(--bt-red)]/20 px-4 py-3 text-sm font-semibold ring-1 ring-[var(--bt-red)]/50">{error}</p>}

            <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center">
              {data.open_match_id ? (
                <Link href={`/battle/match/${data.open_match_id}`} prefetch={false} data-testid="battle-resume"
                      className="bt-btn-start inline-flex h-16 items-center justify-center gap-3 rounded-2xl px-8 text-lg font-black uppercase tracking-wider">
                  <Play size={22} aria-hidden="true" /> {t("battle.resume")}
                </Link>
              ) : (
                <button type="button" disabled={busy || !data.playable} onClick={() => { setError(null); queue.mutate(); }} data-testid="battle-start"
                        className="bt-btn-start inline-flex h-16 items-center justify-center gap-3 rounded-2xl px-8 text-lg font-black uppercase tracking-wider disabled:cursor-not-allowed disabled:opacity-60">
                  <BattleIcon size={30} /> {t("battle.start")}
                </button>
              )}
              <button type="button" disabled={busy || !data.playable || !!data.open_match_id} onClick={() => { setError(null); practice.mutate(); }} data-testid="battle-practice"
                      className="bt-glass inline-flex h-12 items-center justify-center gap-2 rounded-2xl px-5 text-sm font-bold hover:bg-white/10 disabled:opacity-50">
                <Bot size={18} aria-hidden="true" /> {t("battle.practice")}
                <span className="text-xs font-semibold text-white/60">· {t("battle.practiceHint")}</span>
              </button>
            </div>
          </div>

          <div className="order-1 flex flex-col items-center lg:order-2">
            <div className="relative grid place-items-center">
              <div aria-hidden="true" className="bt-holo-ring absolute h-[250px] w-[250px] rounded-full border-2 border-dashed border-[var(--bt-blue)]/50 sm:h-[330px] sm:w-[330px]" />
              <div aria-hidden="true" className="absolute h-[200px] w-[200px] rounded-full bg-[var(--bt-blue)]/25 blur-3xl sm:h-[280px] sm:w-[280px]" />
              <PlayerAvatar player={player} size={lowFx ? 190 : 240} accent={theme.accent} className="relative sm:scale-110" />
              <div className="absolute -bottom-2 -right-6 sm:-right-10"><RankBadge stage={rank.stage} tier={rank.tier} size={70} /></div>
            </div>
            <p className="mt-4 text-lg font-black">{player.name}</p>
            <p className="text-sm font-bold text-[var(--bt-gold)]">{rank.title}</p>
            <button type="button" onClick={() => setPicker(true)} data-testid="battle-change-avatar"
                    className="mt-3 inline-flex items-center gap-1.5 rounded-xl bg-white/10 px-3 py-1.5 text-xs font-bold ring-1 ring-white/15 hover:bg-white/15">
              <UserRound size={14} aria-hidden="true" /> {t("battle.changeAvatar")}
            </button>
          </div>
        </section>

        {/* PROGRESS + STATS */}
        <div className="grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
          <GlassPanel className="p-5 sm:p-6" data-testid="battle-progress">
            <SectionTitle>{t("battle.progressTitle")}</SectionTitle>
            <div className="flex items-center gap-4">
              <RankBadge stage={rank.stage} tier={rank.tier} size={64} />
              <div className="min-w-0 flex-1">
                <p className="text-xs font-bold uppercase tracking-wider text-white/60">{t("battle.currentRank")}</p>
                <p className="truncate text-xl font-black">{rank.title}</p>
                <p className="text-xs font-semibold text-white/60">{rank.stage} — {rank.stage_subtitle}</p>
              </div>
              <PointsChip points={player.points} className="text-sm" />
            </div>
            <ProgressBar value={rank.progress} className="mt-5" label={t("battle.nextRank")} />
            <div className="mt-2 flex justify-between gap-2 text-xs font-semibold text-white/70">
              <span>{rank.floor} BP</span>
              {rank.next_title ? (
                <span className="text-right">{t("battle.nextRank")}: <b className="text-white">{rank.next_title}</b> · {t("battle.remaining", { n: rank.remaining ?? 0 })}</span>
              ) : <span>{t("battle.maxRank")}</span>}
            </div>
          </GlassPanel>

          <GlassPanel className="p-5 sm:p-6" data-testid="battle-stats">
            <SectionTitle>{t("battle.statsTitle")}</SectionTitle>
            <div className="grid grid-cols-3 gap-2 sm:grid-cols-5">
              {[
                { k: "wins", v: stats.wins, c: "text-[var(--bt-blue)]" },
                { k: "losses", v: stats.losses, c: "text-[var(--bt-red)]" },
                { k: "draws", v: stats.draws, c: "text-white" },
                { k: "winRate", v: winRate(stats.win_rate), c: "text-[var(--bt-gold)]" },
                { k: "streak", v: stats.streak, c: "text-[var(--bt-gold)]", icon: true },
              ].map((s) => (
                <div key={s.k} className="rounded-2xl bg-white/5 px-2 py-3 text-center ring-1 ring-white/10">
                  <p className={cn("flex items-center justify-center gap-1 text-2xl font-black", s.c)}>{s.icon && <Flame size={18} aria-hidden="true" />}{s.v}</p>
                  <p className="mt-1 text-[11px] font-bold uppercase tracking-wide text-white/60">{t(`battle.${s.k}`)}</p>
                </div>
              ))}
            </div>
            <p className="mt-4 text-xs text-white/55">{t("battle.rules", { rounds: data.rules.rounds, sec: data.rules.round_s, per: data.rules.per_correct, bonus: data.rules.win_bonus })}</p>
          </GlassPanel>
        </div>

        {/* LEADERBOARD + RECENT + ROOM */}
        <div className="grid gap-5 lg:grid-cols-3">
          <GlassPanel className="p-5" data-testid="battle-leaderboard-preview">
            <SectionTitle action={<Link href="/battle/rangliste" prefetch={false} className="flex items-center text-xs font-bold text-[var(--bt-gold)] hover:underline">{t("battle.showAll")}<ChevronRight size={14} /></Link>}>
              {t("battle.leaderboardPreview")}
            </SectionTitle>
            <ol className="space-y-1.5">
              {data.leaderboard.items.map((row) => (
                <li key={`${row.position}-${row.name}`} className={cn("flex items-center gap-3 rounded-xl px-2 py-1.5", row.me && "bg-[var(--bt-blue)]/20 ring-1 ring-[var(--bt-blue)]/50")}>
                  <span className={cn("w-6 text-center text-sm font-black", row.position <= 3 ? "text-[var(--bt-gold)]" : "text-white/60")}>{row.position}</span>
                  <span className="grid h-8 w-8 shrink-0 place-items-center overflow-hidden rounded-full bg-[var(--bt-dark)]"><PlayerAvatar player={row} size={32} round /></span>
                  <span className="min-w-0 flex-1 truncate text-sm font-bold">{row.name}</span>
                  <span className="text-xs font-black text-[var(--bt-gold)]">{row.points}</span>
                </li>
              ))}
            </ol>
            <p className="mt-3 border-t border-white/10 pt-3 text-xs font-semibold text-white/70">{t("battle.yourPosition")}: <b className="text-white">#{data.leaderboard.me.position}</b></p>
          </GlassPanel>

          <GlassPanel className="p-5" data-testid="battle-recent">
            <SectionTitle>{t("battle.recentTitle")}</SectionTitle>
            {data.recent.length === 0 ? <p className="text-sm text-white/60">{t("battle.noMatches")}</p> : (
              <ul className="space-y-1.5">
                {data.recent.map((m) => (
                  <li key={m.id} className="flex items-center gap-3 rounded-xl bg-white/5 px-3 py-2 ring-1 ring-white/5">
                    <span className={cn("grid h-8 w-8 shrink-0 place-items-center rounded-lg text-xs font-black",
                      m.result === "win" ? "bg-[var(--bt-blue)]/30 text-[var(--bt-blue)]" : m.result === "loss" ? "bg-[var(--bt-red)]/25 text-[var(--bt-red)]" : "bg-white/10 text-white")}>
                      {m.result === "win" ? <Trophy size={15} /> : m.result === "loss" ? <XIcon size={15} /> : <Minus size={15} />}
                    </span>
                    <PlayerAvatar player={{ avatar: m.mode === "bot" ? "bot" : "student", photo: m.opponent_photo, name: m.opponent }} size={28} round />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm font-bold">{t("battle.vs")} {m.opponent}</span>
                      <span className="text-[11px] text-white/55">{m.stage} · {m.mode === "ranked" ? "Ranked" : m.mode === "bot" ? "Training" : t("battle.privateRoom")}</span>
                    </span>
                    <span className="text-right">
                      <span className="block text-sm font-black">{m.my_score}:{m.opponent_score}</span>
                      {m.mode === "ranked" && <span className={cn("text-[11px] font-bold", m.points_delta >= 0 ? "text-[var(--bt-gold)]" : "text-[var(--bt-red)]")}>{m.points_delta >= 0 ? "+" : ""}{m.points_delta} BP</span>}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </GlassPanel>

          <GlassPanel className="p-5" data-testid="battle-room">
            <SectionTitle>{t("battle.privateRoom")}</SectionTitle>
            <p className="text-sm text-white/70">{t("battle.roomHint")}</p>
            <button type="button" disabled={busy || !data.playable || !!data.open_match_id} onClick={() => { setError(null); room.mutate(); }} data-testid="battle-create-room"
                    className="mt-4 inline-flex h-11 w-full items-center justify-center gap-2 rounded-xl bg-[var(--bt-blue)] text-sm font-black shadow-[var(--bt-glow-blue)] hover:brightness-110 disabled:opacity-50">
              <DoorOpen size={17} aria-hidden="true" /> {t("battle.createRoom")}
            </button>
            <form onSubmit={onJoin} className="mt-3 flex gap-2">
              <input value={code} onChange={(e) => setCode(e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 8))} placeholder={t("battle.roomCodePlaceholder")}
                     aria-label={t("battle.roomCodePlaceholder")} data-testid="battle-room-code" autoComplete="off" inputMode="text"
                     className="h-11 min-w-0 flex-1 rounded-xl bg-white/10 px-3 text-center font-mono text-base font-black tracking-[0.3em] ring-1 ring-white/15 placeholder:font-sans placeholder:tracking-normal placeholder:text-white/40 focus:outline-none focus:ring-[var(--bt-gold)]" />
              <button type="submit" disabled={busy || code.length < 4 || !!data.open_match_id} data-testid="battle-join-room"
                      className="h-11 rounded-xl bg-white/15 px-4 text-sm font-bold ring-1 ring-white/20 hover:bg-white/20 disabled:opacity-50">{t("battle.joinRoom")}</button>
            </form>
          </GlassPanel>
        </div>

        {/* ACHIEVEMENTS */}
        <GlassPanel className="p-5" data-testid="battle-achievements">
          <SectionTitle action={<Link href="/battle/erfolge" prefetch={false} className="flex items-center text-xs font-bold text-[var(--bt-gold)] hover:underline">{t("battle.showAll")}<ChevronRight size={14} /></Link>}>
            {t("battle.achievementsTitle")}
          </SectionTitle>
          <div className="flex gap-3 overflow-x-auto pb-1 [scrollbar-width:thin]">
            {data.achievements.map((a) => (
              <div key={a.key} className={cn("flex w-32 shrink-0 flex-col items-center rounded-2xl p-3 text-center ring-1", a.unlocked ? "bg-[var(--bt-gold)]/10 ring-[var(--bt-gold)]/40" : "bg-white/5 ring-white/10 opacity-70")}>
                <span className={cn("grid h-11 w-11 place-items-center rounded-full", a.unlocked ? "shadow-[var(--bt-glow-gold)]" : "bg-white/10 text-white/50")}>
                  {a.unlocked ? <BattleIcon size={30} /> : <Lock size={16} />}
                </span>
                <span className="mt-2 text-xs font-black leading-tight">{language === "uz" ? a.title_uz : a.title_de}</span>
                <span className="mt-1 text-[10px] text-white/55">{a.progress}/{a.goal}</span>
              </div>
            ))}
          </div>
        </GlassPanel>

        <StageRoad data={data} />
      </div>
      {showPicker && <AvatarPicker avatars={data.avatars} accent={theme.accent} player={player} onClose={closePicker} />}
    </>
  );
}

function StageRoad({ data }: { data: Home }) {
  const { t } = useTranslation();
  const current = data.themes.findIndex((th) => th.stage === data.rank.stage);
  return (
    <GlassPanel className="p-5" data-testid="battle-ladder">
      <SectionTitle>{t("battle.ladderTitle")}</SectionTitle>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {data.themes.map((th, i) => {
          const src = resolveThemeImage(th.mobile_image ?? th.desktop_image, API_URL);
          const reached = i <= current;
          const ranks = data.ladder.filter((r) => r.stage === th.stage);
          return (
            <div key={th.stage} className={cn("relative h-44 overflow-hidden rounded-2xl ring-1", i === current ? "ring-2 ring-[var(--bt-gold)] shadow-[var(--bt-glow-gold)]" : "ring-white/10")}>
              {src && (
                // eslint-disable-next-line @next/next/no-img-element -- small pre-sized WebP card
                <img src={src} alt="" loading="lazy" decoding="async" className={cn("absolute inset-0 h-full w-full object-cover", !reached && "grayscale")} />
              )}
              <div className="absolute inset-0 bg-gradient-to-t from-[#0b1426] via-[#101d35]/55 to-transparent" />
              <div className="absolute inset-x-0 bottom-0 p-3">
                <p className="text-lg font-black text-[var(--bt-gold)]">{th.stage}</p>
                <p className="text-sm font-black">{th.city}</p>
                <p className="text-[10px] font-semibold text-white/65">{ranks[0]?.at ?? 0} BP</p>
              </div>
              {!reached && <Lock size={16} className="absolute right-3 top-3 text-white/70" aria-label={t("battle.locked")} />}
            </div>
          );
        })}
      </div>
    </GlassPanel>
  );
}
