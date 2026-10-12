"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";

import AdminTabs from "@/components/admin/admin-tabs";
import LessonResultsManager from "@/features/admin/components/lesson-results/lesson-results-manager";
import ExerciseManager from "@/features/admin/components/lesson-skills/exercise-manager";
import GrammarManager from "@/features/admin/components/lesson-skills/grammar-manager";
import HoerenManager from "@/features/admin/components/lesson-skills/hoeren-manager";
import WordManager from "@/features/admin/components/lesson-skills/word-manager";
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
  // deep link from the LMS structure view: ?tab=lesen|hoeren|writing|speaking|results
  const tab = useSearchParams().get("tab");
  const initialTab = tab && ["video", "frage", "grammatik", "lesen", "hoeren", "writing", "speaking", "wortschatz", "yakuniy", "results"].includes(tab) ? tab : "video";

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
        defaultValue={initialTab}
        tabs={[
          { value: "video", label: "Videokurs", content: <VideoManager lessonId={lessonId} /> },
          { value: "frage", label: "Frage des Themas", content: <SpeakingManager lessonId={lessonId} kind="FRAGE" /> },
          { value: "grammatik", label: "Grammatik", content: <GrammarManager lessonId={lessonId} /> },
          { value: "lesen", label: "Lesen", content: <LesenManager lessonId={lessonId} /> },
          { value: "hoeren", label: "Hören", content: <HoerenManager lessonId={lessonId} /> },
          { value: "writing", label: "Schreiben", content: <WritingManager lessonId={lessonId} /> },
          { value: "speaking", label: "Sprechen", content: <SpeakingManager lessonId={lessonId} /> },
          { value: "wortschatz", label: "Wortschatz", content: <WordManager lessonId={lessonId} /> },
          {
            value: "yakuniy",
            label: "Yakuniy Test",
            content: <ExerciseManager lessonId={lessonId} skill="YAKUNIY" label="Yakuniy Test" />,
          },
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
