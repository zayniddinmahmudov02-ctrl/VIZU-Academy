"use client";

import { Check } from "lucide-react";

import { usePanelSwitcher } from "@/features/auth/hooks/use-panel-switcher";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

/** Settings' full-card presentation of the switcher — the source of
 * truth per the spec ("Settings → Panel almashtirish"). Same shared
 * usePanelSwitcher() hook as the compact header dropdown
 * (panel-switcher-menu.tsx); only the layout differs. Renders nothing
 * at all for a plain STUDENT (see the hook's `visible` flag) — not an
 * empty/disabled section. */
export default function PanelSwitcher() {
  const { t } = useTranslation();
  const { options, visible, current, go } = usePanelSwitcher();

  if (!visible) return null;

  return (
    <section className="rounded-card bg-surface-card p-7 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
      <h2 className="text-lg font-bold text-text-primary">{t("settings.panelSwitcher")}</h2>
      <p className="mt-1 text-sm text-text-secondary">{t("settings.panelSwitcherBody")}</p>

      <div className="mt-5 space-y-2">
        {options.map((option) => {
          const isCurrent = option.panel === current;
          return (
            <button
              key={option.panel}
              type="button"
              onClick={() => go(option)}
              aria-current={isCurrent ? "page" : undefined}
              className={cn(
                "flex min-h-11 w-full items-center gap-3 rounded-2xl p-4 text-left transition-colors",
                isCurrent ? "bg-accent-blue/10 ring-1 ring-accent-blue/30" : "bg-surface-hover hover:bg-surface-hover/70",
              )}
            >
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-surface-card text-accent-blue ring-1 ring-surface-border">
                <option.icon size={18} />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-sm font-semibold text-text-primary">{t(option.labelKey)}</span>
                <span className="block truncate text-xs text-text-secondary">{t(option.descriptionKey)}</span>
              </span>
              {isCurrent && (
                <span className="flex shrink-0 items-center gap-1 text-xs font-bold text-accent-blue">
                  <Check size={14} />
                  {t("settings.panelCurrent")}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </section>
  );
}
