"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { adminNavItems } from "@/constants/admin-nav";
import type { CurrentUser } from "@/features/auth/types/user";

interface Props {
  user: CurrentUser | null;
}

export default function AdminSidebar({ user }: Props) {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();

  return (
    <aside
      className={`sticky top-0 z-30 hidden h-screen shrink-0 border-r border-[var(--admin-border)] bg-[var(--admin-card)]/70 backdrop-blur-xl transition-all duration-300 lg:flex lg:flex-col ${
        collapsed ? "w-[68px]" : "w-[235px]"
      }`}
    >
      {/* Logo */}
      <div className="flex h-16 items-center gap-2.5 border-b border-[var(--admin-border)] px-4">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--admin-primary)] to-[var(--admin-secondary)] text-sm font-extrabold text-white shadow-[0_4px_16px_-4px_rgba(91,91,248,0.6)]">
          V
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <p className="truncate text-sm font-bold text-[var(--admin-text-primary)]">VIZU Admin</p>
            <p className="truncate text-[10px] font-medium uppercase tracking-wide text-[var(--admin-text-muted)]">
              Super Admin Panel
            </p>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-0.5 overflow-y-auto px-2.5 py-4">
        {adminNavItems.map((item) => {
          const active =
            pathname === item.href ||
            (item.href !== "/admin" && pathname.startsWith(`${item.href}/`));
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              title={collapsed ? item.label : undefined}
              className={`group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors duration-200 ${
                collapsed ? "justify-center" : ""
              } ${
                active
                  ? "bg-gradient-to-r from-[var(--admin-primary)]/20 to-[var(--admin-secondary)]/10 text-white ring-1 ring-[var(--admin-primary)]/30"
                  : "text-[var(--admin-text-secondary)] hover:bg-white/5 hover:text-white"
              }`}
            >
              <Icon size={16} className={active ? "text-[var(--admin-primary)]" : ""} />
              {!collapsed && <span className="truncate">{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <button
        type="button"
        onClick={() => setCollapsed((c) => !c)}
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        className="mx-2.5 mb-2 flex items-center justify-center gap-2 rounded-xl border border-[var(--admin-border)] py-2 text-xs font-semibold text-[var(--admin-text-secondary)] transition-colors hover:bg-white/5 hover:text-white"
      >
        {collapsed ? (
          <ChevronRight size={14} />
        ) : (
          <>
            <ChevronLeft size={14} /> Collapse
          </>
        )}
      </button>

      {/* Footer — Super Admin profile */}
      <div className="border-t border-[var(--admin-border)] p-3">
        <div
          className={`flex items-center gap-3 rounded-xl bg-white/[0.03] p-2.5 ${collapsed ? "justify-center" : ""}`}
        >
          <div className="relative shrink-0">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-[var(--admin-primary)] to-[var(--admin-secondary)] text-xs font-bold text-white">
              {(user?.username ?? "SA").slice(0, 2).toUpperCase()}
            </div>
            <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-[var(--admin-accent)] ring-2 ring-[var(--admin-card)]" />
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <p className="truncate text-xs font-semibold text-white">
                {user?.username ?? "Loading…"}
              </p>
              <p className="truncate text-[10px] text-[var(--admin-text-muted)]">
                {user?.role ?? ""}
              </p>
            </div>
          )}
        </div>
        {!collapsed && user?.email && (
          <p className="mt-2 truncate px-1 text-[10px] text-[var(--admin-text-muted)]">
            {user.email}
          </p>
        )}
      </div>
    </aside>
  );
}
