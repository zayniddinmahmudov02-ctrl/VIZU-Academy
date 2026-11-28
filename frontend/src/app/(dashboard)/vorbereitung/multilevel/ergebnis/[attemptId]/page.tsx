"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Check, Minus, X } from "lucide-react";

import { levelLabel, levelTone, SECTION_LABEL_KEY } from "@/features/vorbereitung/lib/multilevel-labels";
import { getHistory, getResult } from "@/features/vorbereitung/services/multilevel-exam-service";
import type { AiEvaluationView, AiTeil, ResultSection } from "@/features/vorbereitung/types/multilevel-exam.types";
import { useTranslation } from "@/lib/i18n/use-translation";

// Result of a finished Multilevel attempt: every section x / 75 with its level, total / max (300, less when a section has no answer key
// and is not scored), the AI assessment and the student's attempt history.
export default function MultilevelResultPage() {
  const { attemptId } = useParams<{ attemptId: string }>();
  const { t, language } = useTranslation();
  const dateLocale = language === "uz" ? "uz-UZ" : language === "en" ? "en-US" : language === "ru" ? "ru-RU" : "de-DE";
  const { data: result, isError } = useQuery({
    queryKey: ["multilevel-result", attemptId],
    queryFn: () => getResult(attemptId),
    refetchInterval: (query) => query.state.data?.sections.some((s) => s.ai_status === "PENDING" || s.ai_status === "RUNNING") ? 3000 : false,
  });
  const history = useQuery({ queryKey: ["multilevel-history"], queryFn: getHistory, enabled: Boolean(result) });

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
                <p>{t("multilevelExam.date")}: {new Date(result.submitted_at ?? result.started_at).toLocaleDateString(dateLocale)}</p>
                <p>{t("multilevelExam.duration")}: {localizedDuration(t, result.duration_seconds)}</p>
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

          <section className="rounded-2xl bg-surface-card p-5 ring-1 ring-surface-border" aria-labelledby="attempt-history-title">
            <h2 id="attempt-history-title" className="text-base font-semibold text-text-primary">{t("multilevelExam.historyTitle")}</h2>
            {history.isLoading ? <p className="mt-3 text-sm text-text-muted">{t("multilevelExam.historyLoading")}</p>
              : history.isError ? <p className="mt-3 text-sm text-text-secondary">{t("multilevelExam.historyUnavailable")}</p>
                : !history.data?.length ? <p className="mt-3 text-sm text-text-muted">{t("multilevelExam.noHistory")}</p>
                  : (
                    <ol className="mt-3 space-y-2">
                      {history.data.filter((attempt) => attempt.status !== "IN_PROGRESS").map((attempt) => (
                        <li key={attempt.attempt_id}>
                          <Link href={`/vorbereitung/multilevel/ergebnis/${attempt.attempt_id}`}
                                className="flex flex-wrap items-center justify-between gap-2 rounded-xl bg-surface-hover/50 p-3 text-sm ring-1 ring-surface-border hover:ring-accent-blue"
                                data-testid="attempt-history-item">
                            <span>
                              <span className="font-semibold text-text-primary">{attempt.title}</span>
                              <span className="ml-2 text-text-secondary">{new Date(attempt.submitted_at ?? attempt.started_at).toLocaleString(dateLocale)}</span>
                              {attempt.attempt_id === result.attempt_id && <span className="ml-2 text-xs text-accent-blue">{t("multilevelExam.currentAttempt")}</span>}
                            </span>
                            <span className="flex items-center gap-2">
                              <span className="font-bold text-text-primary">{attempt.total_score ?? "—"} / {attempt.max_score}</span>
                              <span className={`rounded-full px-2 py-0.5 text-xs font-bold ${levelTone(attempt.result_level)}`}>{levelLabel(t, attempt.result_level)}</span>
                            </span>
                          </Link>
                        </li>
                      ))}
                    </ol>
                  )}
          </section>

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
                    <li key={r.question_id} className="rounded-xl bg-surface-hover/50 p-3 text-sm" data-testid="review-item" data-has-key={r.has_key === false ? "0" : "1"}>
                      <p className="flex items-start gap-2 font-medium text-text-primary">
                        {r.has_key === false ? <Minus size={15} className="mt-0.5 shrink-0 text-text-muted" />
                          : r.is_correct ? <Check size={15} className="mt-0.5 shrink-0 text-success" /> : <X size={15} className="mt-0.5 shrink-0 text-danger" />}
                        <span className="line-clamp-3 break-words">{r.question_text}</span>
                      </p>
                      <p className="mt-1 text-xs text-text-secondary">{t("multilevelExam.yourAnswer")}: {r.chosen.length ? text(r.chosen) : t("multilevelExam.noAnswer")}</p>
                      {r.has_key === false ? <p className="text-xs text-text-muted">{t("multilevelExam.noKeyQuestion")}</p>
                        : !r.is_correct && <p className="text-xs text-success">{t("multilevelExam.correctAnswer")}: {text(r.correct)}</p>}
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
      {s.no_key ? (
        <p className="mt-2 text-sm text-text-muted" data-testid="section-no-key">{t("multilevelExam.noKeySection")}</p>
      ) : s.awaiting_grading ? (
        <p className="mt-2 text-sm text-text-muted">
          {s.ai_status === "FAILED" ? t("multilevelExam.aiEvaluationFailed")
            : s.ai_status === "NEEDS_ADMIN" ? t("multilevelExam.aiReviewNeeded")
              : t("multilevelExam.awaiting")}
        </p>
      ) : (
        <div className="mt-2 flex items-center gap-3">
          <p className="text-2xl font-bold text-text-primary">{s.score ?? "—"} <span className="text-sm font-medium text-text-muted">/ {s.max}</span></p>
          <span className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${levelTone(s.level)}`}>{levelLabel(t, s.level)}</span>
        </div>
      )}
      {!s.no_key && s.raw_max !== null && s.raw_points !== null && <p className="mt-1 text-xs text-text-muted">{s.raw_points} / {s.raw_max}</p>}
      {s.feedback && <p className="mt-2 whitespace-pre-line text-xs text-text-secondary">{t("multilevelExam.feedback")}: {s.feedback}</p>}
      {s.evaluation && <AiEvaluationDetails evaluation={s.evaluation} />}
    </div>
  );
}

function localizedDuration(t: (key: string, vars?: Record<string, string | number>) => string, seconds: number | null | undefined): string {
  if (!seconds) return "—";
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const remainder = minutes % 60;
  return hours ? t("multilevelExam.hoursMinutes", { h: hours, m: remainder }) : t("multilevelExam.minutes", { count: minutes });
}

function AiEvaluationDetails({ evaluation }: { evaluation: AiEvaluationView }) {
  const { t } = useTranslation();
  return (
    <details className="mt-3 rounded-xl bg-surface-hover/50 p-3 ring-1 ring-surface-border" open>
      <summary className="cursor-pointer text-sm font-semibold text-text-primary">{t("multilevelExam.aiEvaluation")}</summary>
      <div className="mt-3 space-y-4 text-sm">
        <p className="text-xs text-text-secondary">
          {t("multilevelExam.rawScore")}: {evaluation.raw} / {evaluation.raw_max}
          {" · "}{t("multilevelExam.convertedScore")}: {evaluation.converted ?? "—"} / 75
        </p>
        {evaluation.conversion_missing && <p className="rounded-lg bg-warning/10 p-2 text-xs text-text-secondary">{t("multilevelExam.conversionMissing")}</p>}
        {evaluation.summary && <p className="whitespace-pre-line text-text-secondary">{evaluation.summary}</p>}
        {evaluation.teile.map((teil) => <AiTeilDetails key={`${teil.teil}-${teil.title}`} teil={teil} />)}
        <EvaluationList label={t("multilevelExam.strengths")} items={evaluation.strengths} />
        <EvaluationList label={t("multilevelExam.mistakes")} items={evaluation.mistakes} />
        <EvaluationList label={t("multilevelExam.recommendations")} items={evaluation.recommendations} />
        <EvaluationList label={t("multilevelExam.limitations")} items={evaluation.limitations} />
      </div>
    </details>
  );
}

function AiTeilDetails({ teil }: { teil: AiTeil }) {
  const { t } = useTranslation();
  return (
    <section className="space-y-2 border-t border-surface-border pt-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="font-semibold text-text-primary">{teil.title || teil.teil}</h3>
        <span className="font-bold text-text-primary">{teil.score} / {teil.max}</span>
      </div>
      {teil.explanation && <p className="whitespace-pre-line text-text-secondary">{teil.explanation}</p>}
      {!!teil.criteria?.length && (
        <ul className="space-y-1.5">
          {teil.criteria.map((criterion, index) => (
            <li key={`${criterion.key ?? criterion.name}-${index}`} className="rounded-lg bg-surface-card p-2">
              <p className="flex flex-wrap justify-between gap-2 font-medium text-text-primary">
                <span>{criterion.name}</span>
                <span>{criterion.score == null ? t("multilevelExam.notAssessed") : `${criterion.score} / ${criterion.max ?? 5}`}</span>
              </p>
              {criterion.comment && <p className="mt-1 text-xs text-text-secondary">{criterion.comment}</p>}
            </li>
          ))}
        </ul>
      )}
      {teil.transcript && <details className="text-xs"><summary className="cursor-pointer font-medium text-text-secondary">{t("multilevelExam.transcript")}</summary>
        <p className="mt-1 whitespace-pre-wrap text-text-secondary">{teil.transcript}</p></details>}
      <EvaluationList label={t("multilevelExam.strengths")} items={teil.strengths} />
      {teil.mistakes?.length ? (
        <div>
          <p className="text-xs font-semibold text-text-secondary">{t("multilevelExam.mistakes")}</p>
          <ul className="mt-1 space-y-1">
            {teil.mistakes.map((mistake, index) => (
              <li key={`${mistake.original}-${index}`} className="text-xs text-text-secondary">
                <p><span className="text-danger">{mistake.original}</span> → <span className="text-success">{mistake.correction}</span></p>
                {mistake.explanation && <p>{mistake.explanation}</p>}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      <EvaluationList label={t("multilevelExam.recommendations")} items={teil.recommendations} />
    </section>
  );
}

function EvaluationList({ label, items }: { label: string; items?: string[] }) {
  if (!items?.length) return null;
  return <div><p className="text-xs font-semibold text-text-secondary">{label}</p><ul className="mt-1 list-inside list-disc space-y-1 text-xs text-text-secondary">
    {items.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
  </ul></div>;
}
