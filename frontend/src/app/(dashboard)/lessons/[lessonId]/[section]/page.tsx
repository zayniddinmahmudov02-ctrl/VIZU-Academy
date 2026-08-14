import type { ComponentType } from "react";
import { notFound } from "next/navigation";

import GrammarSection from "@/components/lesson-player/grammar/grammar-section";
import HomeworkSection from "@/components/lesson-player/homework/homework-section";
import LessonActivityGate from "@/components/lesson-player/video/lesson-activity-gate";
import PremiumLessonGate from "@/components/lesson-player/video/premium-lesson-gate";
import ListeningSection from "@/components/lesson-player/listening/listening-section";
import QuizSection from "@/components/lesson-player/quiz/quiz-section";
import ReadingSection from "@/components/lesson-player/reading/reading-section";
import ResultSection from "@/components/lesson-player/results/result-section";
import SpeakingSection from "@/components/lesson-player/speaking/speaking-section";
import VideoSection from "@/components/lesson-player/video/video-section";
import VocabularySection from "@/components/lesson-player/vocabulary/vocabulary-section";
import WritingSection from "@/components/lesson-player/writing/writing-section";
import { getSectionBySlug, type LessonSectionMeta } from "@/constants/lesson-sections";

interface SectionComponentProps {
  lessonId: string;
}

const SECTION_COMPONENTS: Record<LessonSectionMeta["type"], ComponentType<SectionComponentProps>> = {
  video: VideoSection,
  vocabulary: VocabularySection,
  grammar: GrammarSection,
  "grammar-quiz": (props) => <QuizSection {...props} quizType="GRAMMAR" />,
  reading: ReadingSection,
  listening: ListeningSection,
  writing: WritingSection,
  speaking: SpeakingSection,
  "lesson-quiz": (props) => <QuizSection {...props} quizType="LESSON" />,
  homework: HomeworkSection,
  results: ResultSection,
};

interface Props {
  params: Promise<{
    lessonId: string;
    section: string;
  }>;
}

export default async function LessonSectionPage({ params }: Props) {
  const { lessonId, section } = await params;

  const meta = getSectionBySlug(section);

  if (!meta) {
    notFound();
  }

  const SectionComponent = SECTION_COMPONENTS[meta.type];

  return (
    <PremiumLessonGate lessonId={lessonId}>
      {meta.type === "video" ? (
        <SectionComponent lessonId={lessonId} />
      ) : (
        <LessonActivityGate lessonId={lessonId}>
          <SectionComponent lessonId={lessonId} />
        </LessonActivityGate>
      )}
    </PremiumLessonGate>
  );
}
