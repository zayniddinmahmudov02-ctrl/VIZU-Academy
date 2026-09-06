"use client";

import { Check } from "lucide-react";

import { usePanelSwitcher } from "@/features/auth/hooks/use-panel-switcher";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

interface Props {
  /** "admin" renders with the Admin Panel's own --admin-* design tokens
   * (its dropdown is a separate, isolated theme system — see
   * admin-header.tsx) so this doesn't look like a foreign component
   * dropped into it. Default matches the Student/Teacher Panel's shared
   * VIZU tokens (surface-card, accent-blue, ...). Same underlying
   * usePanelSwitcher() hook either way — only the classNames differ. */
  theme?: "admin" | "default";
}

/** Compact dropdown presentation of the same switcher (see
 * panel-switcher.tsx / use-panel-switcher.ts) for a header/user-menu —
 * Admin and Teacher headers both render this exact component (Student's
 * header uses the same hook directly, adapted to its own generic
 * DropdownMenu item list — see dashboard/header.tsx), never three
 * separate implementations of the switching logic. Renders nothing for
 * a plain STUDENT. */
export default function PanelSwitcherMenu({ theme = "default" }: Props) {
  const { t } = useTranslation();
  const { options, visible, current, go } = usePanelSwitcher();

  if (!visible) return null;

  const isAdmin = theme === "admin";

  return (
    <div className={cn("border-t pt-1.5", isAdmin ? "border-[var(--admin-border)]" : "border-surface-border")}>
      <p
        className={cn(
          "px-3.5 pb-1 pt-2 text-[10px] font-semibold uppercase tracking-wide",
          isAdmin ? "text-[var(--admin-text-muted)]" : "text-text-muted",
        )}
      >
        {t("settings.panelSwitcher")}
      </p>
      {options.map((option) => {
        const isCurrent = option.panel === current;
        return (
          <button
            key={option.panel}
            type="button"
            onClick={() => go(option)}
            aria-current={isCurrent ? "page" : undefined}
            className={cn(
              "flex min-h-11 w-full items-center gap-2.5 px-3.5 py-2 text-sm transition-colors",
              isCurrent
                ? isAdmin
                  ? "font-semibold text-[var(--admin-primary)]"
                  : "font-semibold text-accent-blue"
                : isAdmin
                  ? "text-[var(--admin-text-primary)] hover:bg-[var(--admin-hover)]"
                  : "text-text-primary hover:bg-surface-hover",
            )}
          >
            <option.icon size={15} className="shrink-0" />
            <span className="flex-1 truncate text-left">{t(option.labelKey)}</span>
            {isCurrent && <Check size={13} className="shrink-0" />}
          </button>
        );
      })}
    </div>
  );
}
