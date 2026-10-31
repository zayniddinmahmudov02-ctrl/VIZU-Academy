"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { History } from "lucide-react";

import { getMyWritingHistory } from "@/features/lessons/services/writing-submission-service";
import { useTranslation } from "@/lib/i18n/use-translation";

/** The student's own submitted versions (exact text, newest first) with the
 * result of each analysis run and each teacher decision — nothing is lost
 * when a task is analysed again or re-submitted. Loaded on demand. */
export default function WritingHistory({ writingId, refreshKey }: { writingId: string; refreshKey?: string | null }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const { data, isLoading } = useQuery({
    queryKey: ["writing-history", writingId, refreshKey],
    queryFn: () => getMyWritingHistory(writingId),
    enabled: open,
  });

  return (
    <details className="rounded-xl bg-surface-hover/40 px-3 py-2 text-sm ring-1 ring-surface-border" onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)}
             data-testid="writing-history">
      <summary className="flex min-h-10 cursor-pointer items-center gap-2 font-semibold text-text-primary">
        <History size={15} /> {t("lessons.historyTitle")}
      </summary>
      {isLoading && <p className="py-2 text-xs text-text-muted">{t("common.loading")}</p>}
      {data && data.versions.length === 0 && <p className="py-2 text-xs text-text-muted">{t("lessons.historyEmpty")}</p>}
      <ol className="mt-2 space-y-3">
        {data?.versions.map((v) => (
          <li key={v.attempt_number} className="rounded-xl bg-surface-card p-3 ring-1 ring-surface-border" data-testid="writing-version">
            <p className="text-xs font-semibold text-text-muted">
              {t("lessons.historyVersion", { n: v.attempt_number })} · {new Date(v.submitted_at).toLocaleString()} · {t("lessons.historyWords", { n: v.word_count })}
            </p>
            <p className="mt-1.5 whitespace-pre-line break-words text-text-primary">{v.answer_text}</p>
            <ul className="mt-2 space-y-1">
              {v.evaluations.map((e) => (
                <li key={e.id} className="text-xs text-text-secondary">
                  {e.source === "MANUAL_OVERRIDE"
                    ? t("lessons.historyTeacher", { score: e.score ?? "—" })
                    : e.status === "SUCCEEDED"
                      ? t("lessons.historyAi", { score: e.score ?? "—" })
                      : t("lessons.historyAiFailed")}
                  {" · "}
                  {new Date(e.created_at).toLocaleString()}
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ol>
    </details>
  );
}
