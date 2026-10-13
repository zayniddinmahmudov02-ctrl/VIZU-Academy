"use client";

import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";

import GrammarSection from "@/components/lesson-player/grammar/grammar-section";
import ListeningSection from "@/components/lesson-player/listening/listening-section";
import FinalTestSection from "@/components/lesson-player/quiz/final-test-section";
import ReadingSection from "@/components/lesson-player/reading/reading-section";
import SkillResultsPanel from "@/components/lesson-player/results/skill-results-panel";
import ExerciseSets, { useExercises } from "@/components/lesson-player/skill-test/exercise-sets";
import SpeakingSection from "@/components/lesson-player/speaking/speaking-section";
import VocabularySection from "@/components/lesson-player/vocabulary/vocabulary-section";
import WritingSection from "@/components/lesson-player/writing/writing-section";
import { getLessonSpeakings } from "@/features/lessons/services/speaking-service";
import type { LmsCompetency, LmsLesson, LmsResource, LmsVideo } from "@/features/lms/types";
import { useTranslation } from "@/lib/i18n/use-translation";

import LmsResourceList from "./lms-resource-list";
import LmsVideos from "./lms-video";

/** Frage des Themas belongs to the Einführung — shown only when the lesson
 * has such a task (same query key as SpeakingSection, so one request). */
function FrageIfAny({ lessonId }: { lessonId: string }) {
  const { data } = useQuery({ queryKey: ["lesson-speakings", lessonId, "FRAGE"], queryFn: () => getLessonSpeakings(lessonId, "FRAGE") });
  if (!data?.length) return null;
  return <SpeakingSection lessonId={lessonId} kind="FRAGE" />;
}

function Uebungen({ lessonId }: { lessonId: string }) {
  const { t } = useTranslation();
  const { data: sets, isLoading } = useExercises(lessonId, "uebungen");
  if (isLoading) return <p className="text-sm text-text-muted">{t("common.loading")}</p>;
  if (!sets?.length) return null;
  return <ExerciseSets lessonId={lessonId} skill="uebungen" sets={sets} />;
}

/** The content of one competency: the admin's text, its videos, the existing
 * lesson section that holds its tasks (unchanged components, same APIs) and
 * its resources. */
export default function LmsCompetencyContent({
  data,
  competency,
  reloadVideos,
  reloadResources,
}: {
  data: LmsLesson;
  competency: LmsCompetency;
  reloadVideos: () => Promise<LmsVideo[] | undefined>;
  reloadResources: () => Promise<LmsResource[] | undefined>;
}) {
  const { t } = useTranslation();
  const lessonId = data.lesson.id;
  const kind = competency.kind;
  const videos = data.videos.filter((v) => v.competency === kind);
  const resources = data.resources.filter((r) => r.competency === kind);

  let section: ReactNode = null;
  switch (kind) {
    case "EINFUEHRUNG":
      section = <FrageIfAny lessonId={lessonId} />;
      break;
    case "WORTSCHATZ":
      section = <VocabularySection lessonId={lessonId} />;
      break;
    case "GRAMMATIK":
      section = <GrammarSection lessonId={lessonId} />;
      break;
    case "LESEN":
      section = <ReadingSection lessonId={lessonId} />;
      break;
    case "HOEREN":
      section = <ListeningSection lessonId={lessonId} />;
      break;
    case "SPRECHEN":
      section = <SpeakingSection lessonId={lessonId} />;
      break;
    case "SCHREIBEN":
      section = <WritingSection lessonId={lessonId} />;
      break;
    case "UEBUNGEN":
      section = <Uebungen lessonId={lessonId} />;
      break;
    case "ABSCHLUSSTEST":
      section = <FinalTestSection lessonId={lessonId} />;
      break;
    case "ZUSAMMENFASSUNG":
      section = (
        <div className="space-y-6">
          <div className="rounded-2xl bg-surface-hover/60 p-5 ring-1 ring-surface-border" data-testid="lms-summary">
            <p className="text-sm text-text-secondary">
              {t("lms.summaryProgress", { done: data.competencies_completed, total: data.competencies_total })}
            </p>
            <p className="mt-1 text-lg font-bold text-text-primary">
              {data.completed ? t("lms.lessonCompleted") : t("lms.lessonNotCompleted")}
            </p>
          </div>
          <SkillResultsPanel lessonId={lessonId} />
        </div>
      );
      break;
  }

  return (
    <div className="space-y-8" data-testid="lms-competency-content" data-kind={kind}>
      {competency.body && (
        // sanitised on the server (allow-list, app/core/utils/safe_html.py)
        <div className="prose-editor rounded-2xl bg-surface-card p-5 text-[15px] leading-relaxed text-text-primary ring-1 ring-surface-border sm:p-6"
             data-testid="lms-competency-body"
             dangerouslySetInnerHTML={{ __html: competency.body }} />
      )}
      <LmsVideos lessonId={lessonId} videos={videos} onReload={reloadVideos} />
      {section}
      <LmsResourceList resources={resources} onReload={reloadResources} />
    </div>
  );
}
