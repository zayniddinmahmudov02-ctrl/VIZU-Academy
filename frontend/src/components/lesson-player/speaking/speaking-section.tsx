"use client";

import { MessageCircleQuestion, Mic } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { getLessonSpeakings } from "@/features/lessons/services/speaking-service";
import { useTranslation } from "@/lib/i18n/use-translation";

import LessonSection from "../common/lesson-section";
import SpeakingTaskRecorder from "./speaking-task-recorder";

interface Props {
  lessonId: string;
  /** FRAGE = Frage des Themas (same recorder, its own step and tasks) */
  kind?: "SPRECHEN" | "FRAGE";
}

/** The real Sprechen panel — published Speaking rows for this lesson
 * (see app/models/speaking.py), each now paired with a real microphone
 * recorder (SpeakingTaskRecorder — MediaRecorder, pause/resume, preview,
 * re-record, upload) backed by StudentSpeaking
 * (app/models/student_speaking.py), a table that already existed but had
 * no user_id column and no real submission workflow until now. Legacy-
 * backed on purpose, same as its Lesen/Hören/Schreiben siblings — see
 * reading-section.tsx's docstring; only the "view-only" half no longer
 * applies to this section specifically. */
export default function SpeakingSection({ lessonId, kind = "SPRECHEN" }: Props) {
  const { t } = useTranslation();
  const frage = kind === "FRAGE";

  const { data: items, isLoading } = useQuery({
    queryKey: ["lesson-speakings", lessonId, kind],
    queryFn: () => getLessonSpeakings(lessonId, kind),
  });

  return (
    <LessonSection
      title={t(frage ? "lessons.sectionFrage" : "lessons.sectionSpeaking")}
      description={t(frage ? "lessons.frageDescription" : "lessons.speakingDescription")}
      icon={frage ? MessageCircleQuestion : Mic}
    >
      {isLoading && <p className="text-sm text-text-muted">{t("common.loading")}</p>}

      {!isLoading && (items?.length ?? 0) === 0 && (
        <div className="rounded-2xl bg-surface-hover/60 p-6 text-center ring-1 ring-surface-border sm:p-8">
          <p className="text-text-secondary">{frage ? t("lessons.frageEmpty") : "Für diese Lektion ist noch keine Sprechaufgabe verfügbar."}</p>
        </div>
      )}

      <div className="space-y-5">
        {items?.map((item) => (
          <div key={item.id} className="rounded-2xl bg-surface-hover p-6">
            <h3 className="text-lg font-bold text-text-primary">{item.title}</h3>
            {item.topic && item.topic !== item.title && <p className="mt-1 text-sm text-text-muted">{item.topic}</p>}
            <p className="mt-2.5 whitespace-pre-line text-sm text-text-secondary sm:text-base">{item.instruction}</p>
            {!!item.questions?.length && (
              <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm text-text-primary" data-testid="speaking-questions">
                {item.questions.map((q, i) => (
                  <li key={i}>{q}</li>
                ))}
              </ol>
            )}
            <div className="mt-3 flex flex-wrap gap-3 text-xs text-text-muted">
              {item.response_type === "DIALOG" && <span className="font-semibold">{t("lessons.speakingDialog")}</span>}
              {item.preparation_time > 0 && <span>Vorbereitung: {item.preparation_time}s</span>}
              <span>Sprechzeit: {item.speaking_time}s</span>
            </div>
            <SpeakingTaskRecorder speaking={item} />
          </div>
        ))}
      </div>
    </LessonSection>
  );
}
