"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { LayoutGrid, LogOut, Menu, User } from "lucide-react";

import { logoutService } from "@/features/auth/services/auth.service";
import { CURRENT_USER_QUERY_KEY, useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { getRefreshToken, removeRefreshToken, removeToken } from "@/lib/token";

interface Props {
  onMenuClick?: () => void;
}

export default function AdminHeader({ onMenuClick }: Props) {
  const router = useRouter();
  const { user } = useCurrentUser();
  const [menuOpen, setMenuOpen] = useState(false);
  const queryClient = useQueryClient();

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
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between gap-3 border-b border-[var(--admin-border)] bg-[var(--admin-bg)]/95 px-4 backdrop-blur-md sm:px-6">
      <button
        onClick={onMenuClick}
        aria-label="Menü öffnen"
        className="flex h-9 w-9 items-center justify-center rounded-lg text-[var(--admin-text-secondary)] hover:bg-white/5 lg:hidden"
      >
        <Menu size={18} />
      </button>

      <div className="hidden lg:block" />

      <div className="relative flex items-center gap-2">
        <button
          onClick={() => router.push("/dashboard")}
          className="hidden items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium text-[var(--admin-text-secondary)] transition hover:bg-white/5 hover:text-[var(--admin-text-primary)] sm:flex"
        >
          <LayoutGrid size={14} />
          Student-Ansicht
        </button>

        <button
          onClick={() => setMenuOpen((v) => !v)}
          className="flex items-center gap-2 rounded-lg px-2 py-1.5 transition hover:bg-white/5"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--admin-primary)]/15 text-[var(--admin-primary)]">
            <User size={15} />
          </div>
          <span className="hidden text-sm font-medium text-[var(--admin-text-primary)] sm:block">
            {user?.username ?? "Admin"}
          </span>
        </button>

        {menuOpen && (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
            <div className="absolute right-0 top-12 z-20 w-48 overflow-hidden rounded-xl bg-[var(--admin-card)] py-1.5 shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-border-strong)]">
              <div className="border-b border-[var(--admin-border)] px-3.5 py-2.5">
                <p className="truncate text-sm font-medium text-[var(--admin-text-primary)]">
                  {user?.username}
                </p>
                <p className="truncate text-xs text-[var(--admin-text-muted)]">{user?.email}</p>
              </div>
              <button
                onClick={handleLogout}
                className="flex w-full items-center gap-2 px-3.5 py-2.5 text-sm text-[var(--admin-danger)] transition hover:bg-white/5"
              >
                <LogOut size={14} />
                Abmelden
              </button>
            </div>
          </>
        )}
      </div>
    </header>
  );
}
