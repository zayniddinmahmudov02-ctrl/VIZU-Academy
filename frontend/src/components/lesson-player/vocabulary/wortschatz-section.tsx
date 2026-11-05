"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BookOpen, ClipboardCheck } from "lucide-react";

import { getLessonQuizzes } from "@/features/lessons/services/quiz-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import ExerciseSets, { useExercises } from "../skill-test/exercise-sets";
import WritingSection from "../writing/writing-section";
import VocabularyQuizSection from "./vocabulary-quiz-section";
import WordDictionary from "./word-dictionary";

type Tab = "dictionary" | "tests";

/** Older lessons may still have only the legacy VOCABULARY quiz (it decides
 * their Wortschatz progress) — it stays reachable here. */
function LegacyQuizOrEmpty({ lessonId }: { lessonId: string }) {
  const { t } = useTranslation();
  const { data: legacy, isLoading } = useQuery({
    queryKey: ["lesson-quizzes", lessonId, "VOCABULARY"],
    queryFn: () => getLessonQuizzes(lessonId, "VOCABULARY"),
  });
  if (isLoading) return <p className="text-sm text-text-muted">{t("common.loading")}</p>;
  if ((legacy?.length ?? 0) > 0) return <VocabularyQuizSection lessonId={lessonId} />;
  return <p className="rounded-2xl bg-surface-hover/60 p-6 text-center text-text-secondary ring-1 ring-surface-border">{t("lessons.wsTestsEmpty")}</p>;
}

/** Wortschatz (VIZU LMS, all levels): exactly two parts (2026-11-05 — the word cards are gone):
 *  Lug'at / Wörterbuch  the lesson's words with translation, article, plural, examples (WordDictionary),
 *  Testlar / Tests      every graded Wortschatz task: the generated tests (source "vizu"), the course book's
 *                       Wortschatz sets and the written Wortschatz tasks (writings.competency = WORTSCHATZ),
 *                       with their results. Completion = all published Wortschatz test sets done (lms/progress.py). */
export default function WortschatzSection({ lessonId }: { lessonId: string }) {
  const { t } = useTranslation();
  const [tab, setTab] = useState<Tab>("dictionary");
  const { data: sets, isLoading } = useExercises(lessonId, "wortschatz");
  const testSets = (sets ?? []).filter((s) => s.source === "vizu");
  const bookSets = (sets ?? []).filter((s) => s.source !== "vizu");
  const allSets = [...testSets, ...bookSets];

  const tabs: { key: Tab; label: string; icon: typeof BookOpen }[] = [
    { key: "dictionary", label: t("lessons.wsTabDictionary"), icon: BookOpen },
    { key: "tests", label: t("lessons.wsTabTests"), icon: ClipboardCheck },
  ];

  return (
    <div className="space-y-6" data-testid="wortschatz-section">
      <div className="grid grid-cols-2 gap-1 rounded-2xl bg-surface-hover/60 p-1 ring-1 ring-surface-border" role="tablist">
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
            {key === "tests" && allSets.length > 0 && <span className="rounded-full bg-accent-blue/10 px-1.5 text-[11px] text-accent-blue">{allSets.length}</span>}
          </button>
        ))}
      </div>

      {tab === "dictionary" && <WordDictionary lessonId={lessonId} />}

      {tab === "tests" && (
        <div className="space-y-8" data-testid="ws-tests">
          {isLoading ? (
            <p className="text-sm text-text-muted">{t("common.loading")}</p>
          ) : allSets.length ? (
            <ExerciseSets lessonId={lessonId} skill="wortschatz" sets={allSets} />
          ) : (
            <LegacyQuizOrEmpty lessonId={lessonId} />
          )}
          <WritingSection lessonId={lessonId} competency="WORTSCHATZ" />
        </div>
      )}
    </div>
  );
}
