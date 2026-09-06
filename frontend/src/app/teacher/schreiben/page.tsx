"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, PenLine, Sparkles } from "lucide-react";

import PageHeader from "@/components/dashboard/page-header";
import {
  listPendingWritingReviews,
  reviewWritingSubmission,
} from "@/features/admin/services/assessment-service";
import type { PendingWritingReviewItem } from "@/features/admin/types/assessment.types";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

const TABS = [
  { key: "ALLE", label: "Alle" },
  { key: "NEU", label: "Neu" },
  { key: "IN_PRUEFUNG", label: "In Prüfung" },
  { key: "BEWERTET", label: "Bewertet" },
  { key: "ZURUECKGEGEBEN", label: "Zurückgegeben" },
] as const;

/** Real Schreiben submissions (WritingSubmission — Assessment Engine),
 * scoped server-side to this teacher's TeacherAssignment courses
 * (backend/app/services/teacher/scope.py, wired into
 * writing_service.list_pending_reviews) — the exact same endpoint the
 * Admin "Hausaufgaben" queue already calls, just automatically filtered
 * down when the caller's role is TEACHER instead of an admin role. No
 * fake data, no parallel grading engine — same rubric-score-based review
 * as Admin, same AI pre-evaluation surfaced as a suggestion. */
export default function TeacherSchreibenPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<(typeof TABS)[number]["key"]>("ALLE");
  const [active, setActive] = useState<PendingWritingReviewItem | null>(null);

  const { data: items, isLoading } = useQuery({
    queryKey: ["teacher-schreiben", tab],
    queryFn: () => listPendingWritingReviews(undefined, tab),
  });

  function handleReviewed() {
    setActive(null);
    queryClient.invalidateQueries({ queryKey: ["teacher-schreiben"] });
  }

  return (
    <div className="space-y-6">
      <PageHeader icon={PenLine} titleKey="teacher.navSchreiben" gradient="from-accent-blue to-purple-600" />

      <div className="flex gap-1.5 overflow-x-auto rounded-xl bg-surface-hover p-1 ring-1 ring-surface-border">
        {TABS.map((tb) => (
          <button
            key={tb.key}
            onClick={() => {
              setTab(tb.key);
              setActive(null);
            }}
            className={cn(
              "min-h-11 flex-1 shrink-0 whitespace-nowrap rounded-lg px-3 py-2 text-xs font-semibold transition-colors",
              tab === tb.key ? "bg-accent-blue text-white" : "text-text-secondary hover:bg-surface-card",
            )}
          >
            {tb.label}
          </button>
        ))}
      </div>

      {isLoading && <p className="text-sm text-text-muted">{t("common.loading")}</p>}

      {!isLoading && (items?.length ?? 0) === 0 && (
        <div className="rounded-card bg-surface-card p-10 text-center shadow-[var(--shadow-md)] ring-1 ring-surface-border">
          <PenLine className="mx-auto mb-2 text-text-muted" size={22} />
          <p className="text-sm text-text-muted">Keine Abgaben vorhanden.</p>
        </div>
      )}

      {!isLoading && (items?.length ?? 0) > 0 && (
        <div className="grid gap-4 lg:grid-cols-[380px_1fr]">
          <div className="space-y-2">
            {items!.map((item) => (
              <button
                key={item.submission.id}
                onClick={() => setActive(item)}
                className={cn(
                  "w-full rounded-2xl p-4 text-left ring-1 transition-colors",
                  active?.submission.id === item.submission.id
                    ? "bg-accent-blue/10 ring-accent-blue/30"
                    : "bg-surface-card ring-surface-border hover:bg-surface-hover",
                )}
              >
                <p className="text-sm font-bold text-text-primary">{item.student_name}</p>
                <p className="mt-0.5 text-xs text-text-muted">
                  {item.lesson_title || "—"} · {item.level}
                </p>
              </button>
            ))}
          </div>

          <div>
            {active ? (
              <WritingReviewCard item={active} tab={tab} onReviewed={handleReviewed} />
            ) : (
              <div className="flex h-full min-h-[200px] items-center justify-center rounded-card bg-surface-card text-sm text-text-muted ring-1 ring-surface-border">
                Wähle eine Abgabe aus der Liste.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function WritingReviewCard({
  item,
  tab,
  onReviewed,
}: {
  item: PendingWritingReviewItem;
  tab: string;
  onReviewed: () => void;
}) {
  const ai = item.ai_evaluation;
  const [scores, setScores] = useState<Record<string, number>>(() =>
    Object.fromEntries(item.rubric_criteria.map((c) => [c.id, ai?.rubric_scores[c.id] ?? 0])),
  );
  const [feedback, setFeedback] = useState(ai?.feedback ?? "");
  const [saving, setSaving] = useState(false);
  const alreadyGraded = tab === "BEWERTET" || tab === "ZURUECKGEGEBEN" || item.submission.status === "GRADED";

  async function handleSubmit() {
    setSaving(true);
    try {
      await reviewWritingSubmission(item.submission.id, { rubric_scores: scores, feedback });
      onReviewed();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4 rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
      <div>
        <h3 className="text-base font-bold text-text-primary">{item.task_title}</h3>
        <p className="text-xs text-text-muted">
          {item.student_name} · {item.lesson_title} ({item.level})
        </p>
      </div>

      <div className="rounded-xl bg-surface-hover p-4 text-sm text-text-secondary">{item.submission.content}</div>
      <p className="text-xs text-text-muted">
        {item.submission.word_count} Wörter · {item.submission.character_count} Zeichen
      </p>

      {ai && (
        <div className="rounded-xl bg-accent-blue/5 p-4 ring-1 ring-accent-blue/20">
          <p className="flex items-center gap-1.5 text-xs font-semibold text-accent-blue">
            <Sparkles size={12} /> KI-Bewertung{alreadyGraded ? "" : " (Vorschlag)"}
          </p>
          {ai.feedback && <p className="mt-1 whitespace-pre-line text-xs text-text-secondary">{ai.feedback}</p>}
        </div>
      )}

      {alreadyGraded ? (
        <div className="rounded-xl bg-surface-hover p-4 ring-1 ring-surface-border">
          <p className="text-sm font-semibold text-text-primary">
            {item.submission.final_score} / {item.rubric_criteria.reduce((s, c) => s + c.max_score, 0)} Punkte
          </p>
        </div>
      ) : (
        <>
          <div className="space-y-2">
            <p className="text-xs font-medium text-text-secondary">Kriterien-Punktzahl</p>
            {item.rubric_criteria.map((c) => (
              <div key={c.id} className="flex items-center gap-2">
                <span className="flex-1 text-xs text-text-secondary">{c.name}</span>
                <input
                  type="number"
                  min={0}
                  max={c.max_score}
                  value={scores[c.id] ?? 0}
                  onChange={(e) => setScores((prev) => ({ ...prev, [c.id]: Number(e.target.value) }))}
                  className="h-9 w-16 rounded-md bg-surface-hover px-2 text-xs text-text-primary ring-1 ring-surface-border outline-none focus:ring-accent-blue"
                />
                <span className="w-10 text-xs text-text-muted">/ {c.max_score}</span>
              </div>
            ))}
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-text-secondary">Feedback</label>
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              rows={4}
              className="w-full rounded-xl bg-surface-hover p-3 text-sm text-text-primary ring-1 ring-surface-border outline-none focus:ring-accent-blue"
            />
          </div>

          <button
            onClick={handleSubmit}
            disabled={saving}
            className="flex min-h-11 items-center gap-1.5 rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-60"
          >
            <CheckCircle2 size={15} />
            {saving ? "Wird gespeichert..." : "Bewertung bestätigen"}
          </button>
        </>
      )}
    </div>
  );
}
