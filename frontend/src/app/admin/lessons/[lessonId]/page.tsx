"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";

import AdminTabs from "@/components/admin/admin-tabs";
import HoerenQuizImport from "@/features/admin/components/managers/hoeren-quiz-import";
import LessonResultsManager from "@/features/admin/components/lesson-results/lesson-results-manager";
import ListeningManager from "@/features/admin/components/managers/listening-manager";
import SpeakingManager from "@/features/admin/components/managers/speaking-manager";
import VideoManager from "@/features/admin/components/managers/video-manager";
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

      {/* Content management is deliberately limited to what an admin still
          authors by hand: the lesson's Video, the Hören audio upload, and
          the Schreiben / Sprechen task definitions. Lesen, Wortschatz Test,
          Yakuniy Test and every other exercise/test content is produced
          externally (Claude) and imported straight into the database —
          there are no test/question/vocabulary/grammar creators or
          generators in the admin panel any more. The Hören Quiz tab is a
          CSV import, not a question editor, for the same reason (see
          hoeren-quiz-import.tsx). Student submissions are reviewed in the
          Teacher Panel, never here ("Ergebnisse" is a read-only
          per-student score view). */}
      <AdminTabs
        defaultValue="video"
        tabs={[
          { value: "video", label: "Videokurs", content: <VideoManager lessonId={lessonId} /> },
          { value: "listening", label: "Hören Audio", content: <ListeningManager lessonId={lessonId} /> },
          { value: "hoeren-quiz", label: "Hören Quiz (CSV)", content: <HoerenQuizImport lessonId={lessonId} /> },
          { value: "writing", label: "Schreiben Aufgabe", content: <WritingManager lessonId={lessonId} /> },
          { value: "speaking", label: "Sprechen Aufgabe", content: <SpeakingManager lessonId={lessonId} /> },
          { value: "results", label: "Ergebnisse", content: <LessonResultsManager lessonId={lessonId} /> },
        ]}
      />
    </div>
  );
}
