import type { ComponentType } from "react";
import { notFound } from "next/navigation";

import SectionGateBoundary from "@/components/lesson-player/common/section-gate-boundary";
import PremiumLessonGate from "@/components/lesson-player/video/premium-lesson-gate";
import GrammarSection from "@/components/lesson-player/grammar/grammar-section";
import ListeningSection from "@/components/lesson-player/listening/listening-section";
import FinalTestSection from "@/components/lesson-player/quiz/final-test-section";
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
  frage: (props) => <SpeakingSection {...props} kind="FRAGE" />,
  grammar: GrammarSection,
  reading: ReadingSection,
  listening: ListeningSection,
  writing: WritingSection,
  speaking: SpeakingSection,
  vocabulary: VocabularySection,
  "lesson-quiz": FinalTestSection,
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

  // PremiumLessonGate enforces the free-3-lessons/Premium rule.
  // SectionGateBoundary enforces real sequential section unlocking
  // (server-computed, dynamic per lesson content — see
  // section-gate-boundary.tsx) — this is UX; the actual unbypassable
  // gate lives server-side on each section's submit endpoint.
  return (
    <PremiumLessonGate lessonId={lessonId}>
      <SectionGateBoundary lessonId={lessonId} slug={meta.slug}>
        <SectionComponent lessonId={lessonId} />
      </SectionGateBoundary>
    </PremiumLessonGate>
  );
}
