"use client";

import { CheckCircle2, Sparkles, TriangleAlert } from "lucide-react";

import ProgressBar from "@/components/ui/progress-bar";
import { useTranslation } from "@/lib/i18n/use-translation";
import type { Evaluation } from "../types/assessment";

function scoreColor(score: number): string {
  if (score >= 80) return "text-success";
  if (score >= 60) return "text-accent-blue";
  if (score >= 40) return "text-warning";
  return "text-danger";
}

export default function EvaluationResult({ data }: { data: Evaluation }) {
  const { t } = useTranslation();

  return (
    <div className="rounded-card bg-accent-blue/5 p-6 ring-1 ring-accent-blue/15">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-accent-blue to-purple-600 text-white shadow-md">
            <Sparkles size={22} />
          </div>
          <div>
            <h4 className="text-lg font-bold text-text-primary">{t("assessment.title")}</h4>
            <p className="text-sm text-text-secondary">
              {t("assessment.estimatedLevel")}{" "}
              <span className="font-semibold text-accent-blue">{data.level}</span>
            </p>
          </div>
        </div>

        <div className="text-right">
          <p className={`text-4xl font-bold ${scoreColor(data.score)}`}>
            {data.score}
            <span className="text-lg text-text-muted">/100</span>
          </p>
        </div>
      </div>

      {/* Summary */}
      <p className="mt-5 rounded-2xl bg-surface-card p-4 text-sm text-text-secondary shadow-sm">
        {data.summary}
      </p>

      {/* Criteria */}
      {data.criteria.length > 0 && (
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          {data.criteria.map((c) => (
            <div key={c.name} className="rounded-2xl bg-surface-card p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-text-primary">{c.name}</p>
                <span className={`text-sm font-bold ${scoreColor(c.score)}`}>{c.score}</span>
              </div>
              <ProgressBar value={c.score} className="mt-2.5" trackClassName="h-1.5" />
              <p className="mt-2 text-xs text-text-secondary">{c.comment}</p>
            </div>
          ))}
        </div>
      )}

      {/* Corrections */}
      {data.corrections.length > 0 && (
        <div className="mt-5">
          <p className="mb-3 flex items-center gap-2 text-sm font-semibold text-text-primary">
            <TriangleAlert size={16} className="text-warning" />
            {t("assessment.corrections")}
          </p>
          <div className="space-y-2">
            {data.corrections.map((corr, i) => (
              <div key={i} className="rounded-2xl bg-surface-card p-4 text-sm shadow-sm">
                <p className="text-text-muted line-through">{corr.original}</p>
                <p className="mt-1 flex items-center gap-2 font-semibold text-success">
                  <CheckCircle2 size={15} />
                  {corr.suggestion}
                </p>
                <p className="mt-1 text-xs text-text-secondary">{corr.reason}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
