"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Mic, Pause, Play, Save } from "lucide-react";

import { AdminButton, AdminCard, AdminPageHeader, AdminTextarea } from "@/components/admin/admin-ui";
import {
  getSpeakingAudioBlobUrl,
  listPendingSpeakingReviews,
  reviewSpeakingSubmission,
} from "@/features/admin/services/assessment-service";
import type { PendingSpeakingReviewItem } from "@/features/admin/types/assessment.types";

/** The teacher review queue for Sprechen submissions — same route
 * pattern as /admin/writing-review (real route, not a 13th sidebar item;
 * the CMS sidebar is locked to exactly 12 top-level sections). Teacher
 * listens to the recording, scores the (admin-defined, never hardcoded)
 * rubric, and either saves progress (REVIEWED) or finalizes (FINAL,
 * which folds the score into the attempt's total). */
export default function SpeakingReviewPage() {
  const queryClient = useQueryClient();
  const [activeId, setActiveId] = useState<string | null>(null);

  const { data: items, isLoading } = useQuery({
    queryKey: ["pending-speaking-reviews"],
    queryFn: () => listPendingSpeakingReviews(),
  });

  const activeItem = items?.find((i) => i.submission.id === activeId) ?? null;

  function handleReviewed() {
    queryClient.invalidateQueries({ queryKey: ["pending-speaking-reviews"] });
  }

  return (
    <div>
      <AdminPageHeader
        title="Sprechen — Bewertung"
        description="Audioeinreichungen, die auf eine Lehrerbewertung warten."
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
                <Mic size={13} />
                {item.task_title}
              </p>
              <p className="mt-0.5 text-xs text-[var(--admin-text-muted)]">{item.student_name}</p>
              <p className="mt-1 text-xs text-[var(--admin-text-muted)]">
                {item.submission.status === "REVIEWED" ? "Teilweise bewertet" : "Neu"}
              </p>
            </button>
          ))}
        </div>

        <div>{activeItem && <ReviewForm key={activeItem.submission.id} item={activeItem} onReviewed={handleReviewed} />}</div>
      </div>
    </div>
  );
}

function ReviewForm({ item, onReviewed }: { item: PendingSpeakingReviewItem; onReviewed: () => void }) {
  const [scores, setScores] = useState<Record<string, number>>(() =>
    Object.fromEntries(item.rubric_criteria.map((c) => [c.id, 0])),
  );
  const [feedback, setFeedback] = useState("");
  const [saving, setSaving] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);

  async function togglePlay() {
    const audio = document.getElementById("speaking-review-audio") as HTMLAudioElement | null;
    if (!audio) return;
    if (playing) {
      audio.pause();
      setPlaying(false);
      return;
    }
    if (!audioUrl) {
      const url = await getSpeakingAudioBlobUrl(item.submission.id);
      setAudioUrl(url);
      requestAnimationFrame(() => audio.play());
    } else {
      audio.play();
    }
    setPlaying(true);
  }

  async function handleSave(finalize: boolean) {
    setSaving(true);
    try {
      await reviewSpeakingSubmission(item.submission.id, { rubric_scores: scores, feedback, finalize });
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

        <div className="flex items-center gap-3 rounded-xl bg-white/[0.02] p-4 ring-1 ring-[var(--admin-border)]">
          <button
            onClick={togglePlay}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--admin-primary)] text-white"
            aria-label={playing ? "Pause" : "Abspielen"}
          >
            {playing ? <Pause size={16} /> : <Play size={16} />}
          </button>
          <span className="text-xs text-[var(--admin-text-secondary)]">
            {item.submission.duration_seconds != null ? `${item.submission.duration_seconds}s` : "Aufnahme"}
          </span>
          {audioUrl && (
            <audio id="speaking-review-audio" src={audioUrl} onEnded={() => setPlaying(false)} className="hidden" />
          )}
        </div>

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

        <div className="flex gap-2">
          <AdminButton variant="secondary" onClick={() => handleSave(false)} disabled={saving}>
            <Save size={14} />
            Fortschritt speichern
          </AdminButton>
          <AdminButton onClick={() => handleSave(true)} disabled={saving}>
            <CheckCircle2 size={14} />
            {saving ? "Wird gespeichert..." : "Bewertung finalisieren"}
          </AdminButton>
        </div>
      </div>
    </AdminCard>
  );
}
