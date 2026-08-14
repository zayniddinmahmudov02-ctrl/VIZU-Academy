"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { CircleHelp } from "lucide-react";

import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import {
  getLessonQuizzes,
  getQuizOptions,
  getQuizQuestions,
  submitQuizResult,
  type LessonQuizOption,
  type LessonQuizQuestion,
  type QuizType,
} from "@/features/lessons/services/quiz-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import LessonSection from "../common/lesson-section";

interface Props {
  lessonId: string;
  quizType?: QuizType;
}

interface QuestionWithOptions extends LessonQuizQuestion {
  options: LessonQuizOption[];
}

/** Real quiz player, backed by the legacy Quiz/QuizQuestion/QuizOption
 * models (see app/models/quiz.py) — grammar quiz_type feeds 10 of the
 * lesson's 100 points (see LessonScoringService), lesson quiz_type is
 * shown separately and never added to that total. Scored client-side
 * and persisted via POST /student-quizzes, matching this legacy quiz
 * system's existing architecture (no dedicated server-side grading
 * endpoint exists for it, unlike the newer Assessment Engine). */
export default function QuizSection({ lessonId, quizType = "GRAMMAR" }: Props) {
  const { t } = useTranslation();
  const { user } = useCurrentUser();

  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState<{ correct: number; wrong: number; skipped: number; score: number } | null>(
    null,
  );
  const [submitting, setSubmitting] = useState(false);

  const { data: quizzes, isLoading: quizzesLoading } = useQuery({
    queryKey: ["lesson-quizzes", lessonId, quizType],
    queryFn: () => getLessonQuizzes(lessonId, quizType),
  });
  const quiz = quizzes?.[0];

  const { data: questions, isLoading: questionsLoading } = useQuery({
    queryKey: ["quiz-questions-with-options", quiz?.id],
    queryFn: async (): Promise<QuestionWithOptions[]> => {
      if (!quiz) return [];
      const qs = await getQuizQuestions(quiz.id);
      const withOptions = await Promise.all(
        qs.map(async (q) => ({ ...q, options: await getQuizOptions(q.id) })),
      );
      return withOptions;
    },
    enabled: !!quiz,
  });

  const isLoading = quizzesLoading || questionsLoading;
  const title = quizType === "LESSON" ? "Lesson Quiz" : t("lessons.sectionQuiz");

  function selectAnswer(questionId: string, optionId: string) {
    if (submitted) return;
    setAnswers((prev) => ({ ...prev, [questionId]: optionId }));
  }

  async function handleSubmit() {
    if (!questions || !quiz || !user) return;
    setSubmitting(true);

    let correct = 0;
    let wrong = 0;
    let skipped = 0;

    for (const question of questions) {
      const selectedId = answers[question.id];
      if (!selectedId) {
        skipped += 1;
        continue;
      }
      const selectedOption = question.options.find((o) => o.id === selectedId);
      if (selectedOption?.is_correct) correct += 1;
      else wrong += 1;
    }

    const total = questions.length;
    const score = total > 0 ? Math.round((correct / total) * 100) : 0;

    try {
      await submitQuizResult({
        user_id: user.id,
        quiz_id: quiz.id,
        correct_answers: correct,
        wrong_answers: wrong,
        skipped_answers: skipped,
        score,
        passed: score >= quiz.passing_score,
      });
      setResult({ correct, wrong, skipped, score });
      setSubmitted(true);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <LessonSection title={title} description={t("lessons.quizDescription")} icon={CircleHelp}>
      {isLoading && <p className="text-sm text-text-secondary">{t("common.loading")}</p>}

      {!isLoading && (!quiz || (questions ?? []).length === 0) && (
        <p className="rounded-2xl bg-surface-hover p-6 text-center text-sm text-text-secondary">
          Für diese Lektion sind noch keine Aufgaben verfügbar.
        </p>
      )}

      {!isLoading && quiz && questions && questions.length > 0 && (
        <div className="space-y-5">
          {questions.map((question, index) => (
            <div key={question.id} className="rounded-2xl bg-surface-hover/60 p-6 ring-1 ring-surface-border">
              <h3 className="text-base font-semibold text-text-primary">
                {index + 1}. {question.question}
              </h3>

              <div className="mt-4 space-y-2.5">
                {question.options.map((option) => {
                  const isSelected = answers[question.id] === option.id;
                  const showCorrect = submitted && option.is_correct;
                  const showIncorrect = submitted && isSelected && !option.is_correct;

                  return (
                    <button
                      key={option.id}
                      type="button"
                      onClick={() => selectAnswer(question.id, option.id)}
                      disabled={submitted}
                      className={`w-full rounded-xl px-4 py-3 text-left text-sm font-medium shadow-sm ring-1 transition-colors ${
                        showCorrect
                          ? "bg-success/10 text-success ring-success/40"
                          : showIncorrect
                            ? "bg-danger/10 text-danger ring-danger/40"
                            : isSelected
                              ? "bg-accent-blue/10 text-text-primary ring-accent-blue/40"
                              : "bg-surface-card text-text-primary ring-surface-border hover:bg-accent-blue/5 hover:ring-accent-blue/30 disabled:cursor-not-allowed"
                      }`}
                    >
                      {option.option_text}
                    </button>
                  );
                })}
              </div>

              {submitted && question.explanation && (
                <p className="mt-3 text-sm text-text-muted">{question.explanation}</p>
              )}
            </div>
          ))}

          {!submitted ? (
            <button
              type="button"
              onClick={handleSubmit}
              disabled={submitting || !user}
              className="inline-flex items-center gap-1.5 rounded-button bg-gradient-to-r from-accent-blue-hover to-accent-blue px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-accent-blue/25 transition enabled:hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting ? "Wird ausgewertet..." : t("lessons.quizCheckAnswer")}
            </button>
          ) : (
            result && (
              <div className="rounded-2xl bg-surface-card p-5 ring-1 ring-surface-border">
                <p className="text-lg font-bold text-text-primary">{result.score}%</p>
                <p className="mt-1 text-sm text-text-secondary">
                  {result.correct} richtig · {result.wrong} falsch · {result.skipped} übersprungen
                </p>
              </div>
            )
          )}
        </div>
      )}
    </LessonSection>
  );
}
