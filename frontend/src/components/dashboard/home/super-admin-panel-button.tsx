"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Wrench } from "lucide-react";

import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { useTranslation } from "@/lib/i18n/use-translation";
import { fadeInUp } from "@/lib/motion";

/** Visible only to SUPER_ADMIN — renders nothing (not hidden, not
 *  disabled) for every other role, and nothing while the role is still
 *  loading, so there's no flash of a button a non-admin can click and no
 *  empty gap left behind for anyone else. */
export default function SuperAdminPanelButton() {
  const { user } = useCurrentUser();
  const { t } = useTranslation();

  if (user?.role !== "SUPER_ADMIN") {
    return null;
  }

  return (
    <motion.div variants={fadeInUp} initial="hidden" animate="show">
      <Link
        href="/admin"
        className="group flex items-center justify-between gap-4 rounded-card bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 px-6 py-5 text-white shadow-[var(--shadow-card)] ring-1 ring-white/10 transition-all duration-300 hover:shadow-[var(--shadow-card-hover)] sm:px-7"
      >
        <div className="flex items-center gap-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-accent-gold to-amber-400 text-slate-900 shadow-[var(--shadow-3d-soft)]">
            <Wrench size={20} />
          </div>

          <div>
            <p className="text-base font-bold">{t("dashboard.superAdminPanel")}</p>
            <p className="mt-0.5 text-sm text-white/70">{t("dashboard.superAdminPanelSubtitle")}</p>
          </div>
        </div>

        <ArrowRight
          size={18}
          className="shrink-0 text-white/60 transition-transform duration-200 group-hover:translate-x-1 group-hover:text-white"
        />
      </Link>
    </motion.div>
  );
}
