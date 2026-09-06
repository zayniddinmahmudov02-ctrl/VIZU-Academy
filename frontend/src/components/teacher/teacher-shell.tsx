"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { ClipboardList, GraduationCap, LayoutDashboard, LogOut, Mic, PenLine, Users } from "lucide-react";

import Logo from "@/components/common/logo";
import Avatar from "@/components/ui/avatar";
import { logoutService } from "@/features/auth/services/auth.service";
import { CURRENT_USER_QUERY_KEY, useCurrentUser } from "@/features/auth/hooks/use-current-user";
import PanelSwitcherMenu from "@/features/auth/components/panel-switcher-menu";
import { getRefreshToken, removeRefreshToken, removeToken } from "@/lib/token";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import TeacherGuard from "./teacher-guard";

const NAV = [
  { href: "/teacher", labelKey: "teacher.overviewTitle", icon: LayoutDashboard },
  { href: "/teacher/students", labelKey: "teacher.navStudents", icon: Users },
  { href: "/teacher/homework", labelKey: "teacher.navHomework", icon: ClipboardList },
  { href: "/teacher/schreiben", labelKey: "teacher.navSchreiben", icon: PenLine },
  { href: "/teacher/sprechen", labelKey: "teacher.navSprechen", icon: Mic },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/teacher") return pathname === "/teacher";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export default function TeacherShell({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation();
  const pathname = usePathname();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user } = useCurrentUser();
  const displayName = user ? [user.firstName, user.lastName].filter(Boolean).join(" ") || user.username : "";
  const [menuOpen, setMenuOpen] = useState(false);

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

  return (
    <TeacherGuard>
      <div className="min-h-screen bg-surface-bg">
        <header className="safe-top sticky top-0 z-20 flex h-16 items-center justify-between gap-3 border-b border-surface-border bg-surface-card/95 px-4 backdrop-blur-md sm:px-6">
          <div className="flex items-center gap-2.5">
            <Logo size={34} showText={false} />
            <div>
              <p className="text-sm font-extrabold leading-tight text-text-primary">
                VIZU <span className="text-accent-blue">{t("teacher.nav")}</span>
              </p>
              <p className="flex items-center gap-1 text-[10px] font-medium uppercase tracking-wide text-text-muted">
                <GraduationCap size={11} />
                {t("teacher.nav")}
              </p>
            </div>
          </div>

          <div className="relative flex items-center gap-2">
            <button
              onClick={() => setMenuOpen((v) => !v)}
              className="flex items-center gap-2 rounded-full px-1.5 py-1 transition-colors hover:bg-surface-hover"
            >
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
                      <p className="truncate text-xs text-text-muted">{user?.email}</p>
                    </div>
                  </div>

                  <PanelSwitcherMenu />

                  <button
                    onClick={handleLogout}
                    className="flex w-full items-center gap-2 border-t border-surface-border px-3.5 py-2.5 text-sm text-danger transition-colors hover:bg-surface-hover"
                  >
                    <LogOut size={14} />
                    Abmelden
                  </button>
                </div>
              </>
            )}
          </div>
        </header>

        <nav
          aria-label="Lehrer-Navigation"
          className="flex gap-1 overflow-x-auto border-b border-surface-border bg-surface-card px-4 sm:px-6"
        >
          {NAV.map((item) => {
            const active = isActive(pathname, item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex min-h-11 shrink-0 items-center gap-2 border-b-2 px-3 text-sm font-medium transition-colors",
                  active
                    ? "border-accent-blue text-accent-blue"
                    : "border-transparent text-text-secondary hover:text-text-primary",
                )}
              >
                <item.icon size={16} />
                {t(item.labelKey)}
              </Link>
            );
          })}
        </nav>

        <main className="safe-bottom mx-auto max-w-5xl px-4 py-8 sm:px-6">{children}</main>
      </div>
    </TeacherGuard>
  );
}
