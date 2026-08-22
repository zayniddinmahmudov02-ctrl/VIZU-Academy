"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Lock, Library } from "lucide-react";

import { getLessonQuizzes, getQuizOptions, getQuizQuestions } from "@/features/lessons/services/quiz-service";
import { useSectionGate } from "@/features/lessons/hooks/use-section-gate";
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
 * always present in lessonSections regardless of level. Access is gated
 * on the Wortschatz learning step being done (StudentProgress.
 * vocabulary_completed, surfaced via useSectionGate) — this is UX only;
 * the real, unbypassable gate is server-side in grading_service.
 * grade_and_submit(), which 403s a submit attempt for a VOCABULARY quiz
 * if vocabulary_completed isn't true yet, regardless of how this page was
 * reached. */
export default function VocabularyQuizSection({ lessonId }: Props) {
  const { t } = useTranslation();

  const { data: vocabQuizzes, isLoading: vocabQuizLoading } = useQuery({
    queryKey: ["lesson-quizzes", lessonId, "VOCABULARY"],
    queryFn: () => getLessonQuizzes(lessonId, "VOCABULARY"),
  });
  const vocabQuiz = vocabQuizzes?.[0];

  const { data: gate, isLoading: gateLoading } = useSectionGate(lessonId);

  const { data: questions, isLoading: questionsLoading } = useQuery({
    queryKey: ["quiz-questions-with-options", vocabQuiz?.id],
    queryFn: async () => {
      if (!vocabQuiz) return [];
      const qs = await getQuizQuestions(vocabQuiz.id);
      return Promise.all(qs.map(async (q) => ({ ...q, options: await getQuizOptions(q.id) })));
    },
    enabled: !!vocabQuiz && !!gate?.wortschatz.completed,
  });

  if (vocabQuizLoading || gateLoading) {
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

  if (!gate?.wortschatz.completed) {
    return (
      <LessonSection title="Wortschatz Quiz" description="Gesperrt" icon={Library}>
        <div className="rounded-2xl bg-surface-hover p-8 text-center ring-1 ring-surface-border">
          <Lock className="mx-auto text-text-muted" size={28} />
          <p className="mt-3 text-sm font-medium text-text-primary">
            🔒 Wortschatz Quiz — Schließe zuerst den Wortschatz ab.
          </p>
          <Link
            href={`/lessons/${lessonId}/wortschatz`}
            className="mt-4 inline-flex items-center gap-1.5 rounded-button bg-gradient-to-r from-accent-blue-hover to-accent-blue px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-accent-blue/25 transition hover:-translate-y-0.5"
          >
            Zum Wortschatz
          </Link>
        </div>
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
