"use client";

import { useMemo } from "react";
import { CheckCircle2 } from "lucide-react";

import { useCrudList } from "@/features/admin/hooks/use-crud";
import { quizQuestionsApi, quizzesApi } from "@/features/admin/services/quiz-service";
import { vocabularyApi } from "@/features/admin/services/vocabulary-service";

import QuizQuestionsEditor from "./quiz-questions-editor";

/** Read-only status + per-question editing for the auto-generated
 * Wortschatz Quiz (see app/services/vocabulary/test_sync_service.py) —
 * deliberately separate from VocabularyManager (vocabulary CRUD only, no
 * quiz table mixed in) and deliberately NOT a raw QuizManager reuse: the
 * admin never manually creates/deletes this quiz or adds/removes
 * questions by hand — one published Vocabulary word always becomes
 * exactly one question, kept in sync by the backend on every vocabulary
 * mutation. Only the correct-answer/distractor text is admin-editable
 * (via QuizQuestionsEditor with manual-add/AI-generate hidden). Renders
 * an empty state for B1-C1 lessons (no VOCABULARY quiz ever exists for
 * them) or A1 lessons with no published vocabulary yet. */
export default function VocabularyQuizManager({ lessonId }: { lessonId: string }) {
  const { data: allQuizzes, isLoading: quizzesLoading } = useCrudList("quizzes", quizzesApi);
  const { data: allQuizQuestions } = useCrudList("quiz-questions", quizQuestionsApi);
  const { data: allVocabulary } = useCrudList("vocabularies", vocabularyApi);

  const quiz = useMemo(
    () => allQuizzes?.find((q) => q.lesson_id === lessonId && q.quiz_type === "VOCABULARY"),
    [allQuizzes, lessonId],
  );

  const questions = useMemo(
    () => (quiz ? (allQuizQuestions ?? []).filter((q) => q.quiz_id === quiz.id) : []),
    [allQuizQuestions, quiz],
  );
  const publishedCount = questions.filter((q) => q.is_published).length;
  // Published vocabulary count — shown next to the question count so it's
  // visible at a glance that they always match 1:1 (no cap), e.g.
  // "52 Wörter · 52 Fragen".
  const publishedWordCount = useMemo(
    () => (allVocabulary ?? []).filter((v) => v.lesson_id === lessonId && v.is_published).length,
    [allVocabulary, lessonId],
  );

  if (quizzesLoading) {
    return <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>;
  }

  if (!quiz) {
    return (
      <p className="rounded-xl bg-white/[0.02] p-6 text-center text-sm text-[var(--admin-text-muted)] ring-1 ring-[var(--admin-border)]">
        Quiz wird automatisch erstellt, sobald Wörter im Wortschatz veröffentlicht werden.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2.5">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-[var(--admin-accent)]/15 px-2.5 py-1 text-xs font-semibold text-[var(--admin-accent)]">
          <CheckCircle2 size={13} />
          Wortschatz Quiz
        </span>
        <span className="text-xs text-[var(--admin-text-muted)]">
          {publishedWordCount} Wörter · {questions.length} Fragen — {publishedCount} veröffentlicht —{" "}
          {questions.length - publishedCount} Entwurf
        </span>
      </div>

      <QuizQuestionsEditor quizId={quiz.id} lessonId={lessonId} allowManualAdd={false} allowAiGenerate={false} />
    </div>
  );
}
