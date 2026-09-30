"use client";

import type { ReactNode } from "react";
import { motion } from "framer-motion";

import { fadeInUp } from "@/lib/motion";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import { VIZU_MOCK_SKILLS, getSkillIndex, type VizuMockSkillMeta } from "../constants/skills";
import VizuMockTimer from "./timer";

interface Props {
  skill: VizuMockSkillMeta;
  children: ReactNode;
  footer: ReactNode;
  /** Lesen wires this to auto-submit whatever's answered so far the
   * instant the 20-minute countdown hits 0 — the other, still-placeholder
   * steps leave it unset. */
  onTimerExpire?: () => void;
}

/** Shared layout for the four skill steps (Lesen/Hören/Schreiben/
 * Sprechen) — skill-colored header, step progress dots, a live
 * countdown, and a fixed footer for the step's own action button. Keeps
 * the four step pages themselves down to just their placeholder content
 * + footer button, instead of each re-implementing this chrome. */
export default function VizuMockStepShell({ skill, children, footer, onTimerExpire }: Props) {
  const { t } = useTranslation();
  const Icon = skill.icon;
  const currentIndex = getSkillIndex(skill.skill);

  return (
    <motion.div variants={fadeInUp} initial="hidden" animate="show" className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br text-white shadow-md",
              skill.color,
            )}
          >
            <Icon size={20} />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
              {t("vizuMock.step", { current: currentIndex + 1, total: VIZU_MOCK_SKILLS.length })}
            </p>
            <h1 className="text-lg font-bold text-text-primary">{t(skill.labelKey)}</h1>
          </div>
        </div>

        <VizuMockTimer key={skill.skill} minutes={skill.durationMinutes} onExpire={onTimerExpire} />
      </div>

      <div className="flex items-center gap-1.5">
        {VIZU_MOCK_SKILLS.map((s, i) => (
          <div
            key={s.skill}
            className={cn(
              "h-1.5 flex-1 rounded-full transition-colors",
              i < currentIndex ? "bg-success" : i === currentIndex ? `bg-gradient-to-r ${s.color}` : "bg-surface-border",
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
