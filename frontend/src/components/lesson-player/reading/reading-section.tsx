"use client";

import { useEffect, useMemo, useState } from "react";
import { BookOpen, CheckCircle2 } from "lucide-react";
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
} from "@/features/admin/types/assessment.types";
import { useTranslation } from "@/lib/i18n/use-translation";

import LessonSection from "../common/lesson-section";
import TaskRenderer from "./task-renderer";

interface Props {
  lessonId: string;
}

/** The real Lesen player, backed by the universal Assessment engine
 * (Assessment[type=COURSE] -> Section -> Task -> Question -> Option).
 * Previously this component showed a single hardcoded demo passage
 * ("Hallo! Ich heiße Anna...") to every user on every lesson — that fake
 * content is gone; this now shows genuinely published tasks, or the
 * empty state, and nothing else. */
export default function ReadingSection({ lessonId }: Props) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const { data: assessment, isLoading } = useQuery({
    queryKey: ["public-lesen-assessment", lessonId],
    queryFn: () => getPublicLessonAssessment(lessonId),
  });

  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (assessment && !attemptId && !result) {
      startAttempt(assessment.id).then((attempt) => setAttemptId(attempt.id));
    }
  }, [assessment, attemptId, result]);

  const allTasks = useMemo(
    () => (assessment?.sections ?? []).flatMap((s: PublicSection) => s.tasks),
    [assessment],
  );

  function handleAnswerChange(questionId: string, answerData: string) {
    setAnswers((prev) => ({ ...prev, [questionId]: answerData }));
    if (attemptId) {
      submitAnswer(attemptId, { question_id: questionId, answer_data: answerData }).catch(() => {});
    }
  }

  async function handleSubmit() {
    if (!attemptId) return;
    setSubmitting(true);
    try {
      await submitAttempt(attemptId);
      const finalResult = await getAttemptResult(attemptId);
      setResult(finalResult);
      queryClient.invalidateQueries({ queryKey: ["public-lesen-assessment", lessonId] });
    } finally {
      setSubmitting(false);
    }
  }

  const answeredCount = Object.keys(answers).length;
  const totalQuestions = allTasks.reduce((sum: number, task: PublicTask) => sum + task.questions.length, 0);

  return (
    <LessonSection title={t("lessons.sectionReading")} description={t("lessons.readingDescription")} icon={BookOpen}>
      {isLoading && <p className="text-sm text-text-muted">{t("common.loading")}</p>}

      {!isLoading && !assessment && (
        <div className="rounded-2xl bg-surface-hover/60 p-6 text-center ring-1 ring-surface-border sm:p-8">
          <p className="text-text-secondary">Für diese Lektion sind noch keine Aufgaben verfügbar.</p>
        </div>
      )}

      {!isLoading && assessment && result && (
        <div className="rounded-2xl bg-surface-hover/60 p-6 text-center ring-1 ring-surface-border sm:p-8">
          <CheckCircle2 size={32} className="mx-auto text-success" />
          <h3 className="mt-3 text-xl font-bold text-text-primary">
            {result.total_score} / {result.max_score} Punkte
          </h3>
          <p className="mt-1 text-text-secondary">{result.percentage}%</p>
        </div>
      )}

      {!isLoading && assessment && !result && (
        <div className="space-y-6">
          {assessment.sections.map((section: PublicSection) => (
            <div key={section.id} className="space-y-5">
              {section.tasks.map((task: PublicTask) => (
                <TaskRenderer
                  key={task.id}
                  task={task}
                  answers={answers}
                  onAnswerChange={handleAnswerChange}
                />
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
