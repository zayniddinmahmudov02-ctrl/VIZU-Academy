"use client";

import { useQuery } from "@tanstack/react-query";
import { BookMarked, BookOpen, ClipboardCheck, Headphones, Languages, MessageCircleQuestion, Mic, PenLine, type LucideIcon } from "lucide-react";

import {
  getLessonSkillResults,
  type SkillKey,
  type SkillResult,
  type SkillStatus,
} from "@/features/lessons/services/lesson-skills-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

// lesson order (lesson flow v3)
export const SKILLS: { key: SkillKey; label: string; icon: LucideIcon }[] = [
  { key: "frage", label: "lessons.sectionFrage", icon: MessageCircleQuestion },
  { key: "grammatik", label: "lessons.sectionGrammar", icon: BookMarked },
  { key: "lesen", label: "lessons.sectionReading", icon: BookOpen },
  { key: "hoeren", label: "lessons.sectionListening", icon: Headphones },
  { key: "schreiben", label: "lessons.sectionWriting", icon: PenLine },
  { key: "sprechen", label: "lessons.sectionSpeaking", icon: Mic },
  { key: "wortschatz", label: "lessons.sectionVocabulary", icon: Languages },
  { key: "yakuniy", label: "lessons.sectionLessonQuiz", icon: ClipboardCheck },
];

export const STATUS: Record<SkillStatus | "frage_sent", { label: string; tone: string }> = {
  frage_sent: { label: "lessons.frageSent", tone: "bg-success/10 text-success" },
  not_available: { label: "lessons.skillNotAvailable", tone: "bg-surface-hover text-text-muted" },
  not_started: { label: "lessons.skillNotStarted", tone: "bg-surface-hover text-text-secondary" },
  in_progress: { label: "lessons.skillInProgress", tone: "bg-accent-blue/10 text-accent-blue" },
  pending_evaluation: { label: "lessons.skillPending", tone: "bg-warning/10 text-warning" },
  evaluation_failed: { label: "lessons.skillFailed", tone: "bg-danger/10 text-danger" },
  completed: { label: "lessons.skillCompleted", tone: "bg-success/10 text-success" },
};

function formatDate(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? null : d.toLocaleDateString(undefined, { day: "2-digit", month: "2-digit", year: "numeric" });
}

function attemptsOf(skill: SkillResult): number {
  if (skill.attempts != null) return skill.attempts;
  return (skill.tasks ?? []).reduce((sum, task) => sum + (task.attempts ?? 0), 0);
}

/** Lesen / Hören / Schreiben / Sprechen results of one lesson. Every value
 * comes from GET /lesson-skills/{id}/results; the overall score is final
 * only once every available skill is graded, otherwise it is shown as an
 * interim average of the graded ones (a missing skill is never a 0). */
export default function SkillResultsPanel({ lessonId }: { lessonId: string }) {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ["lesson-skill-results", lessonId],
    queryFn: () => getLessonSkillResults(lessonId),
  });

  if (isLoading || !data) return null;
  const { overall, skills } = data;
  if (overall.status === "not_available") return null;

  return (
    <div className="space-y-4 rounded-2xl bg-surface-card p-4 ring-1 ring-surface-border sm:p-6" data-testid="skill-results">
      <h3 className="text-base font-bold text-text-primary">{t("lessons.skillResultsTitle")}</h3>

      <div
        className={cn(
          "rounded-xl px-4 py-3",
          overall.status === "final" ? "bg-gradient-to-br from-brand-900 to-brand-700 text-white" : "bg-surface-hover/70 text-text-primary",
        )}
        data-testid="skill-overall"
      >
        {overall.score === null ? (
          <p className="text-sm text-text-secondary">{t("lessons.overallNone")}</p>
        ) : (
          <>
            <p className={cn("text-xs font-bold uppercase tracking-wide", overall.status === "final" ? "text-white/75" : "text-text-muted")}>
              {overall.status === "final"
                ? t("lessons.overallFinal")
                : t("lessons.overallInterim", { n: overall.graded_skills, m: overall.required_skills })}
            </p>
            <p className="mt-0.5 text-3xl font-extrabold tabular-nums">{overall.score} / 100</p>
            {overall.method && overall.status === "final" && (
              <p className={cn("mt-0.5 text-xs", overall.status === "final" ? "text-white/75" : "text-text-muted")}>{overall.method}</p>
            )}
          </>
        )}
      </div>

      <ul className="grid gap-3 sm:grid-cols-2">
        {SKILLS.map(({ key, label, icon: Icon }) => {
          const skill = skills[key];
          // a step the lesson has no content for is not listed
          if (!skill || !skill.available) return null;
          // Frage des Themas: no fixed rubric — "sent" instead of "waiting for a score"
          const frageSent = key === "frage" && skill.submitted && skill.status !== "completed";
          const status = frageSent ? STATUS.frage_sent : (STATUS[skill.status] ?? STATUS.not_started);
          const attempts = attemptsOf(skill);
          const date = formatDate(skill.evaluated_at ?? skill.submitted_at);
          return (
            <li key={key} className="rounded-xl bg-surface-hover/50 p-3.5 ring-1 ring-surface-border" data-testid={`skill-${key}`}>
              <div className="flex items-center justify-between gap-2">
                <span className="flex items-center gap-2 text-sm font-semibold text-text-primary">
                  <Icon size={16} className="text-accent-blue" />
                  {t(label)}
                </span>
                <span className="text-lg font-extrabold tabular-nums text-text-primary">
                  {skill.score !== null ? `${skill.score}` : "—"}
                  {skill.score !== null && <span className="text-xs font-semibold text-text-muted"> / 100</span>}
                </span>
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
                <span className={cn("rounded-full px-2 py-0.5 font-semibold", status.tone)}>{t(status.label)}</span>
                {attempts > 0 && <span className="text-text-muted">{t("lessons.testAttempts", { n: attempts })}</span>}
                {date && <span className="text-text-muted">{date}</span>}
                {skill.can_retry && <span className="font-semibold text-accent-blue">{t("lessons.skillCanRetry")}</span>}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
