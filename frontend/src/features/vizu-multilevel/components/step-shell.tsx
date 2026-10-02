"use client";

import type { ReactNode } from "react";
import { motion } from "framer-motion";

import { fadeInUp } from "@/lib/motion";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import { VIZU_MULTILEVEL_SKILLS, getSkillIndex, type VizuMultilevelSkillMeta } from "../constants/skills";
import VizuMultilevelTimer from "./timer";

interface Props {
  skill: VizuMultilevelSkillMeta;
  children: ReactNode;
  footer: ReactNode;
  /** Seconds left in this competency, computed by the server. The timer is
   * only rendered once it is known. */
  initialSeconds?: number;
  /** Auto-submits whatever is answered so far the instant the countdown
   * hits 0. */
  onTimerExpire?: () => void;
  /** Persistent "Testni yakunlash" button next to the timer — lets the
   * student end the CURRENT competency at any time, even with unanswered
   * questions (they score 0). Opens the shared confirm dialog (see
   * finish-confirm-dialog.tsx). */
  onFinishClick?: () => void;
}

/** Shared layout for the four competency steps (Lesen/Hören/Schreiben/
 * Sprechen) — competency-colored header, step progress, the server-driven
 * countdown, and a footer for the step's own action button. */
export default function VizuMultilevelStepShell({
  skill,
  children,
  footer,
  initialSeconds,
  onTimerExpire,
  onFinishClick,
}: Props) {
  const { t } = useTranslation();
  const Icon = skill.icon;
  const currentIndex = getSkillIndex(skill.skill);

  return (
    <motion.div variants={fadeInUp} initial="hidden" animate="show" className="mx-auto max-w-2xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-600 text-white shadow-md",
            )}
          >
            <Icon size={20} />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
              {t("vizuMultilevel.step", { current: currentIndex + 1, total: VIZU_MULTILEVEL_SKILLS.length })}
            </p>
            <h1 className="text-lg font-bold text-text-primary">{t(skill.labelKey)}</h1>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {initialSeconds !== undefined && (
            <VizuMultilevelTimer key={skill.skill} initialSeconds={initialSeconds} onExpire={onTimerExpire} />
          )}
          {onFinishClick && (
            <button
              type="button"
              onClick={onFinishClick}
              className="rounded-full px-3 py-1.5 text-xs font-semibold text-blue-700 ring-1 ring-blue-200 transition-all hover:bg-blue-50 active:scale-95 dark:text-blue-300 dark:ring-blue-500/40 dark:hover:bg-blue-500/10"
            >
              {t("vizuMultilevel.finishLabel")}
            </button>
          )}
        </div>
      </div>

      <div className="flex items-center gap-1.5">
        {VIZU_MULTILEVEL_SKILLS.map((s, i) => (
          <div
            key={s.skill}
            className={cn(
              "h-1.5 flex-1 rounded-full transition-colors",
              i < currentIndex ? "bg-blue-600" : i === currentIndex ? "bg-orange-500" : "bg-surface-border",
            )}
          />
        ))}
      </div>

      <div className="rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border sm:p-8">
        {children}
      </div>

      <div className="flex justify-end">{footer}</div>
    </motion.div>
  );
}
