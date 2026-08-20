"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Library } from "lucide-react";

import { completeLessonVocabulary, getLessonVocabularies } from "@/features/lessons/services/vocabulary-service";
import { getLessonQuizzes, getQuizOptions, getQuizQuestions } from "@/features/lessons/services/quiz-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import LessonSection from "../common/lesson-section";
import { generateExercises, type VocabularyExercise } from "./exercise-generator";
import ExerciseRunner from "./exercise-runner";
import VocabularyTestSection from "./vocabulary-test-section";

interface Props {
  lessonId: string;
}

/** Real Wortschatz panel — published Vocabulary rows for this lesson (see
 * app/models/vocabulary.py). A1 lessons get an auto-generated 20-question
 * 2-option test (backend keeps Quiz/QuizQuestion/QuizOption in sync with
 * vocabulary — see app/services/vocabulary/test_sync_service.py); this
 * component detects that by simply checking whether a published
 * VOCABULARY-type quiz with questions exists for the lesson — true only
 * for A1 by construction, so no level needs to be plumbed in here at
 * all. Every other level falls through to the original sequential
 * client-side exercise generator (see exercise-generator.ts), completely
 * unchanged. Finishing either flow persists the session's score server-
 * side (StudentProgress.vocabulary_score, feeding LessonScoringService's
 * partial-credit Wortschatz component out of 10 points). No vocabulary
 * audio anywhere in this flow — not a feature right now. */
export default function VocabularySection({ lessonId }: Props) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const { data: vocabQuizzes, isLoading: vocabQuizLoading } = useQuery({
    queryKey: ["lesson-quizzes", lessonId, "VOCABULARY"],
    queryFn: () => getLessonQuizzes(lessonId, "VOCABULARY"),
  });
  const vocabQuiz = vocabQuizzes?.[0];

  const { data: vocabQuestions, isLoading: vocabQuestionsLoading } = useQuery({
    queryKey: ["quiz-questions-with-options", vocabQuiz?.id],
    queryFn: async () => {
      if (!vocabQuiz) return [];
      const qs = await getQuizQuestions(vocabQuiz.id);
      return Promise.all(qs.map(async (q) => ({ ...q, options: await getQuizOptions(q.id) })));
    },
    enabled: !!vocabQuiz,
  });

  const { data: words, isLoading } = useQuery({
    queryKey: ["lesson-vocabularies", lessonId],
    queryFn: () => getLessonVocabularies(lessonId),
  });

  const exercises: VocabularyExercise[] = useMemo(() => generateExercises(words ?? []), [words]);

  const [index, setIndex] = useState(0);
  const [correctCount, setCorrectCount] = useState(0);
  const [finished, setFinished] = useState(false);

  const completeMutation = useMutation({
    mutationFn: (percentage: number) => completeLessonVocabulary(lessonId, percentage),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["section-gate", lessonId] });
    },
  });

  function handleExerciseDone(correct: boolean) {
    const nextCorrect = correctCount + (correct ? 1 : 0);
    setCorrectCount(nextCorrect);

    if (index + 1 >= exercises.length) {
      setFinished(true);
      const percentage = Math.round((nextCorrect / exercises.length) * 100);
      completeMutation.mutate(percentage);
    } else {
      setIndex(index + 1);
    }
  }

  const percentage = exercises.length > 0 ? Math.round((correctCount / exercises.length) * 100) : 0;

  // A1's auto-generated test takes over whenever one exists for this
  // lesson — every other level never has a VOCABULARY-type quiz at all
  // (see test_sync_service.py's level gate), so this check alone is a
  // complete, self-contained A1/B1+ router with no level plumbing needed.
  if (!vocabQuizLoading && !vocabQuestionsLoading && vocabQuestions && vocabQuestions.length > 0) {
    return <VocabularyTestSection lessonId={lessonId} questions={vocabQuestions} />;
  }

  return (
    <LessonSection title={t("lessons.sectionVocabulary")} description={t("lessons.vocabularyDescription")} icon={Library}>
      {isLoading && <p className="text-sm text-text-secondary">{t("common.loading")}</p>}

      {!isLoading && exercises.length === 0 && (
        <p className="rounded-2xl bg-surface-hover p-6 text-center text-sm text-text-secondary">
          Für diese Lektion sind noch keine Inhalte verfügbar.
        </p>
      )}

      {!isLoading && exercises.length > 0 && !finished && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs font-medium text-text-muted">
            <span>
              Übung {index + 1} / {exercises.length}
            </span>
            <span>
              {correctCount} richtig bisher
            </span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-hover">
            <div
              className="h-full rounded-full bg-accent-blue transition-all duration-300"
              style={{ width: `${(index / exercises.length) * 100}%` }}
            />
          </div>

          <ExerciseRunner key={index} exercise={exercises[index]} onDone={handleExerciseDone} />
        </div>
      )}

      {finished && (
        <div className="rounded-2xl bg-surface-card p-6 text-center ring-1 ring-surface-border">
          <p className="text-3xl font-bold text-text-primary">{percentage}%</p>
          <p className="mt-1 text-sm text-text-secondary">
            {correctCount} von {exercises.length} Übungen richtig
          </p>
          <p className="mt-3 text-sm font-medium text-success">Wortschatz abgeschlossen ✓</p>
        </div>
      )}
    </LessonSection>
  );
}
