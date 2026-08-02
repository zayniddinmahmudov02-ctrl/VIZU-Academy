"use client";

import { useRouter } from "next/navigation";
import { Crown, LogOut, Menu, Search, Settings, User } from "lucide-react";

import Avatar from "@/components/ui/avatar";
import DropdownMenu from "@/components/ui/dropdown-menu";
import ThemeToggle from "@/components/ui/theme-toggle";
import CalendarDropdown from "@/features/calendar/components/calendar-dropdown";
import NotificationDropdown from "@/features/notifications/components/notification-dropdown";
import { useTranslation } from "@/lib/i18n/use-translation";
import { removeToken } from "@/lib/token";

type Props = {
  onMenuClick?: () => void;
};

export default function Header({ onMenuClick }: Props) {
  const router = useRouter();
  const { t } = useTranslation();

  function handleLogout() {
    removeToken();
    router.push("/login");
  }

  return (
    <header className="sticky top-4 z-20 mx-4 mt-4 flex h-16 items-center justify-between gap-3 rounded-card px-4 glass shadow-[var(--shadow-card)] ring-1 ring-surface-border sm:px-5">
      {/* Left */}
      <div className="flex min-w-0 flex-1 items-center gap-3">
        <button
          onClick={onMenuClick}
          aria-label={t("header.menuOpen")}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-card text-text-secondary shadow-[var(--shadow-3d-soft)] ring-1 ring-surface-border transition-all duration-200 hover:-translate-y-px hover:text-accent-blue active:translate-y-0 lg:hidden"
        >
          <Menu size={16} />
        </button>

        {/* Search */}
        <div className="flex h-11 w-full max-w-sm items-center gap-2.5 rounded-full bg-surface-card px-4 shadow-[var(--shadow-3d-soft)] ring-1 ring-surface-border">
          <Search size={15} className="shrink-0 text-text-muted" />
          <input
            type="text"
            placeholder={t("header.searchPlaceholder")}
            className="w-full bg-transparent text-sm text-text-primary outline-none placeholder:text-text-muted"
          />
          <kbd className="hidden shrink-0 items-center gap-0.5 rounded-md bg-surface-hover px-1.5 py-0.5 text-[10px] font-semibold text-text-muted sm:flex">
            Ctrl + K
          </kbd>
        </div>
      </div>

      {/* Right */}
      <div className="flex shrink-0 items-center gap-2">
        <div className="hidden sm:block">
          <CalendarDropdown />
        </div>

        <NotificationDropdown />

        <ThemeToggle variant="icon" className="hidden sm:flex" />

        <DropdownMenu
          align="end"
          trigger={
            <span className="flex items-center gap-2.5 rounded-full bg-surface-card py-1 pl-1 pr-3 shadow-[var(--shadow-3d-soft)] ring-1 ring-surface-border transition-all duration-200 hover:-translate-y-px hover:ring-accent-gold/40">
              <Avatar name="Zayniddin" size={34} />
              <span className="hidden text-left lg:block">
                <span className="block text-xs font-semibold text-text-primary">Zayniddin</span>
                <span className="flex items-center gap-1 text-[11px] text-text-secondary">
                  <Crown size={11} className="text-accent-gold" /> {t("header.learner")}
                </span>
              </span>
            </span>
          }
          items={[
            { label: t("sidebar.profile"), icon: User, onClick: () => router.push("/profile") },
            { label: t("sidebar.settings"), icon: Settings, onClick: () => router.push("/settings") },
            { label: t("header.logout"), icon: LogOut, onClick: handleLogout, danger: true },
          ]}
        />
      </div>
    </header>
  );
}
