"use client";

import { useQuery } from "@tanstack/react-query";
import { Library } from "lucide-react";

import { getLessonQuizzes, getQuizOptions, getQuizQuestions } from "@/features/lessons/services/quiz-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import LessonSection from "../common/lesson-section";
import VocabularyTestSection from "./vocabulary-test-section";

interface Props {
  lessonId: string;
}

/** The separate "Wortschatz Quiz" section — distinct from the Wortschatz
 * learning step (vocabulary-learn-section.tsx). Self-detects whether this
 * lesson has a VOCABULARY-type quiz at all (A1 only, by construction of
 * test_sync_service.py's level gate); B1-C1 lessons render a short
 * "not applicable" panel instead of erroring, since this section slug is
 * always present in lessonSections regardless of level. Whether the
 * Wortschatz learning step is done first is enforced by the central
 * SectionGateBoundary wrapping this component (see
 * section-gate-boundary.tsx) — this component only needs to distinguish
 * "not applicable for this level" from "has real quiz content," it
 * doesn't duplicate the lock check itself. The real, unbypassable gate
 * is server-side in grading_service.grade_and_submit(). */
export default function VocabularyQuizSection({ lessonId }: Props) {
  const { t } = useTranslation();

  const { data: vocabQuizzes, isLoading: vocabQuizLoading } = useQuery({
    queryKey: ["lesson-quizzes", lessonId, "VOCABULARY"],
    queryFn: () => getLessonQuizzes(lessonId, "VOCABULARY"),
  });
  const vocabQuiz = vocabQuizzes?.[0];

  const { data: questions, isLoading: questionsLoading } = useQuery({
    queryKey: ["quiz-questions-with-options", vocabQuiz?.id],
    queryFn: async () => {
      if (!vocabQuiz) return [];
      const qs = await getQuizQuestions(vocabQuiz.id);
      return Promise.all(qs.map(async (q) => ({ ...q, options: await getQuizOptions(q.id) })));
    },
    enabled: !!vocabQuiz,
  });

  if (vocabQuizLoading) {
    return (
      <LessonSection title="Wortschatz Quiz" description={t("common.loading")} icon={Library}>
        <p className="text-sm text-text-secondary">{t("common.loading")}</p>
      </LessonSection>
    );
  }

  if (!vocabQuiz) {
    return (
      <LessonSection title="Wortschatz Quiz" description="Nicht verfügbar" icon={Library}>
        <p className="rounded-2xl bg-surface-hover p-6 text-center text-sm text-text-secondary">
          Für dieses Niveau nicht verfügbar.
        </p>
      </LessonSection>
    );
  }

  if (questionsLoading || !questions || questions.length === 0) {
    return (
      <LessonSection title="Wortschatz Quiz" description={t("common.loading")} icon={Library}>
        <p className="text-sm text-text-secondary">{t("common.loading")}</p>
      </LessonSection>
    );
  }

  return <VocabularyTestSection lessonId={lessonId} quizId={vocabQuiz.id} questions={questions} />;
}
