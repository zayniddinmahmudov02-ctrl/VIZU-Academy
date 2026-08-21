"use client";

import { useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, Library } from "lucide-react";

import { completeLessonVocabulary } from "@/features/lessons/services/vocabulary-service";
import {
  submitQuizAttempt,
  type LessonQuizOption,
  type LessonQuizQuestion,
} from "@/features/lessons/services/quiz-service";
import LessonSection from "../common/lesson-section";

interface QuestionWithOptions extends LessonQuizQuestion {
  options: LessonQuizOption[];
}

interface Props {
  lessonId: string;
  quizId: string;
  questions: QuestionWithOptions[];
}

function feedbackFor(percentage: number): string {
  if (percentage >= 90) return "Sehr gut!";
  if (percentage >= 75) return "Gut gemacht!";
  if (percentage >= 60) return "Weiter üben!";
  return "Wiederholen und erneut versuchen.";
}

const OPTION_LETTERS = ["A", "B"];

/** The A1-only, auto-generated 20-question (or fewer, if the lesson has
 * fewer words) 2-option Wortschatz test — content comes from
 * Quiz/QuizQuestion/QuizOption rows the backend keeps in sync with this
 * lesson's Vocabulary (see app/services/vocabulary/test_sync_service.py).
 * Grading is server-side (POST /quizzes/{quizId}/submit, see
 * app/services/quiz/grading_service.py) — fetched options never carry
 * is_correct, so this component only learns the score from that
 * response. That score is then sent straight to the same
 * completeLessonVocabulary() call the B1+ exercise generator already
 * uses, feeding StudentProgress.vocabulary_score and, through it, the
 * existing 100-point LessonScoringService — nothing new on that side. */
export default function VocabularyTestSection({ lessonId, quizId, questions }: Props) {
  const queryClient = useQueryClient();
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [finished, setFinished] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitResult, setSubmitResult] = useState<{ score: number; correct: number; total: number } | null>(null);

  const sorted = useMemo(
    () => [...questions].sort((a, b) => a.order_index - b.order_index),
    [questions],
  );
  const total = sorted.length;
  const current = sorted[index];
  const currentAnswer = current ? answers[current.id] : undefined;
  const isLast = index === total - 1;

  const completeMutation = useMutation({
    mutationFn: (percentage: number) => completeLessonVocabulary(lessonId, percentage),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["section-gate", lessonId] });
    },
  });

  function selectAnswer(optionId: string) {
    if (!current) return;
    setAnswers((prev) => ({ ...prev, [current.id]: optionId }));
  }

  function goBack() {
    setIndex((i) => Math.max(0, i - 1));
  }

  async function goNext() {
    if (!isLast) {
      setIndex((i) => Math.min(total - 1, i + 1));
      return;
    }

    setSubmitting(true);
    try {
      const response = await submitQuizAttempt(
        quizId,
        sorted.map((q) => ({ question_id: q.id, option_id: answers[q.id] })),
      );
      setSubmitResult({ score: response.score, correct: response.correct_answers, total });
      setFinished(true);
      await completeMutation.mutateAsync(response.score);
    } finally {
      setSubmitting(false);
    }
  }

  const percentage = submitResult?.score ?? 0;
  const correctCount = submitResult?.correct ?? 0;
  const points = Math.round((percentage / 100) * 10 * 10) / 10;

  return (
    <LessonSection
      title="Wortschatz Test"
      description={finished ? "Ergebnis" : `Frage ${index + 1} von ${total}`}
      icon={Library}
    >
      {!finished && current && (
        <div className="space-y-5">
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-hover">
            <div
              className="h-full rounded-full bg-accent-blue transition-all duration-300"
              style={{ width: `${(index / total) * 100}%` }}
            />
          </div>

          <div className="rounded-2xl bg-surface-hover/60 p-8 text-center ring-1 ring-surface-border">
            <p className="text-3xl font-bold text-text-primary">{current.question}</p>
            <p className="mt-3 text-sm text-text-secondary">Wähle die richtige Übersetzung.</p>
          </div>

          <div className="space-y-2.5">
            {current.options.map((option, i) => {
              const isSelected = currentAnswer === option.id;
              return (
                <button
                  key={option.id}
                  type="button"
                  onClick={() => selectAnswer(option.id)}
                  className={`flex w-full items-center gap-3 rounded-xl px-4 py-3.5 text-left text-sm font-medium shadow-sm ring-1 transition-colors ${
                    isSelected
                      ? "bg-accent-blue/10 text-text-primary ring-accent-blue/50"
                      : "bg-surface-card text-text-primary ring-surface-border hover:bg-accent-blue/5 hover:ring-accent-blue/30"
                  }`}
                >
                  <span
                    className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                      isSelected ? "bg-accent-blue text-white" : "bg-surface-hover text-text-muted"
                    }`}
                  >
                    {OPTION_LETTERS[i]}
                  </span>
                  {option.option_text}
                </button>
              );
            })}
          </div>

          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={goBack}
              disabled={index === 0}
              className="inline-flex items-center gap-1.5 rounded-button px-4 py-2.5 text-sm font-semibold text-text-secondary ring-1 ring-surface-border transition enabled:hover:bg-surface-hover disabled:cursor-not-allowed disabled:opacity-40"
            >
              <ArrowLeft size={14} />
              Zurück
            </button>
            <button
              type="button"
              onClick={goNext}
              disabled={!currentAnswer || submitting}
              className="inline-flex items-center gap-1.5 rounded-button bg-gradient-to-r from-accent-blue-hover to-accent-blue px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-accent-blue/25 transition enabled:hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isLast ? (submitting ? "Wird ausgewertet..." : "Test abschließen") : "Weiter"}
              {!isLast && <ArrowRight size={14} />}
            </button>
          </div>
        </div>
      )}

      {finished && (
        <div className="rounded-2xl bg-surface-card p-6 text-center ring-1 ring-surface-border">
          <p className="text-3xl font-bold text-text-primary">{percentage}%</p>
          <p className="mt-1 text-sm text-text-secondary">
            {correctCount} / {total} richtig
          </p>
          <p className="mt-1 text-sm text-text-secondary">{points} / 10 Punkte</p>
          <p className="mt-3 text-sm font-medium text-accent-blue">{feedbackFor(percentage)}</p>
          <p className="mt-3 text-sm font-medium text-success">Wortschatz abgeschlossen</p>
        </div>
      )}
    </LessonSection>
  );
}
