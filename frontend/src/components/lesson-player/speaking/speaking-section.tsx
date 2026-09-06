"use client";

import { Mic } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { getLessonSpeakings } from "@/features/lessons/services/speaking-service";
import { useTranslation } from "@/lib/i18n/use-translation";

import LessonSection from "../common/lesson-section";
import SpeakingTaskRecorder from "./speaking-task-recorder";

interface Props {
  lessonId: string;
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
export default function SpeakingSection({ lessonId }: Props) {
  const { t } = useTranslation();

  const { data: items, isLoading } = useQuery({
    queryKey: ["lesson-speakings", lessonId],
    queryFn: () => getLessonSpeakings(lessonId),
  });

  return (
    <LessonSection title={t("lessons.sectionSpeaking")} description={t("lessons.speakingDescription")} icon={Mic}>
      {isLoading && <p className="text-sm text-text-muted">{t("common.loading")}</p>}

      {!isLoading && (items?.length ?? 0) === 0 && (
        <div className="rounded-2xl bg-surface-hover/60 p-6 text-center ring-1 ring-surface-border sm:p-8">
          <p className="text-text-secondary">Für diese Lektion ist noch keine Sprechaufgabe verfügbar.</p>
        </div>
      )}

      <div className="space-y-5">
        {items?.map((item) => (
          <div key={item.id} className="rounded-2xl bg-surface-hover p-6">
            <h3 className="text-lg font-bold text-text-primary">{item.title}</h3>
            {item.topic && <p className="mt-1 text-sm text-text-muted">{item.topic}</p>}
            <p className="mt-2.5 whitespace-pre-line text-sm text-text-secondary sm:text-base">{item.instruction}</p>
            <div className="mt-3 flex flex-wrap gap-3 text-xs text-text-muted">
              <span>Vorbereitung: {item.preparation_time}s</span>
              <span>Sprechzeit: {item.speaking_time}s</span>
            </div>
            <SpeakingTaskRecorder speaking={item} />
          </div>
        ))}
      </div>
    </LessonSection>
  );
}
