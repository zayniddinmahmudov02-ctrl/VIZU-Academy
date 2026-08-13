"use client";

import { useQuery } from "@tanstack/react-query";
import { Languages } from "lucide-react";

import { getLessonGrammars } from "@/features/lessons/services/grammar-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import LessonSection from "../common/lesson-section";

interface Props {
  lessonId: string;
}

/** Real Grammatik panel — published Grammar rows for this lesson (see
 * app/models/grammar.py, admin/components/managers/grammar-manager.tsx).
 * No assessment engine here; Grammar is its own existing, simpler
 * publish-gated content type, reused as-is. */
export default function GrammarSection({ lessonId }: Props) {
  const { t } = useTranslation();

  const { data: items, isLoading } = useQuery({
    queryKey: ["lesson-grammars", lessonId],
    queryFn: () => getLessonGrammars(lessonId),
  });

  return (
    <LessonSection
      title={t("lessons.sectionGrammar")}
      description={t("lessons.grammarDescription")}
      icon={Languages}
    >
      {isLoading && <p className="text-sm text-text-secondary">{t("common.loading")}</p>}

      {!isLoading && (items?.length ?? 0) === 0 && (
        <p className="rounded-2xl bg-surface-hover p-6 text-center text-sm text-text-secondary">
          Für diese Lektion sind noch keine Inhalte verfügbar.
        </p>
      )}

      <div className="space-y-5">
        {items?.map((item) => (
          <div key={item.id} className="rounded-2xl bg-surface-hover p-6">
            <h3 className="text-lg font-bold text-text-primary">{item.title}</h3>
            <div
              className="prose-editor mt-2.5 text-sm text-text-secondary sm:text-base"
              dangerouslySetInnerHTML={{ __html: item.content }}
            />
            {item.video_url && (
              <video controls src={item.video_url} className="mt-4 w-full rounded-xl">
                <track kind="captions" />
              </video>
            )}
          </div>
        ))}
      </div>
    </LessonSection>
  );
}
