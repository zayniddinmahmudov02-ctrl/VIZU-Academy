"use client";

import { useQuery } from "@tanstack/react-query";

import {
  getExercises,
  reviewExercise,
  startExercise,
  submitExercise,
  type ExerciseSet,
  type ExerciseSkill,
} from "@/features/lessons/services/lesson-skills-service";
import { useTranslation } from "@/lib/i18n/use-translation";

import SkillTest from "./skill-test";

export const exercisesKey = (lessonId: string, skill: ExerciseSkill) => ["lesson-exercises", lessonId, skill];

export function useExercises(lessonId: string, skill: ExerciseSkill) {
  return useQuery({ queryKey: exercisesKey(lessonId, skill), queryFn: () => getExercises(lessonId, skill) });
}

/** Every published exercise set of one skill, each a server-graded test
 * (the same SkillTest as Lesen / Hören — the key never reaches the browser
 * before an attempt is submitted). */
export default function ExerciseSets({ lessonId, skill, sets }: { lessonId: string; skill: ExerciseSkill; sets: ExerciseSet[] }) {
  const { t } = useTranslation();
  const invalidate = [exercisesKey(lessonId, skill), ["lesson-skill-results", lessonId], ["section-gate", lessonId]];

  return (
    <div className="space-y-10">
      {sets.map((set, i) => (
        <section key={set.id} className="space-y-4" data-testid="exercise-set">
          <div>
            <h3 className="text-lg font-bold text-text-primary">
              {sets.length > 1 && <span className="mr-2 text-text-muted">{i + 1}.</span>}
              {set.title}
            </h3>
            {set.instruction && <p className="mt-1 whitespace-pre-line text-sm text-text-secondary">{set.instruction}</p>}
            {set.source === "vizu" && <p className="mt-1 text-xs text-text-muted">{t("lessons.exerciseSourceVizu")}</p>}
          </div>
          <SkillTest
            testId={`exercise-${skill}`}
            sections={[{ id: set.id, questions: set.questions }]}
            summary={set.summary}
            attempts={set.attempts}
            start={() => startExercise(lessonId, skill, set.id)}
            submit={(attemptId, answers) => submitExercise(lessonId, skill, set.id, attemptId, answers)}
            review={(attemptId) => reviewExercise(lessonId, skill, set.id, attemptId)}
            invalidate={invalidate}
          />
        </section>
      ))}
    </div>
  );
}
