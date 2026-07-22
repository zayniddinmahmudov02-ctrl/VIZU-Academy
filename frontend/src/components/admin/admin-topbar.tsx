"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { LogOut, Search, X } from "lucide-react";

import { adminNavItems } from "@/constants/admin-nav";
import { useLanguageStore } from "@/store/language-store";
import { removeToken } from "@/lib/storage";
import type { CurrentUser } from "@/features/auth/types/user";

interface Props {
  user: CurrentUser | null;
}

export default function AdminTopbar({ user }: Props) {
  const router = useRouter();
  const { language, setLanguage } = useLanguageStore();

  const [now, setNow] = useState<Date | null>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    setNow(new Date());
    const interval = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  const results = useMemo(() => {
    if (!query.trim()) return [];
    const q = query.trim().toLowerCase();
    return adminNavItems.filter((item) => item.label.toLowerCase().includes(q)).slice(0, 6);
  }, [query]);

  const timeLabel = now
    ? new Intl.DateTimeFormat(language === "uz" ? "uz-UZ" : "de-DE", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      }).format(now)
    : "";
  const dateLabel = now
    ? new Intl.DateTimeFormat(language === "uz" ? "uz-UZ" : "de-DE", {
        weekday: "short",
        day: "numeric",
        month: "short",
      }).format(now)
    : "";

  function handleLogout() {
    removeToken();
    router.push("/login");
  }

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-[var(--admin-border)] bg-[var(--admin-bg)]/85 px-4 backdrop-blur-xl sm:px-6">
      {/* Search */}
      <div className="relative w-full max-w-sm">
        <div className="flex h-10 items-center gap-2.5 rounded-xl border border-[var(--admin-border)] bg-white/[0.03] px-3.5">
          <Search size={14} className="shrink-0 text-[var(--admin-text-muted)]" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search modules…"
            className="w-full bg-transparent text-sm text-white outline-none placeholder:text-[var(--admin-text-muted)]"
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery("")}
              aria-label="Clear search"
              className="text-[var(--admin-text-muted)] hover:text-white"
            >
              <X size={14} />
            </button>
          )}
        </div>

        {results.length > 0 && (
          <div className="admin-glass absolute left-0 right-0 top-12 z-30 overflow-hidden rounded-xl shadow-[var(--admin-shadow-card)]">
            {results.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setQuery("")}
                className="flex items-center gap-2.5 px-3.5 py-2.5 text-sm text-[var(--admin-text-secondary)] transition-colors hover:bg-white/5 hover:text-white"
              >
                <item.icon size={15} />
                {item.label}
              </Link>
            ))}
          </div>
        )}
      </div>

      <div className="ml-auto flex shrink-0 items-center gap-2 sm:gap-3">
        {/* Live time */}
        <div className="hidden flex-col items-end leading-tight sm:flex">
          <span className="text-xs font-semibold tabular-nums text-white">{timeLabel}</span>
          <span className="text-[10px] capitalize text-[var(--admin-text-muted)]">{dateLabel}</span>
        </div>

        <div className="hidden h-8 w-px bg-[var(--admin-border)] sm:block" />

        {/* Language toggle */}
        <div className="flex items-center gap-1 rounded-full border border-[var(--admin-border)] bg-white/[0.03] p-1">
          <button
            type="button"
            onClick={() => setLanguage("de")}
            className={`rounded-full px-2.5 py-1 text-[11px] font-bold transition-colors ${
              language === "de" ? "bg-[var(--admin-primary)] text-white" : "text-[var(--admin-text-muted)]"
            }`}
          >
            DE
          </button>
          <button
            type="button"
            onClick={() => setLanguage("uz")}
            className={`rounded-full px-2.5 py-1 text-[11px] font-bold transition-colors ${
              language === "uz" ? "bg-[var(--admin-primary)] text-white" : "text-[var(--admin-text-muted)]"
            }`}
          >
            UZ
          </button>
        </div>

        {/* Exit to student view */}
        <Link
          href="/dashboard"
          className="hidden rounded-xl border border-[var(--admin-border)] px-3 py-2 text-xs font-semibold text-[var(--admin-text-secondary)] transition-colors hover:bg-white/5 hover:text-white sm:block"
        >
          Exit Admin
        </Link>

        {/* Logout */}
        <button
          type="button"
          onClick={handleLogout}
          aria-label="Log out"
          className="flex h-10 w-10 items-center justify-center rounded-xl border border-[var(--admin-border)] text-[var(--admin-text-secondary)] transition-colors hover:border-[var(--admin-danger)]/40 hover:bg-[var(--admin-danger)]/10 hover:text-[var(--admin-danger)]"
        >
          <LogOut size={14} />
        </button>
      </div>
    </header>
  );
}
