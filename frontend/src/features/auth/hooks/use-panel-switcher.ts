"use client";

import { useRouter, usePathname } from "next/navigation";
import { GraduationCap, ShieldCheck, User } from "lucide-react";

import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { setActivePanel, type ActivePanel } from "@/lib/active-panel";

export interface PanelOption {
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

/** The single source of truth for "which panels can this user switch to,
 * and which one are they on right now" — backs every rendering of the
 * switcher (Settings' full card, and the compact header/user-menu
 * dropdown in Admin/Teacher/Student headers). Never write a second copy
 * of this role-filtering logic; give it a new presentation instead (see
 * panel-switcher.tsx vs panel-switcher-menu.tsx).
 *
 * Visibility here is purely additive UX — every panel's real gate is its
 * own backend-enforced dependency (AuthGuard/TeacherGuard/AdminGuard +
 * require_teacher_panel_access/require_super_admin server-side); hiding
 * an option here never grants or revokes access. */
export function usePanelSwitcher() {
  const { user } = useCurrentUser();
  const router = useRouter();
  const pathname = usePathname();

  const options = !user
    ? []
    : ALL_OPTIONS.filter((opt) => {
        if (opt.panel === "student") return true;
        if (opt.panel === "teacher") return user.role === "TEACHER" || user.role === "SUPER_ADMIN";
        if (opt.panel === "admin") return user.role === "SUPER_ADMIN";
        return false;
      });

  // A plain STUDENT has no second panel to switch to — every caller
  // renders nothing at all in that case (not an empty/disabled section).
  const visible = options.length > 1;

  const current = options.find((opt) => pathname.startsWith(opt.href))?.panel ?? "student";

  function go(option: PanelOption) {
    setActivePanel(option.panel);
    router.push(option.href);
  }

  return { options, visible, current, go };
}
