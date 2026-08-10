"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, PenLine, Sparkles } from "lucide-react";

import { AdminButton, AdminCard, AdminPageHeader, AdminTextarea } from "@/components/admin/admin-ui";
import { listPendingWritingReviews, reviewWritingSubmission } from "@/features/admin/services/assessment-service";
import type { PendingWritingReviewItem } from "@/features/admin/types/assessment.types";

/** The teacher review queue for AI_AND_TEACHER / TEACHER_ONLY writing
 * tasks — not a 13th sidebar item (the CMS is locked to exactly 12
 * top-level sections), but a real, working, directly-reachable route at
 * /admin/writing-review, same pattern as /admin/lessons/[lessonId] not
 * being in the sidebar either. Shows the AI's preliminary score/feedback
 * (when there is one) plus the student's text; the teacher's score is
 * what actually finalizes the submission — never the AI's alone. */
export default function WritingReviewPage() {
  const queryClient = useQueryClient();
  const [activeId, setActiveId] = useState<string | null>(null);

  const { data: items, isLoading } = useQuery({
    queryKey: ["pending-writing-reviews"],
    queryFn: () => listPendingWritingReviews(),
  });

  const activeItem = items?.find((i) => i.submission.id === activeId) ?? null;

  function handleReviewed() {
    setActiveId(null);
    queryClient.invalidateQueries({ queryKey: ["pending-writing-reviews"] });
  }

  return (
    <div>
      <AdminPageHeader
        title="Schreiben — Bewertung"
        description="Einreichungen, die auf eine Lehrerbewertung warten (AI_AND_TEACHER / TEACHER_ONLY)."
      />

      {isLoading && <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>}

      {!isLoading && (items?.length ?? 0) === 0 && (
        <AdminCard>
          <p className="p-6 text-center text-sm text-[var(--admin-text-muted)]">
            Keine Einreichungen zur Bewertung.
          </p>
        </AdminCard>
      )}

      <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
        <div className="space-y-2">
          {items?.map((item) => (
            <button
              key={item.submission.id}
              onClick={() => setActiveId(item.submission.id)}
              className={`block w-full rounded-xl p-3 text-left ring-1 transition ${
                activeId === item.submission.id
                  ? "bg-[var(--admin-primary)]/10 ring-[var(--admin-primary)]"
                  : "bg-[var(--admin-card)] ring-[var(--admin-border)] hover:ring-[var(--admin-border-strong)]"
              }`}
            >
              <p className="flex items-center gap-1.5 text-sm font-medium text-[var(--admin-text-primary)]">
                <PenLine size={13} />
                {item.task_title}
              </p>
              <p className="mt-0.5 text-xs text-[var(--admin-text-muted)]">{item.student_name}</p>
              {item.ai_evaluation && (
                <p className="mt-1 flex items-center gap-1 text-xs text-[var(--admin-accent)]">
                  <Sparkles size={11} /> KI-Vorschlag: {item.ai_evaluation.total_score} Pkt.
                </p>
              )}
            </button>
          ))}
        </div>

        <div>{activeItem && <ReviewForm item={activeItem} onReviewed={handleReviewed} />}</div>
      </div>
    </div>
  );
}

function ReviewForm({ item, onReviewed }: { item: PendingWritingReviewItem; onReviewed: () => void }) {
  const ai = item.ai_evaluation;
  const [scores, setScores] = useState<Record<string, number>>(() =>
    Object.fromEntries(item.rubric_criteria.map((c) => [c.id, ai?.rubric_scores[c.id] ?? 0])),
  );
  const [feedback, setFeedback] = useState(ai?.feedback ?? "");
  const [saving, setSaving] = useState(false);

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
    <AdminCard>
      <div className="space-y-4 p-5">
        <div>
          <h3 className="text-sm font-semibold text-[var(--admin-text-primary)]">{item.task_title}</h3>
          <p className="text-xs text-[var(--admin-text-muted)]">{item.student_name}</p>
        </div>

        <div className="rounded-xl bg-white/[0.02] p-4 text-sm text-[var(--admin-text-secondary)] ring-1 ring-[var(--admin-border)]">
          {item.submission.content}
        </div>
        <p className="text-xs text-[var(--admin-text-muted)]">
          {item.submission.word_count} Wörter · {item.submission.character_count} Zeichen
        </p>

        {ai && (
          <div className="rounded-xl bg-[var(--admin-accent)]/5 p-4 ring-1 ring-[var(--admin-accent)]/20">
            <p className="flex items-center gap-1.5 text-xs font-semibold text-[var(--admin-accent)]">
              <Sparkles size={12} /> KI-Bewertung (Vorschlag)
            </p>
            {ai.strengths && <p className="mt-2 text-xs text-[var(--admin-text-secondary)]">{ai.strengths}</p>}
            {ai.feedback && <p className="mt-1 whitespace-pre-line text-xs text-[var(--admin-text-secondary)]">{ai.feedback}</p>}
          </div>
        )}

        <div>
          <p className="mb-2 text-xs font-medium text-[var(--admin-text-secondary)]">Kriterien-Punktzahl</p>
          <div className="space-y-2">
            {item.rubric_criteria.length === 0 && (
              <p className="text-xs text-[var(--admin-text-muted)]">Für diese Aufgabe wurde kein Bewertungsraster angelegt.</p>
            )}
            {item.rubric_criteria.map((criterion) => (
              <div key={criterion.id} className="flex items-center gap-2">
                <span className="flex-1 text-xs text-[var(--admin-text-secondary)]">{criterion.name}</span>
                <input
                  type="number"
                  min={0}
                  max={criterion.max_score}
                  value={scores[criterion.id] ?? 0}
                  onChange={(e) => setScores((prev) => ({ ...prev, [criterion.id]: Number(e.target.value) }))}
                  className="h-8 w-16 rounded-md bg-white/[0.03] px-2 text-xs text-[var(--admin-text-primary)] ring-1 ring-[var(--admin-border)] outline-none focus:ring-[var(--admin-primary)]"
                />
                <span className="w-10 text-xs text-[var(--admin-text-muted)]">/ {criterion.max_score}</span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">Feedback</label>
          <AdminTextarea value={feedback} onChange={(e) => setFeedback(e.target.value)} rows={4} />
        </div>

        <AdminButton onClick={handleSubmit} disabled={saving}>
          <CheckCircle2 size={14} />
          {saving ? "Wird gespeichert..." : "Bewertung bestätigen"}
        </AdminButton>
      </div>
    </AdminCard>
  );
}
