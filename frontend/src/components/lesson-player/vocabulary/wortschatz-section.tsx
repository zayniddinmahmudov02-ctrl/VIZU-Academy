"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BookOpen, ClipboardCheck, Dumbbell } from "lucide-react";

import LmsFlashcards from "@/components/lms/lms-flashcards";
import { getLessonQuizzes } from "@/features/lessons/services/quiz-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import ExerciseSets, { useExercises } from "../skill-test/exercise-sets";
import WritingSection from "../writing/writing-section";
import VocabularyQuizSection from "./vocabulary-quiz-section";
import WordDictionary from "./word-dictionary";

type Tab = "dictionary" | "exercises" | "tests";

/** Older lessons may still have only the legacy VOCABULARY quiz (it decides
 * their Wortschatz progress) — it stays reachable here. */
function LegacyQuizOrEmpty({ lessonId, hasSets }: { lessonId: string; hasSets: boolean }) {
  const { t } = useTranslation();
  const { data: legacy, isLoading } = useQuery({
    queryKey: ["lesson-quizzes", lessonId, "VOCABULARY"],
    queryFn: () => getLessonQuizzes(lessonId, "VOCABULARY"),
    enabled: !hasSets,
  });
  if (!hasSets && isLoading) return <p className="text-sm text-text-muted">{t("common.loading")}</p>;
  if (!hasSets && (legacy?.length ?? 0) > 0) return <VocabularyQuizSection lessonId={lessonId} />;
  return <p className="rounded-2xl bg-surface-hover/60 p-6 text-center text-text-secondary ring-1 ring-surface-border">{t("lessons.wsTestsEmpty")}</p>;
}

/** Wortschatz (VIZU LMS): three parts of its own, nothing from Schreiben —
 *  Wörterbuch  the lesson's words (WordDictionary),
 *  Übungen     word cards, the course book's Wortschatz exercises and the
 *              written Wortschatz tasks (writings.competency = WORTSCHATZ),
 *  Tests       the server-graded Wortschatz tests built from the words
 *              (exercise sets with source "vizu").
 * Results of the sets and tasks count for the Wortschatz competency only. */
export default function WortschatzSection({ lessonId }: { lessonId: string }) {
  const { t } = useTranslation();
  const [tab, setTab] = useState<Tab>("dictionary");
  const { data: sets, isLoading } = useExercises(lessonId, "wortschatz");
  const bookSets = (sets ?? []).filter((s) => s.source !== "vizu");
  const testSets = (sets ?? []).filter((s) => s.source === "vizu");

  const tabs: { key: Tab; label: string; icon: typeof BookOpen }[] = [
    { key: "dictionary", label: t("lessons.wsTabDictionary"), icon: BookOpen },
    { key: "exercises", label: t("lessons.wsTabExercises"), icon: Dumbbell },
    { key: "tests", label: t("lessons.wsTabTests"), icon: ClipboardCheck },
  ];

  return (
    <div className="space-y-6" data-testid="wortschatz-section">
      <div className="grid grid-cols-3 gap-1 rounded-2xl bg-surface-hover/60 p-1 ring-1 ring-surface-border" role="tablist">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={tab === key}
            onClick={() => setTab(key)}
            className={cn(
              "flex min-h-11 items-center justify-center gap-1.5 rounded-xl px-2 text-sm font-semibold transition",
              tab === key ? "bg-surface-card text-accent-blue shadow-sm ring-1 ring-surface-border" : "text-text-secondary hover:text-text-primary",
            )}
            data-testid={`ws-tab-${key}`}
          >
            <Icon size={15} className="shrink-0" />
            <span className="truncate">{label}</span>
            {key === "tests" && testSets.length > 0 && <span className="rounded-full bg-accent-blue/10 px-1.5 text-[11px] text-accent-blue">{testSets.length}</span>}
          </button>
        ))}
      </div>

      {tab === "dictionary" && <WordDictionary lessonId={lessonId} />}

      {tab === "exercises" && (
        <div className="space-y-8" data-testid="ws-exercises">
          <LmsFlashcards lessonId={lessonId} />
          {bookSets.length > 0 && <ExerciseSets lessonId={lessonId} skill="wortschatz" sets={bookSets} />}
          <WritingSection lessonId={lessonId} competency="WORTSCHATZ" />
        </div>
      )}

      {tab === "tests" && (
        <div data-testid="ws-tests">
          {isLoading ? (
            <p className="text-sm text-text-muted">{t("common.loading")}</p>
          ) : testSets.length ? (
            <ExerciseSets lessonId={lessonId} skill="wortschatz" sets={testSets} />
          ) : (
            <LegacyQuizOrEmpty lessonId={lessonId} hasSets={bookSets.length > 0} />
          )}
        </div>
      )}
    </div>
  );
}
