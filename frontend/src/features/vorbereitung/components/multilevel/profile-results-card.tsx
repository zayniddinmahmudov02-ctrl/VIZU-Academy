"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { GraduationCap } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

import { levelLabel, levelTone } from "../../lib/multilevel-labels";
import { getHistory } from "../../services/multilevel-exam-service";

/** Profile: the student's saved Multilevel results (latest five), linking to the full result pages. */
export default function MultilevelProfileResultsCard() {
  const { t } = useTranslation();
  const { data: history = [] } = useQuery({ queryKey: ["multilevel-history"], queryFn: getHistory });
  const finished = history.filter((h) => h.status !== "IN_PROGRESS").slice(0, 5);
  return (
    <section className="rounded-card bg-surface-card p-5 shadow-[var(--shadow-md)] ring-1 ring-surface-border sm:p-7" data-testid="profile-multilevel">
      <h2 className="flex items-center gap-2 text-lg font-bold text-text-primary">
        <GraduationCap size={18} /> Multilevel · {t("multilevelExam.history")}
      </h2>
      {finished.length === 0 ? (
        <p className="mt-3 text-sm text-text-muted">{t("multilevelExam.noHistory")}</p>
      ) : (
        <ul className="mt-3 space-y-2">
          {finished.map((h) => (
            <li key={h.attempt_id} className="flex flex-wrap items-center justify-between gap-2 text-sm">
              <span className="text-text-secondary">{h.title} · {new Date(h.submitted_at ?? h.started_at).toLocaleDateString("de-DE")}</span>
              <span className="flex items-center gap-2">
                <span className="font-semibold text-text-primary">{h.total_score ?? "—"} / 300</span>
                <span className={`rounded-full px-2 py-0.5 text-xs font-bold ${levelTone(h.result_level)}`}>{levelLabel(t, h.result_level)}</span>
                <Link href={`/vorbereitung/multilevel/ergebnis/${h.attempt_id}`} className="font-semibold text-accent-blue hover:underline">
                  {t("multilevelExam.viewResult")}
                </Link>
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
