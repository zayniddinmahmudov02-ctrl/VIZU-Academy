"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import {
  BookMarked, BookOpen, ClipboardCheck, ClipboardList, FileCheck2, GraduationCap, LayoutDashboard, LogOut, Menu, MessagesSquare, MonitorPlay,
  Settings, ShieldCheck, UsersRound, Users, X,
} from "lucide-react";

import Logo from "@/components/common/logo";
import Avatar from "@/components/ui/avatar";
import { logoutService } from "@/features/auth/services/auth.service";
import { CURRENT_USER_QUERY_KEY, useCurrentUser } from "@/features/auth/hooks/use-current-user";
import PanelSwitcherMenu from "@/features/auth/components/panel-switcher-menu";
import GlobalChatWidget from "@/features/global-chat/components/global-chat-widget";
import { useTeacherMe } from "@/features/teacher/hooks/use-teacher-me";
import { getRefreshToken, removeRefreshToken, removeToken } from "@/lib/token";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import TeacherGuard from "./teacher-guard";

interface NavItem {
  href: string;
  labelKey: string;
  icon: typeof Users;
  also?: string[];
  kontroll?: boolean;
}

/** The twelve sections; existing pages (Gruppen, Schreiben / Sprechen) stay where they were and are reached from here. */
export const TEACHER_NAV: NavItem[] = [
  { href: "/teacher", labelKey: "tpanel.navDashboard", icon: LayoutDashboard },
  { href: "/teacher/students", labelKey: "tpanel.navStudents", icon: Users },
  { href: "/teacher/groups", labelKey: "tpanel.navGroups", icon: UsersRound },
  { href: "/teacher/kurse", labelKey: "tpanel.navCourses", icon: BookOpen },
  { href: "/teacher/unterricht", labelKey: "tpanel.navLessons", icon: MonitorPlay },
  { href: "/teacher/aufgaben", labelKey: "tpanel.navTasks", icon: ClipboardList },
  { href: "/teacher/hausaufgaben", labelKey: "tpanel.navHomework", icon: ClipboardCheck },
  { href: "/teacher/pruefungen", labelKey: "tpanel.navExams", icon: FileCheck2, also: ["/teacher/schreiben", "/teacher/sprechen"] },
  { href: "/teacher/materialien", labelKey: "tpanel.navMaterials", icon: BookMarked },
  { href: "/teacher/nachrichten", labelKey: "tpanel.navMessages", icon: MessagesSquare },
  { href: "/teacher/kontroll", labelKey: "tpanel.navKontroll", icon: ShieldCheck, kontroll: true },
  { href: "/teacher/einstellungen", labelKey: "tpanel.navSettings", icon: Settings },
];

function matches(pathname: string, href: string): boolean {
  if (href === "/teacher") return pathname === "/teacher";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function isNavActive(pathname: string, item: Pick<NavItem, "href" | "also">): boolean {
  return matches(pathname, item.href) || (item.also ?? []).some((h) => matches(pathname, h));
}

function Nav({ onNavigate }: { onNavigate?: () => void }) {
  const { t } = useTranslation();
  const pathname = usePathname() ?? "";
  const me = useTeacherMe();
  const items = TEACHER_NAV.filter((item) => !item.kontroll || me.data?.can_access_student_control);
  return (
    <nav aria-label="Lehrer-Navigation" className="space-y-0.5" data-testid="teacher-nav">
      {items.map((item) => {
        const active = isNavActive(pathname, item);
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            aria-current={active ? "page" : undefined}
            data-testid={`teacher-nav-${item.href.split("/")[2] ?? "dashboard"}`}
            className={cn(
              "flex min-h-11 items-center gap-3 rounded-xl px-3 text-sm font-medium transition-colors",
              active ? "bg-accent-blue/10 text-accent-blue" : "text-text-secondary hover:bg-surface-hover hover:text-text-primary",
            )}
          >
            <item.icon size={18} className="shrink-0" />
            <span className="truncate">{t(item.labelKey)}</span>
          </Link>
        );
      })}
    </nav>
  );
}

