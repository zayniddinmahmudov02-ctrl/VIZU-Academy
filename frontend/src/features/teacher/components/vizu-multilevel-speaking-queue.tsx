"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle2, Mic } from "lucide-react";

import {
  getTeacherVizuMultilevelSpeaking,
  getTeacherVizuMultilevelSpeakingAudioBlobUrl,
  getTeacherVizuMultilevelSpeakingDetail,
  gradeTeacherVizuMultilevelSpeakingTask,
} from "@/features/teacher/services/teacher.service";
import type {
  VizuMultilevelTeacherSpeakingDetail,
  VizuMultilevelTeacherSpeakingListItem,
  VizuMultilevelTeacherSpeakingSubmissionDetail,
} from "@/features/teacher/types";
import { cn } from "@/lib/utils";

const STATUS_LABEL: Record<VizuMultilevelTeacherSpeakingListItem["status"], string> = {
  NEW: "Neu",
  IN_PROGRESS: "In Bewertung",
  GRADED: "Bewertet",
};

/** VIZU-Multilevel Sprechen review. Like the Schreiben review, it is not
 * scoped by course — VIZU-Multilevel has no course concept — so any teacher
 * sees every submitted attempt. Recordings are fetched through an
 * authenticated request and played from a blob URL (never a public URL). */
export default function VizuMultilevelSpeakingQueue() {
  const [activeId, setActiveId] = useState<string | null>(null);

  if (activeId) {
    return <SpeakingDetail attemptId={activeId} onBack={() => setActiveId(null)} />;
  }
  return <SpeakingList onOpen={setActiveId} />;
}

function SpeakingList({ onOpen }: { onOpen: (attemptId: string) => void }) {
  const { data: items, isLoading } = useQuery({
    queryKey: ["teacher-vizu-multilevel-speaking"],
    queryFn: getTeacherVizuMultilevelSpeaking,
  });

  if (isLoading) return <p className="text-sm text-text-secondary">Wird geladen…</p>;

  if (!items || items.length === 0) {
    return (
      <div className="rounded-card bg-surface-card p-8 text-center ring-1 ring-surface-border">
        <Mic size={28} className="mx-auto text-text-muted" />
        <p className="mt-3 text-sm text-text-secondary">Noch keine Sprechen-Einsendungen von VIZU-Multilevel.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <button
          key={item.attempt_id}
          type="button"
          onClick={() => onOpen(item.attempt_id)}
          className="flex w-full flex-wrap items-center justify-between gap-3 rounded-2xl bg-surface-card p-5 text-left shadow-[var(--shadow-sm)] ring-1 ring-surface-border transition-colors hover:bg-surface-hover"
        >
          <div>
            <p className="font-semibold text-text-primary">{item.student_name}</p>
            <p className="text-xs text-text-muted">
              VIZU-Multilevel · {new Date(item.sprechen_submitted_at).toLocaleDateString("de-DE")} · {item.email}
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="text-text-secondary">
              {item.graded_count}/{item.total_submissions} bewertet
            </span>
            <span
              className={cn(
                "rounded-full px-2.5 py-1 font-bold",
                item.status === "GRADED" ? "bg-success/15 text-success" : "bg-warning/15 text-warning",
              )}
            >
              {STATUS_LABEL[item.status]}
            </span>
          </div>
        </button>
      ))}
    </div>
  );
}

function SpeakingDetail({ attemptId, onBack }: { attemptId: string; onBack: () => void }) {
  const queryClient = useQueryClient();
  const { data: detail, isLoading, isError } = useQuery({
    queryKey: ["teacher-vizu-multilevel-speaking-detail", attemptId],
    queryFn: () => getTeacherVizuMultilevelSpeakingDetail(attemptId),
    retry: false,
  });

  function handleGraded(updated: VizuMultilevelTeacherSpeakingDetail) {
    queryClient.setQueryData(["teacher-vizu-multilevel-speaking-detail", attemptId], updated);
    queryClient.invalidateQueries({ queryKey: ["teacher-vizu-multilevel-speaking"] });
  }

  return (
    <div className="space-y-4">
      <button type="button" onClick={onBack} className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary hover:text-accent-blue">
        <ArrowLeft size={16} />
        Zurück
      </button>

      {isLoading && <p className="text-sm text-text-secondary">Wird geladen…</p>}
      {isError && (
        <p className="text-sm text-text-secondary">
          Diese Einsendung ist nicht mehr verfügbar (das Gesamtergebnis wurde möglicherweise bereits abgeschlossen).
        </p>
      )}

      {detail && (
        <>
          <div className="rounded-card bg-surface-card p-5 ring-1 ring-surface-border">
            <p className="font-semibold text-text-primary">{detail.student_name}</p>
            <p className="text-xs text-text-muted">
              {detail.email} · VIZU-Multilevel Sprechen · Punkte: {detail.sprechen_score ?? "—"}
              {detail.sprechen_level ? ` · Niveau ${detail.sprechen_level}` : ""}
            </p>
          </div>

          {detail.submissions.map((submission) => (
            <SubmissionCard key={submission.task_id} attemptId={attemptId} submission={submission} onGraded={handleGraded} />
          ))}
        </>
      )}
    </div>
  );
}

