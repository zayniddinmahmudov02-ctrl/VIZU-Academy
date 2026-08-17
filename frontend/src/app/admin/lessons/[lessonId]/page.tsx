"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";

import AdminTabs from "@/components/admin/admin-tabs";
import GrammarManager from "@/features/admin/components/managers/grammar-manager";
import HomeworkManager from "@/features/admin/components/managers/homework-manager";
import LessonResultsManager from "@/features/admin/components/lesson-results/lesson-results-manager";
import LesenAssessmentManager from "@/features/admin/components/lesen/lesen-assessment-manager";
import ListeningManager from "@/features/admin/components/managers/listening-manager";
import QuizManager from "@/features/admin/components/managers/quiz-manager";
import ReadingManager from "@/features/admin/components/managers/reading-manager";
import SpeakingManager from "@/features/admin/components/managers/speaking-manager";
import VideoManager from "@/features/admin/components/managers/video-manager";
import VocabularyManager from "@/features/admin/components/managers/vocabulary-manager";
import WritingManager from "@/features/admin/components/managers/writing-manager";
import { getLesson } from "@/features/admin/services/lessons-service";

export default function LessonEditorPage() {
  const params = useParams<{ lessonId: string }>();
  const router = useRouter();
  const lessonId = params.lessonId;

  const { data: lesson } = useQuery({
    queryKey: ["lesson", lessonId],
    queryFn: () => getLesson(lessonId),
  });

  return (
    <div>
      <button
        onClick={() => router.push("/admin/lessons")}
        className="mb-4 flex items-center gap-1.5 text-sm font-medium text-[var(--admin-text-secondary)] hover:text-[var(--admin-text-primary)]"
      >
        <ArrowLeft size={15} />
        Zurück zu Lektionen
      </button>

      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-[var(--admin-text-primary)]">
          {lesson ? `${lesson.number}. ${lesson.title}` : "Lektion wird geladen..."}
        </h1>
        <p className="mt-1 text-sm text-[var(--admin-text-secondary)]">
          Verwalte alle Inhalte dieser Lektion.
        </p>
      </div>

      {/* Fixed content order matching the 7-step student flow (Video ->
          Wortschatz -> Grammatik Quiz -> Lesen -> Hören -> Schreiben ->
          Sprechen), plus Lesson Quiz as a separate diagnostic — never
          reordered based on which sections happen to have content yet.
          The "Grammatik" tab manages the Grammar model directly after
          Video for authoring convenience; it's admin-only content
          management, not a step in the student-facing lesson flow (see
          lessonSections in constants/lesson-sections.ts). Homework and
          the legacy per-skill managers (pre-Assessment-Engine) are kept
          for existing content but placed after the required order rather
          than interleaved with it. */}
      <AdminTabs
        defaultValue="video"
        tabs={[
          { value: "video", label: "Video", content: <VideoManager lessonId={lessonId} /> },
          { value: "vocabulary", label: "Wortschatz", content: <VocabularyManager lessonId={lessonId} /> },
          { value: "grammar", label: "Grammatik", content: <GrammarManager lessonId={lessonId} /> },
          {
            value: "grammar-quiz",
            label: "Grammatik Quiz",
            content: <QuizManager lessonId={lessonId} quizType="GRAMMAR" />,
          },
          {
            value: "lesen-assessment",
            label: "Lesen",
            content: <LesenAssessmentManager lessonId={lessonId} skill="LESEN" />,
          },
          {
            value: "hoeren-assessment",
            label: "Hören",
            content: <LesenAssessmentManager lessonId={lessonId} skill="HOEREN" />,
          },
          {
            value: "schreiben-assessment",
            label: "Schreiben",
            content: <LesenAssessmentManager lessonId={lessonId} skill="SCHREIBEN" />,
          },
          {
            value: "sprechen-assessment",
            label: "Sprechen",
            content: <LesenAssessmentManager lessonId={lessonId} skill="SPRECHEN" />,
          },
          {
            value: "lesson-quiz",
            label: "Lesson Quiz",
            content: <QuizManager lessonId={lessonId} quizType="LESSON" />,
          },
          { value: "homework", label: "Hausaufgaben", content: <HomeworkManager lessonId={lessonId} /> },
          { value: "reading", label: "Lesen (Legacy)", content: <ReadingManager lessonId={lessonId} /> },
          { value: "listening", label: "Hören (Legacy)", content: <ListeningManager lessonId={lessonId} /> },
          { value: "writing", label: "Schreiben (Legacy)", content: <WritingManager lessonId={lessonId} /> },
          { value: "speaking", label: "Sprechen (Legacy)", content: <SpeakingManager lessonId={lessonId} /> },
          { value: "results", label: "Ergebnisse", content: <LessonResultsManager lessonId={lessonId} /> },
        ]}
      />
    </div>
  );
}
