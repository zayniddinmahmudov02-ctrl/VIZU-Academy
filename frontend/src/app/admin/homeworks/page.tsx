"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, ClipboardList, Mic, Pause, PenLine, Play, Save, Sparkles } from "lucide-react";

import { AdminButton, AdminCard, AdminPageHeader, AdminTextarea } from "@/components/admin/admin-ui";
import {
  getSpeakingAudioBlobUrl,
  listPendingSpeakingReviews,
  listPendingWritingReviews,
  reviewSpeakingSubmission,
  reviewSpeakingSubmissionWithAudio,
  reviewWritingSubmission,
} from "@/features/admin/services/assessment-service";
import type { PendingSpeakingReviewItem, PendingWritingReviewItem } from "@/features/admin/types/assessment.types";

const TABS = [
  { key: "NEU", label: "Neu" },
  { key: "IN_PRUEFUNG", label: "In Prüfung" },
  { key: "BEWERTET", label: "Bewertet" },
  { key: "ZURUECKGEGEBEN", label: "Zurückgegeben" },
] as const;

type BucketKey = (typeof TABS)[number]["key"];

type HomeworkItem =
  | { skill: "SCHREIBEN"; id: string; data: PendingWritingReviewItem }
  | { skill: "SPRECHEN"; id: string; data: PendingSpeakingReviewItem };

const STATUS_LABEL: Record<string, string> = {
  DRAFT: "Entwurf",
  SUBMITTED: "Eingereicht",
  PENDING_REVIEW: "Zur Prüfung",
  GRADED: "Bewertet",
  REVIEWED: "Teilweise bewertet",
  FINAL: "Bewertet",
};

/** One consolidated Hausaufgaben queue across both Schreiben (mostly
 * auto-evaluated, see writing_service._run_ai_evaluation) and Sprechen
 * (always teacher-graded) submissions — reuses the exact same
 * Assessment Engine review endpoints as the standalone writing-review/
 * speaking-review pages, just merged into one list and bucketed into 4
 * tabs server-side (see writing_service.py / speaking_service.py
 * list_pending_reviews' `bucket` param). No second grading engine. */
