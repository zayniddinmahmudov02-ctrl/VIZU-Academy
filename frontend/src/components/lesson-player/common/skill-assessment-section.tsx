"use client";

import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, type LucideIcon } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import Button from "@/components/ui/button";
import {
  getAttemptResult,
  getPublicLessonAssessment,
  startAttempt,
  submitAnswer,
  submitAttempt,
} from "@/features/admin/services/assessment-service";
import type {
  AssessmentResult,
  PublicTask,
  PublicSection,
  SectionSkill,
} from "@/features/admin/types/assessment.types";

import LessonSection from "./lesson-section";
import TaskRenderer from "../reading/task-renderer";

interface Props {
  lessonId: string;
  skill: SectionSkill;
  title: string;
  description: string;
  icon: LucideIcon;
  emptyStateText: string;
}

/** The universal Assessment-engine player for a single skill (Lesen or
 * Hören today; Schreiben/Sprechen can reuse this same shell later).
 * Reuses one engine/component for every skill instead of duplicating
 * per-skill attempt-taking logic — only the skill filter and the copy
 * differ between ReadingSection and ListeningSection. */
export default function SkillAssessmentSection({ lessonId, skill, title, description, icon, emptyStateText }: Props) {
  const queryClient = useQueryClient();

  const { data: assessment, isLoading } = useQuery({
    queryKey: ["public-lesson-assessment", lessonId],
    queryFn: () => getPublicLessonAssessment(lessonId),
  });

  const sections = useMemo(
    () => (assessment?.sections ?? []).filter((s: PublicSection) => s.skill === skill),
    [assessment, skill],
  );
  const hasContent = sections.some((s: PublicSection) => s.tasks.length > 0);

  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (assessment && hasContent && !attemptId && !result) {
      startAttempt(assessment.id).then((attempt) => setAttemptId(attempt.id));
    }
  }, [assessment, hasContent, attemptId, result]);

  function handleAnswerChange(questionId: string, answerData: string) {
    setAnswers((prev) => ({ ...prev, [questionId]: answerData }));
    if (attemptId) {
      submitAnswer(attemptId, { question_id: questionId, answer_data: answerData })
        .then(() => {
          // Answering the last question of a skill (e.g. all of Lesen)
          // is what unlocks the next section in the sequence — see
          // SectionGateService._skill_all_answered. Cheap query, safe to
          // invalidate on every answer rather than only the last one.
          queryClient.invalidateQueries({ queryKey: ["section-gate", lessonId] });
        })
        .catch(() => {});
    }
  }

  async function handleSubmit() {
    if (!attemptId) return;
    setSubmitting(true);
    try {
      await submitAttempt(attemptId);
      const finalResult = await getAttemptResult(attemptId);
      setResult(finalResult);
      queryClient.invalidateQueries({ queryKey: ["public-lesson-assessment", lessonId] });
    } finally {
      setSubmitting(false);
    }
  }

  const allTasks = sections.flatMap((s: PublicSection) => s.tasks);
  const answeredCount = Object.keys(answers).length;
  const totalQuestions = allTasks.reduce((sum: number, task: PublicTask) => sum + task.questions.length, 0);

  return (
    <LessonSection title={title} description={description} icon={icon}>
      {isLoading && <p className="text-sm text-text-muted">Wird geladen...</p>}

      {!isLoading && !hasContent && (
        <div className="rounded-2xl bg-surface-hover/60 p-6 text-center ring-1 ring-surface-border sm:p-8">
          <p className="text-text-secondary">{emptyStateText}</p>
        </div>
      )}

      {!isLoading && hasContent && result && (
        <div className="rounded-2xl bg-surface-hover/60 p-6 text-center ring-1 ring-surface-border sm:p-8">
          <CheckCircle2 size={32} className="mx-auto text-success" />
          <h3 className="mt-3 text-xl font-bold text-text-primary">
            {result.total_score} / {result.max_score} Punkte
          </h3>
          <p className="mt-1 text-text-secondary">{result.percentage}%</p>
        </div>
      )}

      {!isLoading && hasContent && !result && (
        <div className="space-y-6">
          {sections.map((section: PublicSection) => (
            <div key={section.id} className="space-y-5">
              {section.tasks.map((task: PublicTask) => (
                <TaskRenderer key={task.id} task={task} answers={answers} onAnswerChange={handleAnswerChange} />
              ))}
            </div>
          ))}

          <div className="flex items-center justify-between border-t border-surface-border pt-5">
            <span className="text-sm text-text-muted">
              {answeredCount} / {totalQuestions} beantwortet
            </span>
            <Button onClick={handleSubmit} disabled={submitting || !attemptId}>
              {submitting ? "Wird abgegeben..." : "Abgeben"}
            </Button>
          </div>
        </div>
      )}
    </LessonSection>
  );
}
