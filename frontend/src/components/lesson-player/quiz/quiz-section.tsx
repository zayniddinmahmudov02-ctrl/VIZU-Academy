"use client";

import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CircleHelp } from "lucide-react";

import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import {
  getLessonQuizzes,
  getQuizOptions,
  getQuizQuestions,
  submitQuizAttempt,
  type LessonQuizOption,
  type LessonQuizQuestion,
  type QuizAnswerResult,
  type QuizAnswerSubmit,
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

function shuffle<T>(items: T[]): T[] {
  const arr = [...items];
  for (let i = arr.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

const OPTION_BASED_TYPES = new Set(["MULTIPLE_CHOICE", "TRUE_FALSE", "ERROR_FINDING"]);

/** Real quiz player, backed by the legacy Quiz/QuizQuestion/QuizOption
 * models (see app/models/quiz.py) — grammar quiz_type feeds 10 of the
 * lesson's 100 points (see LessonScoringService), lesson quiz_type is
 * shown separately and never added to that total. Grading is server-
 * side (POST /quizzes/{quizId}/submit, see
 * app/services/quiz/grading_service.py) — the fetched questions/options
 * never carry is_correct/correct_text_answer/match_value, so this
 * component only ever learns what was correct from the submit
 * response, after the student has committed their answers.
 *
 * Extended beyond plain multiple-choice per question_type: TRUE_FALSE/
 * ERROR_FINDING reuse the same options mechanism as MC; CLOZE_TEXT/
 * SENTENCE_COMPLETION are free-text; SENTENCE_ORDERING is a click-built
 * order; MATCHING pairs option_text with a chosen value — all four are
 * graded the same way server-side and revealed via the submit response's
 * per-question `results`. */
export default function QuizSection({ lessonId, quizType = "GRAMMAR" }: Props) {
  const { t } = useTranslation();
  const { user } = useCurrentUser();
  const queryClient = useQueryClient();

  const [selectedOptions, setSelectedOptions] = useState<Record<string, string>>({});
  const [textAnswers, setTextAnswers] = useState<Record<string, string>>({});
  const [orderAnswers, setOrderAnswers] = useState<Record<string, string[]>>({});
  const [matchAnswers, setMatchAnswers] = useState<Record<string, Record<string, string>>>({});
  const [matchPending, setMatchPending] = useState<Record<string, string | null>>({});

  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState<{ correct: number; wrong: number; skipped: number; score: number } | null>(
    null,
  );
  const [resultsByQuestion, setResultsByQuestion] = useState<Record<string, QuizAnswerResult>>({});
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

  // Stable per-question shuffles — recomputed only when the question set
  // changes, not on every render (which would reshuffle mid-answer).
  const shuffledOptions = useMemo(() => {
    const map: Record<string, LessonQuizOption[]> = {};
    for (const q of questions ?? []) {
      map[q.id] = q.question_type === "SENTENCE_ORDERING" ? shuffle(q.options) : q.options;
    }
    return map;
  }, [questions]);

  // Already server-shuffled per fetch (see QuizQuestionPublicResponse.
  // match_value_pool) — no client-side shuffling needed or possible,
  // since individual options no longer carry their own match_value.
  const matchValuePools = useMemo(() => {
    const map: Record<string, string[]> = {};
    for (const q of questions ?? []) {
      if (q.question_type === "MATCHING") {
        map[q.id] = q.match_value_pool ?? [];
      }
    }
    return map;
  }, [questions]);

  const isLoading = quizzesLoading || questionsLoading;
  const title = quizType === "LESSON" ? "Lesson Quiz" : t("lessons.sectionQuiz");

  function selectOption(questionId: string, optionId: string) {
    if (submitted) return;
    setSelectedOptions((prev) => ({ ...prev, [questionId]: optionId }));
  }

  function toggleOrderPick(questionId: string, optionId: string) {
    if (submitted) return;
    setOrderAnswers((prev) => {
      const current = prev[questionId] ?? [];
      const next = current.includes(optionId)
        ? current.filter((id) => id !== optionId)
        : [...current, optionId];
      return { ...prev, [questionId]: next };
    });
  }

  function pickMatchValue(questionId: string, value: string) {
    if (submitted) return;
    const pendingOptionId = matchPending[questionId];
    if (!pendingOptionId) return;
    setMatchAnswers((prev) => ({
      ...prev,
      [questionId]: { ...(prev[questionId] ?? {}), [pendingOptionId]: value },
    }));
    setMatchPending((prev) => ({ ...prev, [questionId]: null }));
  }

  function pickMatchOption(questionId: string, optionId: string) {
    if (submitted) return;
    setMatchPending((prev) => ({ ...prev, [questionId]: optionId }));
  }

  function isQuestionAnswered(question: QuestionWithOptions): boolean {
    if (question.question_type === "CLOZE_TEXT" || question.question_type === "SENTENCE_COMPLETION") {
      return !!textAnswers[question.id]?.trim();
    }
    if (question.question_type === "SENTENCE_ORDERING") {
      return (orderAnswers[question.id]?.length ?? 0) === question.options.length && question.options.length > 0;
    }
    if (question.question_type === "MATCHING") {
      const answered = matchAnswers[question.id] ?? {};
      return question.options.length > 0 && Object.keys(answered).length === question.options.length;
    }
    return !!selectedOptions[question.id];
  }

  function buildAnswer(question: QuestionWithOptions): QuizAnswerSubmit | null {
    switch (question.question_type) {
      case "CLOZE_TEXT":
      case "SENTENCE_COMPLETION":
        return { question_id: question.id, text_answer: textAnswers[question.id] };
      case "SENTENCE_ORDERING":
        return { question_id: question.id, ordered_option_ids: orderAnswers[question.id] };
      case "MATCHING":
        return { question_id: question.id, matches: matchAnswers[question.id] };
      default:
        return { question_id: question.id, option_id: selectedOptions[question.id] };
    }
  }

  async function handleSubmit() {
    if (!questions || !quiz || !user) return;
    setSubmitting(true);

    const answers = questions
      .filter((q) => isQuestionAnswered(q))
      .map((q) => buildAnswer(q))
      .filter((a): a is QuizAnswerSubmit => a !== null);

    try {
      const response = await submitQuizAttempt(quiz.id, answers);
      setResultsByQuestion(Object.fromEntries(response.results.map((r) => [r.question_id, r])));
      setResult({
        correct: response.correct_answers,
        wrong: response.wrong_answers,
        skipped: response.skipped_answers,
        score: response.score,
      });
      setSubmitted(true);
      queryClient.invalidateQueries({ queryKey: ["section-gate", lessonId] });
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

              {OPTION_BASED_TYPES.has(question.question_type) && (
                <div className="mt-4 space-y-2.5">
                  {question.options.map((option) => {
                    const isSelected = selectedOptions[question.id] === option.id;
                    const correctOptionId = resultsByQuestion[question.id]?.correct_option_id;
                    const showCorrect = submitted && correctOptionId === option.id;
                    const showIncorrect = submitted && isSelected && correctOptionId !== option.id;

                    return (
                      <button
                        key={option.id}
                        type="button"
                        onClick={() => selectOption(question.id, option.id)}
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
              )}

              {(question.question_type === "CLOZE_TEXT" || question.question_type === "SENTENCE_COMPLETION") && (
                <div className="mt-4 space-y-2">
                  <input
                    type="text"
                    value={textAnswers[question.id] ?? ""}
                    onChange={(e) =>
                      setTextAnswers((prev) => ({ ...prev, [question.id]: e.target.value }))
                    }
                    disabled={submitted}
                    placeholder="Antwort eingeben..."
                    className="w-full rounded-xl bg-surface-card px-4 py-3 text-sm text-text-primary shadow-sm ring-1 ring-surface-border outline-none focus:ring-accent-blue/40 disabled:cursor-not-allowed"
                  />
                  {submitted && (
                    <p
                      className={`text-sm ${resultsByQuestion[question.id]?.is_correct ? "text-success" : "text-danger"}`}
                    >
                      Richtige Antwort:{" "}
                      <span className="font-semibold">{resultsByQuestion[question.id]?.correct_text_answer}</span>
                    </p>
                  )}
                </div>
              )}

              {question.question_type === "SENTENCE_ORDERING" && (
                <div className="mt-4 space-y-3">
                  <div className="flex flex-wrap gap-2 rounded-xl bg-surface-card p-3 ring-1 ring-surface-border">
                    {(orderAnswers[question.id] ?? []).length === 0 && (
                      <span className="text-xs text-text-muted">Klicke die Wörter unten in der richtigen Reihenfolge an</span>
                    )}
                    {(orderAnswers[question.id] ?? []).map((optionId, i) => {
                      const option = question.options.find((o) => o.id === optionId);
                      return (
                        <span
                          key={optionId}
                          className="rounded-lg bg-accent-blue/10 px-3 py-1.5 text-sm font-medium text-accent-blue"
                        >
                          {i + 1}. {option?.option_text}
                        </span>
                      );
                    })}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {shuffledOptions[question.id]?.map((option) => {
                      const picked = (orderAnswers[question.id] ?? []).includes(option.id);
                      return (
                        <button
                          key={option.id}
                          type="button"
                          onClick={() => toggleOrderPick(question.id, option.id)}
                          disabled={submitted || picked}
                          className={`rounded-xl px-3.5 py-2 text-sm font-medium shadow-sm ring-1 transition-colors ${
                            picked
                              ? "cursor-not-allowed bg-surface-hover text-text-muted ring-surface-border"
                              : "bg-surface-card text-text-primary ring-surface-border hover:bg-accent-blue/5 hover:ring-accent-blue/30"
                          }`}
                        >
                          {option.option_text}
                        </button>
                      );
                    })}
                  </div>
                  {submitted && (
                    <p
                      className={`text-sm ${resultsByQuestion[question.id]?.is_correct ? "text-success" : "text-danger"}`}
                    >
                      Richtige Reihenfolge:{" "}
                      <span className="font-semibold">
                        {[...question.options]
                          .sort((a, b) => a.order_index - b.order_index)
                          .map((o) => o.option_text)
                          .join(" → ")}
                      </span>
                    </p>
                  )}
                </div>
              )}

              {question.question_type === "MATCHING" && (
                <div className="mt-4 grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    {question.options.map((option) => {
                      const isPending = matchPending[question.id] === option.id;
                      const pairedValue = matchAnswers[question.id]?.[option.id];
                      const correctValue = resultsByQuestion[question.id]?.correct_matches?.[option.id];
                      const isCorrectPair = submitted && !!pairedValue && pairedValue === correctValue;
                      const isWrongPair = submitted && !!pairedValue && !isCorrectPair;
                      return (
                        <button
                          key={option.id}
                          type="button"
                          onClick={() => pickMatchOption(question.id, option.id)}
                          disabled={submitted}
                          className={`flex w-full items-center justify-between rounded-xl px-3.5 py-2.5 text-left text-sm font-medium shadow-sm ring-1 transition-colors ${
                            isCorrectPair
                              ? "bg-success/10 text-success ring-success/40"
                              : isWrongPair
                                ? "bg-danger/10 text-danger ring-danger/40"
                                : isPending
                                  ? "bg-accent-blue/10 text-text-primary ring-accent-blue/40"
                                  : "bg-surface-card text-text-primary ring-surface-border hover:ring-accent-blue/30"
                          }`}
                        >
                          <span>{option.option_text}</span>
                          {pairedValue && <span className="text-xs text-text-muted">→ {pairedValue}</span>}
                        </button>
                      );
                    })}
                  </div>
                  <div className="space-y-2">
                    {matchValuePools[question.id]?.map((value) => {
                      const usedBy = Object.entries(matchAnswers[question.id] ?? {}).find(
                        ([, v]) => v === value,
                      );
                      return (
                        <button
                          key={value}
                          type="button"
                          onClick={() => pickMatchValue(question.id, value)}
                          disabled={submitted || !!usedBy}
                          className={`w-full rounded-xl px-3.5 py-2.5 text-left text-sm font-medium shadow-sm ring-1 transition-colors ${
                            usedBy
                              ? "cursor-not-allowed bg-surface-hover text-text-muted ring-surface-border"
                              : "bg-surface-card text-text-primary ring-surface-border hover:bg-accent-blue/5 hover:ring-accent-blue/30"
                          }`}
                        >
                          {value}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

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