function SubmissionCard({
  attemptId,
  submission,
  onGraded,
}: {
  attemptId: string;
  submission: VizuMultilevelTeacherSpeakingSubmissionDetail;
  onGraded: (updated: VizuMultilevelTeacherSpeakingDetail) => void;
}) {
  const [score, setScore] = useState(submission.teacher_score?.toString() ?? "");
  const [comment, setComment] = useState(submission.teacher_comment ?? "");
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadAudio() {
    if (!submission.submission_id) return;
    try {
      setAudioUrl(await getTeacherVizuMultilevelSpeakingAudioBlobUrl(attemptId, submission.submission_id));
    } catch {
      setError("Aufnahme konnte nicht geladen werden.");
    }
  }

  async function save() {
    const value = Number(score);
    if (score.trim() === "" || Number.isNaN(value) || value < 0 || value > submission.points) {
      setError(`Bewertung muss zwischen 0 und ${submission.points} liegen.`);
      return;
    }
    setError(null);
    setSaving(true);
    try {
      onGraded(await gradeTeacherVizuMultilevelSpeakingTask(attemptId, submission.task_id, { score: value, comment: comment || null }));
    } catch {
      setError("Speichern fehlgeschlagen.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4 rounded-card bg-surface-card p-5 ring-1 ring-surface-border">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
          Aufgabe {submission.order_index} · Niveau {submission.level} · max. {submission.points} Punkte
        </p>
        <h3 className="mt-1 text-base font-bold text-text-primary">{submission.title}</h3>
        <p className="mt-1 whitespace-pre-line text-sm text-text-secondary">{submission.instruction}</p>
      </div>

      {!submission.has_audio ? (
        <p className="text-sm text-text-muted">Der Student hat zu dieser Aufgabe keine Aufnahme abgegeben (0 Punkte).</p>
      ) : (
        <>
          <div className="rounded-xl bg-surface-hover p-4">
            {audioUrl ? (
              <audio controls src={audioUrl} className="w-full" />
            ) : (
              <button
                type="button"
                onClick={loadAudio}
                className="inline-flex items-center gap-2 text-sm font-semibold text-accent-blue hover:underline"
              >
                <Mic size={15} />
                Aufnahme laden{submission.duration_seconds ? ` (${submission.duration_seconds}s)` : ""}
              </button>
            )}
          </div>

          <div className="grid gap-3 sm:grid-cols-[140px_1fr]">
            <label className="block text-xs font-semibold text-text-secondary">
              Punkte (0–{submission.points})
              <input
                type="number"
                min={0}
                max={submission.points}
                value={score}
                onChange={(e) => setScore(e.target.value)}
                className="mt-1 w-full rounded-lg bg-surface-hover px-3 py-2 text-sm text-text-primary ring-1 ring-surface-border"
              />
            </label>
            <label className="block text-xs font-semibold text-text-secondary">
              Kommentar
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                rows={2}
                className="mt-1 w-full rounded-lg bg-surface-hover px-3 py-2 text-sm text-text-primary ring-1 ring-surface-border"
              />
            </label>
          </div>

          {error && <p className="text-sm text-danger">{error}</p>}

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={save}
              disabled={saving}
              className="rounded-lg bg-accent-blue px-4 py-2 text-sm font-bold text-white disabled:opacity-50"
            >
              {saving ? "Wird gespeichert…" : "Bewertung speichern"}
            </button>
            {submission.teacher_score !== null && (
              <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-success">
                <CheckCircle2 size={14} />
                Bewertet: {submission.teacher_score}/{submission.points}
              </span>
            )}
          </div>
        </>
      )}
    </div>
  );
}