export default function HomeworksPage() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<BucketKey>("NEU");
  const [activeItem, setActiveItem] = useState<HomeworkItem | null>(null);

  const { data: writingItems, isLoading: writingLoading } = useQuery({
    queryKey: ["homeworks-writing", tab],
    queryFn: () => listPendingWritingReviews(undefined, tab),
  });

  const { data: speakingItems, isLoading: speakingLoading } = useQuery({
    queryKey: ["homeworks-speaking", tab],
    queryFn: () => listPendingSpeakingReviews(undefined, tab),
  });

  const isLoading = writingLoading || speakingLoading;

  const items: HomeworkItem[] = [
    ...(writingItems ?? []).map((data): HomeworkItem => ({ skill: "SCHREIBEN", id: data.submission.id, data })),
    ...(speakingItems ?? []).map((data): HomeworkItem => ({ skill: "SPRECHEN", id: data.submission.id, data })),
  ].sort((a, b) => (a.data.submission.submitted_at ?? "").localeCompare(b.data.submission.submitted_at ?? ""));

  function handleReviewed() {
    setActiveItem(null);
    queryClient.invalidateQueries({ queryKey: ["homeworks-writing"] });
    queryClient.invalidateQueries({ queryKey: ["homeworks-speaking"] });
  }

  return (
    <div>
      <AdminPageHeader
        title="Hausaufgaben"
        description="Zentrale Hausaufgabenverwaltung über alle Kurse hinweg — Schreiben und Sprechen in einer Warteschlange."
      />

      <div className="mb-4 flex gap-1.5 rounded-xl bg-white/[0.02] p-1 ring-1 ring-[var(--admin-border)]">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => {
              setTab(t.key);
              setActiveItem(null);
            }}
            className={`flex-1 rounded-lg px-3 py-2 text-xs font-semibold transition ${
              tab === t.key
                ? "bg-[var(--admin-primary)] text-white"
                : "text-[var(--admin-text-secondary)] hover:bg-white/5"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {isLoading && <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>}

      {!isLoading && items.length === 0 && (
        <AdminCard>
          <div className="flex flex-col items-center gap-2 p-10 text-center">
            <ClipboardList size={22} className="text-[var(--admin-text-muted)]" />
            <p className="text-sm text-[var(--admin-text-muted)]">Keine Einreichungen in dieser Kategorie.</p>
          </div>
        </AdminCard>
      )}

      {!isLoading && items.length > 0 && (
        <div className="grid gap-4 lg:grid-cols-[420px_1fr]">
          <AdminCard>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[var(--admin-border)] text-[var(--admin-text-muted)]">
                    <th className="px-3 py-2 font-medium">Schüler</th>
                    <th className="px-3 py-2 font-medium">Lektion</th>
                    <th className="px-3 py-2 font-medium">Typ</th>
                    <th className="px-3 py-2 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr
                      key={`${item.skill}-${item.id}`}
                      onClick={() => setActiveItem(item)}
                      className={`cursor-pointer border-b border-[var(--admin-border)] transition last:border-0 ${
                        activeItem?.id === item.id
                          ? "bg-[var(--admin-primary)]/10"
                          : "hover:bg-white/[0.03]"
                      }`}
                    >
                      <td className="px-3 py-2.5 text-[var(--admin-text-primary)]">{item.data.student_name}</td>
                      <td className="px-3 py-2.5 text-[var(--admin-text-secondary)]">
                        {item.data.lesson_title || "—"}
                        <span className="ml-1 text-[10px] text-[var(--admin-text-muted)]">{item.data.level}</span>
                      </td>
                      <td className="px-3 py-2.5 text-[var(--admin-text-secondary)]">
                        <span className="inline-flex items-center gap-1">
                          {item.skill === "SCHREIBEN" ? <PenLine size={11} /> : <Mic size={11} />}
                          {item.skill === "SCHREIBEN" ? "Schreiben" : "Sprechen"}
                        </span>
                      </td>
                      <td className="px-3 py-2.5 text-[var(--admin-text-muted)]">
                        {STATUS_LABEL[item.data.submission.status] ?? item.data.submission.status}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </AdminCard>

          <div>
            {activeItem?.skill === "SCHREIBEN" && (
              <WritingDetail key={activeItem.id} item={activeItem.data} bucket={tab} onReviewed={handleReviewed} />
            )}
            {activeItem?.skill === "SPRECHEN" && (
              <SpeakingDetail key={activeItem.id} item={activeItem.data} bucket={tab} onReviewed={handleReviewed} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function WritingDetail({
  item,
  bucket,
  onReviewed,
}: {
  item: PendingWritingReviewItem;
  bucket: BucketKey;
  onReviewed: () => void;
}) {
  const ai = item.ai_evaluation;
  const [scores, setScores] = useState<Record<string, number>>(() =>
    Object.fromEntries(item.rubric_criteria.map((c) => [c.id, ai?.rubric_scores[c.id] ?? 0])),
  );
  const [feedback, setFeedback] = useState(ai?.feedback ?? "");
  const [saving, setSaving] = useState(false);
  const alreadyGraded = bucket === "BEWERTET" || bucket === "ZURUECKGEGEBEN";

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
          <p className="text-xs text-[var(--admin-text-muted)]">
            {item.student_name} · {item.lesson_title} ({item.level})
          </p>
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
              <Sparkles size={12} /> KI-Bewertung{alreadyGraded ? "" : " (Vorschlag)"}
            </p>
            {ai.strengths && <p className="mt-2 text-xs text-[var(--admin-text-secondary)]">{ai.strengths}</p>}
            {ai.feedback && (
              <p className="mt-1 whitespace-pre-line text-xs text-[var(--admin-text-secondary)]">{ai.feedback}</p>
            )}
          </div>
        )}

        {alreadyGraded ? (
          <div className="rounded-xl bg-white/[0.02] p-4 ring-1 ring-[var(--admin-border)]">
            <p className="text-sm font-semibold text-[var(--admin-text-primary)]">
              {item.submission.final_score} / {item.rubric_criteria.reduce((s, c) => s + c.max_score, 0)} Punkte
            </p>
            <p className="mt-1 text-xs text-[var(--admin-text-muted)]">
              {item.submission.notified ? "Ergebnis wurde dem Schüler zugestellt." : "Bewertet, Benachrichtigung ausstehend."}
            </p>
          </div>
        ) : (
          <>
            <div>
              <p className="mb-2 text-xs font-medium text-[var(--admin-text-secondary)]">Kriterien-Punktzahl</p>
              <div className="space-y-2">
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
          </>
        )}
      </div>
    </AdminCard>
  );
}

function SpeakingDetail({
  item,
  bucket,
  onReviewed,
}: {
  item: PendingSpeakingReviewItem;
  bucket: BucketKey;
  onReviewed: () => void;
}) {
  const [scores, setScores] = useState<Record<string, number>>(() =>
    Object.fromEntries(item.rubric_criteria.map((c) => [c.id, 0])),
  );
  const [feedback, setFeedback] = useState("");
  const [feedbackAudio, setFeedbackAudio] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const alreadyGraded = bucket === "BEWERTET" || bucket === "ZURUECKGEGEBEN";

  async function togglePlay() {
    const audio = document.getElementById("homework-speaking-audio") as HTMLAudioElement | null;
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
      if (feedbackAudio) {
        await reviewSpeakingSubmissionWithAudio(item.submission.id, {
          rubric_scores: scores,
          feedback: feedback || undefined,
          finalize,
          file: feedbackAudio,
          filename: feedbackAudio.name,
        });
      } else {
        await reviewSpeakingSubmission(item.submission.id, { rubric_scores: scores, feedback, finalize });
      }
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
          <p className="text-xs text-[var(--admin-text-muted)]">
            {item.student_name} · {item.lesson_title} ({item.level})
          </p>
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
            <audio id="homework-speaking-audio" src={audioUrl} onEnded={() => setPlaying(false)} className="hidden" />
          )}
        </div>

        {alreadyGraded ? (
          <div className="rounded-xl bg-white/[0.02] p-4 ring-1 ring-[var(--admin-border)]">
            <p className="text-sm font-semibold text-[var(--admin-text-primary)]">
              {item.submission.final_score} / {item.rubric_criteria.reduce((s, c) => s + c.max_score, 0)} Punkte
            </p>
            <p className="mt-1 text-xs text-[var(--admin-text-muted)]">
              {item.submission.notified ? "Ergebnis wurde dem Schüler zugestellt." : "Bewertet, Benachrichtigung ausstehend."}
            </p>
          </div>
        ) : (
          <>
            <div>
              <p className="mb-2 text-xs font-medium text-[var(--admin-text-secondary)]">Kriterien-Punktzahl</p>
              <div className="space-y-2">
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
              <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">
                Feedback (Text)
              </label>
              <AdminTextarea value={feedback} onChange={(e) => setFeedback(e.target.value)} rows={3} />
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">
                Feedback (Audio, optional)
              </label>
              <input
                type="file"
                accept="audio/*"
                onChange={(e) => setFeedbackAudio(e.target.files?.[0] ?? null)}
                className="block w-full text-xs text-[var(--admin-text-secondary)] file:mr-3 file:rounded-md file:border-0 file:bg-[var(--admin-primary)]/15 file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-[var(--admin-primary)]"
              />
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
          </>
        )}
      </div>
    </AdminCard>
  );
}
