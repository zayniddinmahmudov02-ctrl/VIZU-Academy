"use client";

import { Headphones } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { getLessonListenings } from "@/features/lessons/services/listening-service";
import { useTranslation } from "@/lib/i18n/use-translation";

import LessonSection from "../common/lesson-section";
import ListeningPlayer from "./listening-player";

interface Props {
  lessonId: string;
}

/** The real Hören player — published Listening rows for this lesson
 * (see app/models/listening.py, admin/components/managers/listening-
 * manager.tsx). Legacy-backed on purpose, same as its Lesen/Schreiben/
 * Sprechen siblings — see reading-section.tsx's docstring. A row with
 * no real audio_url yet keeps the section visible (see
 * SectionGateService._listening_applicable, existence-only) but shows
 * the transcript with an explicit "audio not ready yet" state instead
 * of a broken/empty player, rather than hiding the section entirely. */
export default function ListeningSection({ lessonId }: Props) {
  const { t } = useTranslation();

  const { data: items, isLoading } = useQuery({
    queryKey: ["lesson-listenings", lessonId],
    queryFn: () => getLessonListenings(lessonId),
  });

  return (
    <LessonSection title={t("lessons.sectionListening")} description={t("lessons.listeningDescription")} icon={Headphones}>
      {isLoading && <p className="text-sm text-text-muted">{t("common.loading")}</p>}

      {!isLoading && (items?.length ?? 0) === 0 && (
        <div className="rounded-2xl bg-surface-hover/60 p-6 text-center ring-1 ring-surface-border sm:p-8">
          <p className="text-text-secondary">Für diese Lektion sind noch keine Hörübungen verfügbar.</p>
        </div>
      )}

      <div className="space-y-5">
        {items?.map((item) => (
          <div key={item.id} className="rounded-2xl bg-surface-hover p-6">
            <h3 className="text-lg font-bold text-text-primary">{item.title}</h3>

            {item.audio_url ? (
              <div className="mt-4">
                <ListeningPlayer src={item.audio_url} />
              </div>
            ) : (
              <div className="mt-4 rounded-xl bg-surface-card p-4 text-center ring-1 ring-surface-border">
                <p className="text-sm text-text-muted">Audio für diesen Text ist noch nicht verfügbar.</p>
              </div>
            )}

            {item.transcript && (
              <div className="prose-editor mt-4 text-sm text-text-secondary sm:text-base">
                <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Transkript</p>
                <p className="whitespace-pre-line">{item.transcript}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </LessonSection>
  );
}
