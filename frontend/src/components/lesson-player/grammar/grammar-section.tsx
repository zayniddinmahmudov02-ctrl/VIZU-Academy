"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Languages } from "lucide-react";

import { completeLessonGrammar, getLessonGrammars } from "@/features/lessons/services/grammar-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import LessonSection from "../common/lesson-section";

interface Props {
  lessonId: string;
}

/** Real Grammatik panel — published Grammar rows for this lesson (see
 * app/models/grammar.py, admin/components/managers/grammar-manager.tsx).
 * No assessment engine here; Grammar is its own existing, simpler
 * publish-gated content type, reused as-is. "Als gelesen markieren"
 * persists StudentProgress.grammar_completed server-side, which unlocks
 * Grammatik Quiz next in the sequence (see section-gate-service). */
export default function GrammarSection({ lessonId }: Props) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const { data: items, isLoading } = useQuery({
    queryKey: ["lesson-grammars", lessonId],
    queryFn: () => getLessonGrammars(lessonId),
  });

  const completeMutation = useMutation({
    mutationFn: () => completeLessonGrammar(lessonId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["section-gate", lessonId] });
    },
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

      {(items?.length ?? 0) > 0 && (
        <div className="mt-5">
          <button
            type="button"
            disabled={completeMutation.isPending || completeMutation.isSuccess}
            onClick={() => completeMutation.mutate()}
            className="inline-flex items-center gap-1.5 rounded-button bg-gradient-to-r from-accent-blue-hover to-accent-blue px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-accent-blue/25 transition enabled:hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {completeMutation.isSuccess
              ? "Grammatik abgeschlossen ✓"
              : completeMutation.isPending
                ? "Wird gespeichert..."
                : "Als gelesen markieren"}
          </button>
        </div>
      )}
    </LessonSection>
  );
}
