"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bell, BookOpen, LayoutDashboard, Medal, Trophy } from "lucide-react";

import BattleIcon from "@/components/icons/battle-icon";
import PlayerAvatar from "@/features/battle/components/player-avatar";
import { PointsChip, StageChip } from "@/features/battle/components/battle-ui";
import { useBattleHome } from "@/features/battle/hooks/use-battle-home";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

const ITEMS = [
  { href: "/dashboard", key: "navDashboard", icon: LayoutDashboard, exact: true },
  { href: "/kurse", key: "navLearn", icon: BookOpen, exact: false },
  { href: "/battle", key: "navBattle", icon: BattleIcon, exact: true },
  { href: "/battle/rangliste", key: "navLeaderboard", icon: Trophy, exact: false },
  { href: "/battle/erfolge", key: "navAchievements", icon: Medal, exact: false },
];

function isActive(pathname: string, href: string, exact: boolean) {
  if (href === "/battle") return pathname === "/battle" || pathname.startsWith("/battle/match");
  return exact ? pathname === href : pathname === href || pathname.startsWith(`${href}/`);
}

/** One navigation for every Battle page: glass bar on desktop, compact top bar + thumb tab bar on phones. */
export default function BattleNav() {
  const { t } = useTranslation();
  const pathname = usePathname() ?? "";
  const { data } = useBattleHome();
  const inMatch = pathname.startsWith("/battle/match");
  const player = data?.player;

  return (
    <>
      <header className={cn("sticky top-0 z-40 px-3 pt-3 sm:px-5", inMatch && "max-md:hidden landscape-short:hidden")} data-testid="battle-nav">
        <div className="bt-glass-strong mx-auto flex h-14 max-w-[1440px] items-center gap-3 rounded-2xl px-3 sm:h-16 sm:px-4">
          <Link href="/battle" prefetch={false} className="flex shrink-0 items-center gap-2" aria-label="VIZU DEUTSCH Battle">
            <BattleIcon size={32} title="VIZU DEUTSCH BATTLE" />
            <span className="hidden text-sm font-black leading-none tracking-wider sm:block">
              VIZU <span className="text-[var(--bt-gold)]">DEUTSCH</span>
            </span>
          </Link>

          <nav className="ml-2 hidden items-center gap-1 md:flex" aria-label="Battle">
            {ITEMS.map(({ href, key, icon: Icon, exact }) => {
              const active = isActive(pathname, href, exact);
              return (
                <Link key={href} href={href} prefetch={false} aria-current={active ? "page" : undefined} data-testid={`battle-nav-${key}`}
                      className={cn("flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm font-bold transition-colors",
                        active ? "bg-[var(--bt-gold)]/15 text-[var(--bt-gold)] ring-1 ring-[var(--bt-gold)]/40" : "text-white/75 hover:bg-white/10 hover:text-white")}>
                  <Icon size={16} aria-hidden="true" /> <span className="max-lg:sr-only">{t(`battle.${key}`)}</span>
                </Link>
              );
            })}
          </nav>

          <div className="ml-auto flex items-center gap-2">
            {player && (
              <>
                <StageChip stage={player.stage} className="max-[380px]:hidden" />
                <PointsChip points={player.points} />
              </>
            )}
            <Link href="/notifications" prefetch={false} aria-label={t("battle.navNotifications")} className="grid h-9 w-9 place-items-center rounded-xl text-white/80 hover:bg-white/10 hover:text-white">
              <Bell size={18} aria-hidden="true" />
            </Link>
            {player && (
              <Link href="/battle?avatar=1" prefetch={false} className="flex items-center gap-2 rounded-xl py-1 pl-1 pr-2 hover:bg-white/10" aria-label={t("battle.changeAvatar")} data-testid="battle-nav-profile">
                <span className="grid h-9 w-9 place-items-center overflow-hidden rounded-full bg-[var(--bt-dark)] ring-2 ring-[var(--bt-blue)]">
                  <PlayerAvatar player={player} size={36} round />
                </span>
                <span className="hidden max-w-[120px] truncate text-sm font-bold lg:block">{player.name}</span>
              </Link>
            )}
          </div>
        </div>
      </header>

      {!inMatch && (
        <nav className="bt-glass-strong fixed inset-x-2 bottom-2 z-40 grid grid-cols-5 rounded-2xl px-1 py-1.5 md:hidden" aria-label="Battle mobil" data-testid="battle-tabbar"
             style={{ paddingBottom: "max(0.375rem, env(safe-area-inset-bottom))" }}>
          {ITEMS.map(({ href, key, icon: Icon, exact }) => {
            const active = isActive(pathname, href, exact);
            return (
              <Link key={href} href={href} prefetch={false} aria-current={active ? "page" : undefined}
                    className={cn("flex min-h-12 flex-col items-center justify-center gap-0.5 rounded-xl text-[10px] font-bold", active ? "text-[var(--bt-gold)]" : "text-white/70")}>
                <Icon size={20} aria-hidden="true" className={cn(active && "drop-shadow-[0_0_8px_rgba(242,196,91,0.8)]")} />
                <span className="max-w-full truncate px-0.5">{t(`battle.${key}`)}</span>
              </Link>
            );
          })}
        </nav>
      )}
    </>
  );
}
