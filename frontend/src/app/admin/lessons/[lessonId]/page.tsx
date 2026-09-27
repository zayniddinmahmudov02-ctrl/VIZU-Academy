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
import ReadingManager from "@/features/admin/components/managers/reading-manager";
import SpeakingManager from "@/features/admin/components/managers/speaking-manager";
import VideoManager from "@/features/admin/components/managers/video-manager";
import VocabularyManager from "@/features/admin/components/managers/vocabulary-manager";
import VocabularyQuizManager from "@/features/admin/components/managers/vocabulary-quiz-manager";
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

      {/* Fixed content order matching the student flow (Video ->
          Wortschatz -> Wortschatz Quiz -> Grammatik -> Lesen -> Hören ->
          Schreiben -> Sprechen) — never reordered based on which sections
          happen to have content yet. "Wortschatz Quiz" is vocabulary-
          management-only in Wortschatz's own tab; it just reviews the
          auto-generated quiz questions (see vocabulary-quiz-manager.tsx)
          — A1 only, no create/delete UI, since the backend keeps it in
          sync with published vocabulary. The "Grammatik" tab manages the
          Grammar model directly after Video for authoring convenience;
          it's admin-only content management, not a step in the
          student-facing lesson flow (see lessonSections in
          constants/lesson-sections.ts).

          Manual test/question authoring (Grammatik Quiz, Lesson Quiz,
          and the Assessment-Engine-based Lesen/Hören editors) was removed
          from the admin panel — that content is now produced externally
          and inserted directly into the DB. Lesen/Hören/Schreiben/
          Sprechen content management stays on the legacy per-skill
          managers below, which are the real, student-facing source (see
          reading-section.tsx's docstring) — audio upload for Hören and
          the reading passage text for Lesen are still fully editable
          here, just without a manual question/answer sub-editor. */}
      <AdminTabs
        defaultValue="video"
        tabs={[
          { value: "video", label: "Video", content: <VideoManager lessonId={lessonId} /> },
          { value: "vocabulary", label: "Wortschatz", content: <VocabularyManager lessonId={lessonId} /> },
          {
            value: "vocabulary-quiz",
            label: "Wortschatz Quiz",
            content: <VocabularyQuizManager lessonId={lessonId} />,
          },
          { value: "grammar", label: "Grammatik", content: <GrammarManager lessonId={lessonId} /> },
          {
            value: "schreiben-assessment",
            label: "Schreiben (Assessment Engine)",
            content: <LesenAssessmentManager lessonId={lessonId} skill="SCHREIBEN" />,
          },
          {
            value: "sprechen-assessment",
            label: "Sprechen (Assessment Engine)",
            content: <LesenAssessmentManager lessonId={lessonId} skill="SPRECHEN" />,
          },
          { value: "homework", label: "Hausaufgaben", content: <HomeworkManager lessonId={lessonId} /> },
          { value: "reading", label: "Lesen", content: <ReadingManager lessonId={lessonId} /> },
          { value: "listening", label: "Hören", content: <ListeningManager lessonId={lessonId} /> },
          { value: "writing", label: "Schreiben", content: <WritingManager lessonId={lessonId} /> },
          { value: "speaking", label: "Sprechen", content: <SpeakingManager lessonId={lessonId} /> },
          { value: "results", label: "Ergebnisse", content: <LessonResultsManager lessonId={lessonId} /> },
        ]}
      />
    </div>
  );
}
