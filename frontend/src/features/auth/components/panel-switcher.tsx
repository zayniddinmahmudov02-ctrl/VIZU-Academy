"use client";

import { useRouter } from "next/navigation";
import { usePathname } from "next/navigation";
import { Check, GraduationCap, ShieldCheck, User } from "lucide-react";

import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { setActivePanel, type ActivePanel } from "@/lib/active-panel";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

interface PanelOption {
  panel: ActivePanel;
  href: string;
  icon: typeof User;
  labelKey: string;
  descriptionKey: string;
}

const ALL_OPTIONS: PanelOption[] = [
  { panel: "student", href: "/dashboard", icon: User, labelKey: "settings.panelStudent", descriptionKey: "settings.panelStudentDesc" },
  { panel: "teacher", href: "/teacher", icon: GraduationCap, labelKey: "settings.panelTeacher", descriptionKey: "settings.panelTeacherDesc" },
  { panel: "admin", href: "/admin", icon: ShieldCheck, labelKey: "settings.panelAdmin", descriptionKey: "settings.panelAdminDesc" },
];

/** Source of truth for panel switching lives here, not the header — see
 * the spec's own "Settings → Panel almashtirish" requirement. Visibility
 * is purely additive to whatever role gate already protects each panel
 * (AuthGuard/TeacherGuard/AdminGuard, backend-enforced regardless of what
 * this component shows) — hiding an option here never grants or revokes
 * access, it only avoids offering a link that would immediately bounce.
 *
 * A plain STUDENT has no second panel to switch to, so this component
 * renders nothing at all for them (not an empty/disabled section) —
 * exactly the "ko'rinmasin" requirement, not just an inert one. */
export default function PanelSwitcher() {
  const { t } = useTranslation();
  const { user } = useCurrentUser();
  const router = useRouter();
  const pathname = usePathname();

  if (!user) return null;

  const options = ALL_OPTIONS.filter((opt) => {
    if (opt.panel === "student") return true;
    if (opt.panel === "teacher") return user.role === "TEACHER" || user.role === "SUPER_ADMIN";
    if (opt.panel === "admin") return user.role === "SUPER_ADMIN";
    return false;
  });

  // Nothing beyond the student's own panel to offer — stay hidden
  // entirely (see the docstring above).
  if (options.length <= 1) return null;

  function go(option: PanelOption) {
    setActivePanel(option.panel);
    router.push(option.href);
  }

  const current = options.find((opt) => pathname.startsWith(opt.href))?.panel ?? "student";

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
