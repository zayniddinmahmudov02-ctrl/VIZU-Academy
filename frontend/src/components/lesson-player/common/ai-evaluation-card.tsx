"use client";

import { AlertTriangle, CheckCircle2, Lightbulb, Loader2, RefreshCw, Sparkles } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

export interface AiCriterion {
  key: string;
  name: string;
  max: number;
  score: number | null;
  status: "assessed" | "not_assessed";
  comment: string;
}

export interface AiEvaluationResult {
  criteria?: AiCriterion[];
  score?: number;
  strengths?: string[];
  errors?: { original: string; correction: string; explanation: string }[];
  recommendation?: string;
  summary?: string;
  limitations?: string[];
  transcript?: string;
}

interface Props {
  status: string;
  score: number | null;
  aiScore: number | null;
  evaluation: AiEvaluationResult | null;
  onRetry?: () => void;
  retrying?: boolean;
  showTranscript?: boolean;
}

/** Status + result of the AI evaluation of a Schreiben / Sprechen
 * submission. Scores come from the server only (never computed here). */
export default function AiEvaluationCard({ status, score, aiScore, evaluation, onRetry, retrying, showTranscript }: Props) {
  const { t } = useTranslation();

  if (status === "SUBMITTED" || status === "EVALUATING") {
    return (
      <div className="flex items-center gap-2 rounded-xl bg-accent-blue/10 px-4 py-3 text-sm font-semibold text-accent-blue" role="status" data-testid="ai-pending">
        <Loader2 size={16} className="animate-spin" />
        {t("lessons.aiPending")}
      </div>
    );
  }

  if (status === "EVALUATION_FAILED") {
    return (
      <div className="space-y-2 rounded-xl bg-warning/10 px-4 py-3 text-sm text-warning" role="alert" data-testid="ai-failed">
        <p className="flex items-center gap-2 font-semibold">
          <AlertTriangle size={16} />
          {t("lessons.aiFailed")}
        </p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            disabled={retrying}
            className="inline-flex min-h-10 items-center gap-1.5 rounded-lg bg-warning px-3 text-xs font-bold text-white disabled:opacity-60"
            data-testid="ai-retry"
          >
            <RefreshCw size={13} className={retrying ? "animate-spin" : ""} />
            {t("lessons.aiRetry")}
          </button>
        )}
      </div>
    );
  }

  if (status !== "GRADED" || !evaluation?.criteria) return null;

  return (
    <div className="space-y-4 rounded-2xl bg-surface-card p-4 ring-1 ring-surface-border sm:p-5" data-testid="ai-result">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="flex items-center gap-2 text-base font-bold text-text-primary">
          <Sparkles size={17} className="text-accent-blue" />
          {t("lessons.aiTotal", { score: score ?? 0 })}
        </p>
        {aiScore !== null && score !== null && aiScore !== score && (
          <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-800">{t("lessons.aiAdjusted")}</span>
        )}
      </div>
      {evaluation.summary && <p className="text-sm text-text-secondary">{evaluation.summary}</p>}

      <div>
        <p className="mb-2 text-xs font-bold uppercase tracking-wide text-text-muted">{t("lessons.aiCriteria")}</p>
        <ul className="space-y-2">
          {evaluation.criteria.map((c) => (
            <li key={c.key} className="rounded-xl bg-surface-hover/60 px-3 py-2.5">
              <div className="flex items-center justify-between gap-3 text-sm">
                <span className="font-semibold text-text-primary">{c.name}</span>
                <span className="shrink-0 font-bold tabular-nums text-text-primary">
                  {c.status === "assessed" ? `${c.score} / ${c.max}` : t("lessons.aiNotAssessed")}
                </span>
              </div>
              {c.status === "assessed" && (
                <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-surface-border">
                  <div className="h-full rounded-full bg-accent-blue" style={{ width: `${((c.score ?? 0) / c.max) * 100}%` }} />
                </div>
              )}
              {c.comment && <p className="mt-1.5 text-xs text-text-secondary">{c.comment}</p>}
            </li>
          ))}
        </ul>
      </div>

      {!!evaluation.strengths?.length && (
        <div>
          <p className="mb-1.5 text-xs font-bold uppercase tracking-wide text-text-muted">{t("lessons.aiStrengths")}</p>
          <ul className="space-y-1">
            {evaluation.strengths.map((s, i) => (
              <li key={i} className="flex gap-2 text-sm text-text-secondary">
                <CheckCircle2 size={15} className="mt-0.5 shrink-0 text-success" />
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}

      {!!evaluation.errors?.length && (
        <div>
          <p className="mb-1.5 text-xs font-bold uppercase tracking-wide text-text-muted">{t("lessons.aiErrors")}</p>
          <ul className="space-y-2">
            {evaluation.errors.map((e, i) => (
              <li key={i} className="rounded-xl bg-surface-hover/60 px-3 py-2 text-sm">
                <span className="text-danger line-through">{e.original}</span>
                {" → "}
                <span className="font-semibold text-success">{e.correction}</span>
                {e.explanation && <p className="mt-1 text-xs text-text-secondary">{e.explanation}</p>}
              </li>
            ))}
          </ul>
        </div>
      )}

      {evaluation.recommendation && (
        <div className="flex gap-2 rounded-xl bg-accent-blue/5 px-3 py-2.5 text-sm text-text-primary ring-1 ring-accent-blue/15">
          <Lightbulb size={16} className="mt-0.5 shrink-0 text-accent-blue" />
          <div>
            <p className="text-xs font-bold uppercase tracking-wide text-accent-blue">{t("lessons.aiRecommendation")}</p>
            <p className="mt-0.5">{evaluation.recommendation}</p>
          </div>
        </div>
      )}

      {!!evaluation.limitations?.length && (
        <ul className="space-y-1 text-xs text-text-muted">
          {evaluation.limitations.map((l, i) => (
            <li key={i}>ⓘ {l}</li>
          ))}
        </ul>
      )}

      {showTranscript && evaluation.transcript && (
        <details className="rounded-xl bg-surface-hover/60 px-3 py-2 text-sm">
          <summary className="cursor-pointer font-semibold text-text-primary">{t("lessons.aiTranscript")}</summary>
          <p className="mt-1.5 whitespace-pre-line text-text-secondary">{evaluation.transcript}</p>
        </details>
      )}
    </div>
  );
}
