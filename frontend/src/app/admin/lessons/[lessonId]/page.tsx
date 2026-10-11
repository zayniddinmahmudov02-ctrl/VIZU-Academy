"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";

import AdminTabs from "@/components/admin/admin-tabs";
import LessonResultsManager from "@/features/admin/components/lesson-results/lesson-results-manager";
import HoerenManager from "@/features/admin/components/lesson-skills/hoeren-manager";
import LesenManager from "@/features/admin/components/lesson-skills/lesen-manager";
import SkillResultsAdmin from "@/features/admin/components/lesson-skills/skill-results-admin";
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

      {/* One place per lesson for the four book skills: Lesen texts and
          Hören audio with their auto-graded questions (answer keys stay
          server-side for students), Schreiben / Sprechen tasks with their
          AI-evaluation settings, and the students' results incl. AI review,
          audited score correction and re-evaluation. Teacher review of
          non-AI tasks stays in the Teacher Panel. */}
      <AdminTabs
        defaultValue="video"
        tabs={[
          { value: "video", label: "Videokurs", content: <VideoManager lessonId={lessonId} /> },
          { value: "lesen", label: "Lesen", content: <LesenManager lessonId={lessonId} /> },
          { value: "hoeren", label: "Hören", content: <HoerenManager lessonId={lessonId} /> },
          { value: "writing", label: "Schreiben", content: <WritingManager lessonId={lessonId} /> },
          { value: "speaking", label: "Sprechen", content: <SpeakingManager lessonId={lessonId} /> },
          {
            value: "results",
            label: "Schülerergebnisse",
            content: (
              <div className="space-y-10">
                <SkillResultsAdmin lessonId={lessonId} />
                <div>
                  <h3 className="mb-3 text-base font-bold text-[var(--admin-text-primary)]">Punkteübersicht pro Schüler (100-Punkte-Lektion)</h3>
                  <LessonResultsManager lessonId={lessonId} />
                </div>
              </div>
            ),
          },
        ]}
      />
    </div>
  );
}
