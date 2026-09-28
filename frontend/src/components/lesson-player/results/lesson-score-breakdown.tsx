"use client";

import { CheckCircle2, Clock, TriangleAlert } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

export interface ScoreComponentShape {
  label: string;
  points: number;
  max_points: number;
  /** "pending": a Schreiben/Sprechen submission a teacher hasn't graded
   * yet — shown as "not yet graded", never as a silent 0. */
  status?: "final" | "pending";
}

export interface LessonScoreShape {
  total_score: number;
  max_score: number;
  breakdown: Record<string, ScoreComponentShape>;
  feedback: string;
  strengths: string[];
  weak_areas: string[];
}

const LABEL_KEYS: Record<string, string> = {
  video: "lessons.sectionVideo",
  lesen: "lessons.sectionReading",
  hoeren: "lessons.sectionListening",
  schreiben: "lessons.sectionWriting",
  sprechen: "lessons.sectionSpeaking",
  wortschatz: "lessons.sectionVocabularyQuiz",
  yakuniy_test: "lessons.sectionLessonQuiz",
};

/** Pure display component — shared by the student's own result card
 * (lesson-player/results/result-section.tsx) and the admin's per-student
 * lesson score view, so the breakdown/feedback/weak-areas presentation
 * never drifts between the two. */
export default function LessonScoreBreakdown({ score }: { score: LessonScoreShape }) {
  const { t } = useTranslation();
  const labelFor = (key: string) => (LABEL_KEYS[key] ? t(LABEL_KEYS[key]) : (score.breakdown[key]?.label ?? key));
  const percent = score.max_score > 0 ? Math.round((score.total_score / score.max_score) * 100) : 0;

  return (
    <div className="space-y-5">
      <div className="rounded-2xl bg-surface-card p-6 text-center ring-1 ring-surface-border">
        <p className="text-sm font-medium text-text-secondary">Fortschritt</p>
        <p className="mt-1 text-4xl font-extrabold text-text-primary">{percent}%</p>
        <p className="mt-1 text-sm text-text-secondary">
          Punktzahl: {score.total_score} / {score.max_score}
        </p>
      </div>

      <div className="overflow-hidden rounded-2xl ring-1 ring-surface-border">
        <table className="w-full text-left text-sm">
          <tbody className="divide-y divide-surface-border">
            {Object.entries(score.breakdown).map(([key, item]) => (
              <tr key={key} className="bg-surface-card">
                <td className="px-4 py-2.5 font-medium text-text-primary">{labelFor(key)}</td>
                <td className="px-4 py-2.5 text-right text-text-secondary">
                  {item.status === "pending" ? (
                    <span className="inline-flex items-center gap-1.5 text-warning">
                      <Clock size={13} />
                      {t("lessons.notYetGraded")} (/{item.max_points})
                    </span>
                  ) : (
                    <>
                      {item.points}/{item.max_points}
                    </>
                  )}
                </td>
              </tr>
            ))}
            <tr className="bg-surface-hover/60">
              <td className="px-4 py-2.5 font-bold text-text-primary">Gesamt</td>
              <td className="px-4 py-2.5 text-right font-bold text-text-primary">
                {score.total_score}/{score.max_score}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="rounded-2xl bg-accent-blue/5 p-5 ring-1 ring-accent-blue/20">
        <p className="text-sm font-semibold text-text-primary">Feedback</p>
        <p className="mt-1 text-sm text-text-secondary">{score.feedback}</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="rounded-2xl bg-success/5 p-4 ring-1 ring-success/20">
          <p className="mb-2 text-sm font-semibold text-success">Stärken</p>
          {score.strengths.length === 0 ? (
            <p className="text-xs text-text-muted">—</p>
          ) : (
            <ul className="space-y-1">
              {score.strengths.map((key) => (
                <li key={key} className="flex items-center gap-1.5 text-sm text-text-secondary">
                  <CheckCircle2 size={14} className="text-success" />
                  {labelFor(key)}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="rounded-2xl bg-warning/5 p-4 ring-1 ring-warning/20">
          <p className="mb-2 text-sm font-semibold text-warning">Noch üben</p>
          {score.weak_areas.length === 0 ? (
            <p className="text-xs text-text-muted">—</p>
          ) : (
            <ul className="space-y-1">
              {score.weak_areas.map((key) => (
                <li key={key} className="flex items-center gap-1.5 text-sm text-text-secondary">
                  <TriangleAlert size={14} className="text-warning" />
                  {labelFor(key)}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
