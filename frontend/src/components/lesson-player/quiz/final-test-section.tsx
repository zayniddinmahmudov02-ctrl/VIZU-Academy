"use client";

import { ClipboardCheck } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

import LessonSection from "../common/lesson-section";
import ExerciseSets, { useExercises } from "../skill-test/exercise-sets";
import QuizSection from "./quiz-section";

/** Yakuniy Test: the lesson's final test on its grammar and Wortschatz,
 * graded on the server. Lessons without one keep their legacy LESSON quiz. */
export default function FinalTestSection({ lessonId }: { lessonId: string }) {
  const { t } = useTranslation();
  const { data: sets, isLoading } = useExercises(lessonId, "yakuniy");

  if (isLoading) {
    return (
      <LessonSection title={t("lessons.sectionLessonQuiz")} description={t("lessons.finalTestDescription")} icon={ClipboardCheck}>
        <p className="text-sm text-text-muted">{t("common.loading")}</p>
      </LessonSection>
    );
  }
  if (!sets?.length) return <QuizSection lessonId={lessonId} quizType="LESSON" />;

  return (
    <LessonSection title={t("lessons.sectionLessonQuiz")} description={t("lessons.finalTestDescription")} icon={ClipboardCheck}>
      <ExerciseSets lessonId={lessonId} skill="yakuniy" sets={sets} />
    </LessonSection>
  );
}
