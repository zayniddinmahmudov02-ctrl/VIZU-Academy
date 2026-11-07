"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Check, X } from "lucide-react";

import { formatDuration, levelLabel, levelTone, SECTION_LABEL_KEY } from "@/features/vorbereitung/lib/multilevel-labels";
import { getResult } from "@/features/vorbereitung/services/multilevel-exam-service";
import type { ResultSection } from "@/features/vorbereitung/types/multilevel-exam.types";
import { useTranslation } from "@/lib/i18n/use-translation";

// Result of a finished Multilevel attempt: every section x / 75 with its level, total / 300, overall level (or
// "Ungeklärt" while no overall rule is confirmed), date, duration and — only now — the Lesen / Hören answers.
export default function MultilevelResultPage() {
  const { attemptId } = useParams<{ attemptId: string }>();
  const { t } = useTranslation();
  const { data: result, isError } = useQuery({ queryKey: ["multilevel-result", attemptId], queryFn: () => getResult(attemptId) });

  return (
    <div className="mx-auto max-w-3xl space-y-6" data-testid="exam-result">
      <Link href="/vorbereitung/multilevel" className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary hover:text-accent-blue">
        <ArrowLeft size={16} /> {t("multilevelExam.back")}
      </Link>
      {isError && <p className="text-sm text-text-secondary">{t("multilevelExam.resultsAfterFinish")}</p>}
      {result && (
        <>
          <header className="rounded-2xl bg-surface-card p-5 ring-1 ring-surface-border sm:p-6">
            <p className="text-sm text-text-muted">{t("multilevelExam.resultTitle")} · {result.title}</p>
            <div className="mt-3 flex flex-wrap items-end gap-x-6 gap-y-3">
              <div>
                <p className="text-xs uppercase text-text-muted">{t("multilevelExam.overall")}</p>
                <span className={`mt-1 inline-block rounded-full px-3 py-1 text-lg font-bold ${levelTone(result.result_level)}`} data-testid="overall-level">
                  {levelLabel(t, result.result_level)}
                </span>
              </div>
              <div>
                <p className="text-xs uppercase text-text-muted">{t("multilevelExam.total")}</p>
                <p className="text-2xl font-bold text-text-primary" data-testid="total-score">{result.total_score ?? "—"} / {result.max_score}</p>
              </div>
              <div className="text-sm text-text-secondary">
                <p>{t("multilevelExam.date")}: {new Date(result.submitted_at ?? result.started_at).toLocaleDateString("de-DE")}</p>
                <p>{t("multilevelExam.duration")}: {formatDuration(result.duration_seconds)}</p>
              </div>
            </div>
            {result.result_level === "UNGEKLAERT" && result.result_rule === "UNCONFIRMED" && (
              <p className="mt-3 text-xs text-text-muted">{t("multilevelExam.overallUnconfirmed")}</p>
            )}
          </header>

          <div className="grid gap-3 sm:grid-cols-2">
            {result.sections.map((s) => (
              <SectionCard key={s.type} s={s} />
            ))}
          </div>

          {result.sections.filter((s) => s.review?.length).map((s) => (
            <details key={s.type} className="rounded-2xl bg-surface-card p-4 ring-1 ring-surface-border sm:p-5">
              <summary className="cursor-pointer text-sm font-semibold text-text-primary">{t("multilevelExam.review")} — {t(SECTION_LABEL_KEY[s.type])}</summary>
              <ol className="mt-3 space-y-2">
                {s.review!.map((r) => {
                  const text = (ids: string[]) => ids.map((id) => {
                    const i = r.options.findIndex((o) => o.id === id);
                    return i >= 0 ? `${"ABCDEFGHIJ"[i] ?? i + 1}) ${r.options[i].option_text}` : "";
                  }).join(", ");
                  return (
                    <li key={r.question_id} className="rounded-xl bg-surface-hover/50 p-3 text-sm">
                      <p className="flex items-start gap-2 font-medium text-text-primary">
                        {r.is_correct ? <Check size={15} className="mt-0.5 shrink-0 text-success" /> : <X size={15} className="mt-0.5 shrink-0 text-danger" />}
                        <span className="line-clamp-3 break-words">{r.question_text}</span>
                      </p>
                      <p className="mt-1 text-xs text-text-secondary">{t("multilevelExam.yourAnswer")}: {r.chosen.length ? text(r.chosen) : t("multilevelExam.noAnswer")}</p>
                      {!r.is_correct && <p className="text-xs text-success">{t("multilevelExam.correctAnswer")}: {text(r.correct)}</p>}
                    </li>
                  );
                })}
              </ol>
            </details>
          ))}
        </>
      )}
    </div>
  );
}

function SectionCard({ s }: { s: ResultSection }) {
  const { t } = useTranslation();
  return (
    <div className="rounded-2xl bg-surface-card p-5 ring-1 ring-surface-border" data-testid={`result-${s.type}`}>
      <p className="text-sm font-semibold text-text-primary">{t(SECTION_LABEL_KEY[s.type])}</p>
      {s.awaiting_grading ? (
        <p className="mt-2 text-sm text-text-muted">{t("multilevelExam.awaiting")}</p>
      ) : (
        <div className="mt-2 flex items-center gap-3">
          <p className="text-2xl font-bold text-text-primary">{s.score ?? "—"} <span className="text-sm font-medium text-text-muted">/ {s.max}</span></p>
          <span className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${levelTone(s.level)}`}>{levelLabel(t, s.level)}</span>
        </div>
      )}
      {s.raw_max !== null && s.raw_points !== null && <p className="mt-1 text-xs text-text-muted">{s.raw_points} / {s.raw_max}</p>}
      {s.feedback && <p className="mt-2 whitespace-pre-line text-xs text-text-secondary">{t("multilevelExam.feedback")}: {s.feedback}</p>}
    </div>
  );
}
