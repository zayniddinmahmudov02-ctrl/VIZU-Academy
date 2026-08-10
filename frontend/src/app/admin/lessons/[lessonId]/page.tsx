"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";

import AdminTabs from "@/components/admin/admin-tabs";
import GrammarManager from "@/features/admin/components/managers/grammar-manager";
import HomeworkManager from "@/features/admin/components/managers/homework-manager";
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

      <AdminTabs
        defaultValue="video"
        tabs={[
          { value: "video", label: "Video", content: <VideoManager lessonId={lessonId} /> },
          { value: "vocabulary", label: "Vokabeln", content: <VocabularyManager lessonId={lessonId} /> },
          { value: "grammar", label: "Grammatik", content: <GrammarManager lessonId={lessonId} /> },
          { value: "reading", label: "Lesen (Legacy)", content: <ReadingManager lessonId={lessonId} /> },
          {
            value: "lesen-assessment",
            label: "Lesen",
            content: <LesenAssessmentManager lessonId={lessonId} skill="LESEN" />,
          },
          { value: "listening", label: "Hören (Legacy)", content: <ListeningManager lessonId={lessonId} /> },
          {
            value: "hoeren-assessment",
            label: "Hören",
            content: <LesenAssessmentManager lessonId={lessonId} skill="HOEREN" />,
          },
          { value: "writing", label: "Schreiben (Legacy)", content: <WritingManager lessonId={lessonId} /> },
          {
            value: "schreiben-assessment",
            label: "Schreiben",
            content: <LesenAssessmentManager lessonId={lessonId} skill="SCHREIBEN" />,
          },
          { value: "speaking", label: "Sprechen (Legacy)", content: <SpeakingManager lessonId={lessonId} /> },
          {
            value: "sprechen-assessment",
            label: "Sprechen",
            content: <LesenAssessmentManager lessonId={lessonId} skill="SPRECHEN" />,
          },
          { value: "homework", label: "Hausaufgaben", content: <HomeworkManager lessonId={lessonId} /> },
          { value: "quiz", label: "Quiz", content: <QuizManager lessonId={lessonId} /> },
        ]}
      />
    </div>
  );
}
