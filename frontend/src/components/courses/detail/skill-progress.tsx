"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { SKILLS, STATUS } from "@/components/lesson-player/results/skill-results-panel";
import type { LevelCode } from "@/constants/levels";
import { getLevelProgress, type LevelProgressLesson } from "@/features/lessons/services/lesson-skills-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

function started(l: LevelProgressLesson) {
  return Object.values(l.skills).some((s) => s.status !== "not_started" && s.status !== "not_available");
}

/** The student's own Lesen / Hören / Schreiben / Sprechen status per lesson
 * of one level — done, waiting for evaluation and not started are kept
 * apart. Only lessons the student has begun are listed. */
export default function SkillProgress({ level }: { level: LevelCode }) {
  const { t } = useTranslation();
  const { data } = useQuery({ queryKey: ["level-skill-progress", level], queryFn: () => getLevelProgress(level) });

  const lessons = (data?.lessons ?? []).filter(started);
  if (!lessons.length) return null;
  const all = (data?.lessons ?? []).flatMap((l) => Object.values(l.skills));
  const count = (status: string) => all.filter((s) => s.status === status).length;

  return (
    <section className="rounded-card bg-surface-card p-5 shadow-[var(--shadow-md)] ring-1 ring-surface-border sm:p-6" data-testid="level-skill-progress">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h2 className="text-lg font-bold text-text-primary">{t("lessons.skillResultsTitle")}</h2>
        <div className="flex flex-wrap gap-2 text-xs font-semibold">
          <span className={cn("rounded-full px-2.5 py-1", STATUS.completed.tone)}>
            {t(STATUS.completed.label)}: {count("completed")}
          </span>
          <span className={cn("rounded-full px-2.5 py-1", STATUS.pending_evaluation.tone)}>
            {t(STATUS.pending_evaluation.label)}: {count("pending_evaluation")}
          </span>
          {count("evaluation_failed") > 0 && (
            <span className={cn("rounded-full px-2.5 py-1", STATUS.evaluation_failed.tone)}>
              {t(STATUS.evaluation_failed.label)}: {count("evaluation_failed")}
            </span>
          )}
        </div>
      </div>

      <div className="mt-4 space-y-2.5">
        {lessons.map((l) => (
          <Link
            key={l.lesson_id}
            href={`/lessons/${l.lesson_id}`}
            className="block rounded-2xl bg-surface-hover/50 p-3.5 ring-1 ring-surface-border transition hover:ring-accent-blue/40"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-semibold text-text-primary">
                Modul {l.module_number} · {t("dashboard.lessonNumber", { number: l.lesson_number })}
              </p>
              {l.overall.score !== null && (
                <span className={cn("text-sm font-bold tabular-nums", l.overall.status === "final" ? "text-success" : "text-text-secondary")}>
                  {l.overall.score}/100
                  {l.overall.status !== "final" && <span className="ml-1 text-xs font-medium"> ({l.overall.graded_skills}/{l.overall.required_skills})</span>}
                </span>
              )}
            </div>
            <div className="mt-2 grid grid-cols-2 gap-1.5 sm:grid-cols-4 lg:grid-cols-8">
              {SKILLS.map(({ key, label, icon: Icon }) => {
                const s = l.skills[key];
                if (!s || s.status === "not_available") return null;
                const tone = STATUS[s.status] ?? STATUS.not_started;
                return (
                  <span key={key} className={cn("flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs", tone.tone)}>
                    <Icon size={13} className="shrink-0" />
                    <span className="truncate">{t(label)}</span>
                    <span className="ml-auto font-semibold tabular-nums">{s.score !== null && s.status === "completed" ? s.score : t(tone.label)}</span>
                  </span>
                );
              })}
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