export default function TeacherShell({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation();
  const pathname = usePathname();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user } = useCurrentUser();
  const displayName = user ? [user.firstName, user.lastName].filter(Boolean).join(" ") || user.username : "";
  const [menuOpen, setMenuOpen] = useState(false);
  // the drawer belongs to the page it was opened on: any navigation closes it (no effect needed)
  const [drawerPath, setDrawerPath] = useState<string | null>(null);
  const drawer = drawerPath !== null && drawerPath === pathname;
  const setDrawer = (open: boolean) => setDrawerPath(open ? pathname : null);

  async function handleLogout() {
    const refreshToken = getRefreshToken();
    removeToken();
    removeRefreshToken();
    queryClient.removeQueries({ queryKey: CURRENT_USER_QUERY_KEY });
    router.push("/login");
    if (refreshToken) {
      try {
        await logoutService(refreshToken);
      } catch {
        // Local session is already cleared regardless.
      }
    }
  }

  const brand = (
    <div className="flex items-center gap-2.5">
      <Logo size={34} showText={false} />
      <div>
        <p className="text-sm font-extrabold leading-tight text-text-primary">VIZU <span className="text-accent-blue">{t("teacher.nav")}</span></p>
        <p className="flex items-center gap-1 text-[10px] font-medium uppercase tracking-wide text-text-muted"><GraduationCap size={11} />{t("teacher.nav")}</p>
      </div>
    </div>
  );

  return (
    <TeacherGuard>
      <div className="flex min-h-screen bg-surface-bg">
        <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-surface-border bg-surface-card lg:flex">
          <div className="border-b border-surface-border px-5 py-5">{brand}</div>
          <div className="flex-1 overflow-y-auto px-3 py-4"><Nav /></div>
        </aside>

        {drawer && (
          <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true" aria-label={t("tpanel.menu")}
               onKeyDown={(e) => { if (e.key === "Escape") setDrawer(false); }}>
            <div className="absolute inset-0 bg-black/40" onClick={() => setDrawer(false)} />
            <div className="absolute inset-y-0 left-0 flex w-72 max-w-[85vw] flex-col bg-surface-card shadow-[var(--shadow-lg)]">
              <div className="flex items-center justify-between border-b border-surface-border px-4 py-4">
                {brand}
                <button type="button" onClick={() => setDrawer(false)} aria-label={t("tpanel.closeMenu")} className="rounded-lg p-2 hover:bg-surface-hover"><X size={18} /></button>
              </div>
              <div className="flex-1 overflow-y-auto px-3 py-4"><Nav onNavigate={() => setDrawer(false)} /></div>
            </div>
          </div>
        )}

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="safe-top sticky top-0 z-20 flex h-16 items-center justify-between gap-3 border-b border-surface-border bg-surface-card/95 px-4 backdrop-blur-md sm:px-6">
            <div className="flex items-center gap-2">
              <button type="button" onClick={() => setDrawer(true)} className="rounded-lg p-2 hover:bg-surface-hover lg:hidden" aria-label={t("tpanel.menu")} data-testid="teacher-menu-button">
                <Menu size={20} />
              </button>
              <div className="lg:hidden">{brand}</div>
            </div>

            <div className="relative flex items-center gap-2">
              <button onClick={() => setMenuOpen((v) => !v)} className="flex items-center gap-2 rounded-full px-1.5 py-1 transition-colors hover:bg-surface-hover" data-testid="teacher-user-menu">
                <span className="hidden text-sm font-medium text-text-primary sm:block">{displayName}</span>
                <Avatar src={user?.profileImage ?? undefined} name={displayName} size={32} />
              </button>
              {menuOpen && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
                  <div className="absolute right-0 top-12 z-20 w-56 overflow-hidden rounded-xl bg-surface-card py-1.5 shadow-[var(--shadow-lg)] ring-1 ring-surface-border">
                    <div className="flex items-center gap-2.5 border-b border-surface-border px-3.5 py-2.5">
                      <Avatar src={user?.profileImage ?? undefined} name={displayName} size={32} />
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-text-primary">{displayName}</p>
                        <p className="truncate text-xs text-text-muted">{user?.username}</p>
                      </div>
                    </div>
                    <PanelSwitcherMenu />
                    <button onClick={handleLogout} className="flex w-full items-center gap-2 border-t border-surface-border px-3.5 py-2.5 text-sm text-danger transition-colors hover:bg-surface-hover">
                      <LogOut size={14} />
                      {t("tpanel.logout")}
                    </button>
                  </div>
                </>
              )}
            </div>
          </header>

          <main className="safe-bottom mx-auto w-full max-w-6xl px-4 pb-24 pt-6 sm:px-6 lg:pt-8">{children}</main>
        </div>
        <GlobalChatWidget />
      </div>
    </TeacherGuard>
  );
}
