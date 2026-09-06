"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Mic, Pause, Play, Save } from "lucide-react";

import PageHeader from "@/components/dashboard/page-header";
import {
  getSpeakingAudioBlobUrl,
  listPendingSpeakingReviews,
  reviewSpeakingSubmission,
  reviewSpeakingSubmissionWithAudio,
} from "@/features/admin/services/assessment-service";
import type { PendingSpeakingReviewItem } from "@/features/admin/types/assessment.types";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

const TABS = [
  { key: "ALLE", label: "Alle" },
  { key: "NEU", label: "Neu" },
  { key: "IN_PRUEFUNG", label: "In Prüfung" },
  { key: "BEWERTET", label: "Bewertet" },
  { key: "ZURUECKGEGEBEN", label: "Zurückgegeben" },
] as const;

/** Real Sprechen submissions (SpeakingSubmission — Assessment Engine),
 * scoped server-side to this teacher's TeacherAssignment courses — same
 * endpoint the Admin "Hausaufgaben" queue calls, automatically filtered
 * when the caller's role is TEACHER (see speaking_service.py /
 * app/services/teacher/scope.py). No fake recordings, no fake scores. */
export default function TeacherSprechenPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<(typeof TABS)[number]["key"]>("ALLE");
  const [active, setActive] = useState<PendingSpeakingReviewItem | null>(null);

  const { data: items, isLoading } = useQuery({
    queryKey: ["teacher-sprechen", tab],
    queryFn: () => listPendingSpeakingReviews(undefined, tab),
  });

  function handleReviewed() {
    setActive(null);
    queryClient.invalidateQueries({ queryKey: ["teacher-sprechen"] });
  }

  return (
    <div className="space-y-6">
      <PageHeader icon={Mic} titleKey="teacher.navSprechen" gradient="from-accent-blue to-purple-600" />

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
          <Mic className="mx-auto mb-2 text-text-muted" size={22} />
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
              <SpeakingReviewCard key={active.submission.id} item={active} tab={tab} onReviewed={handleReviewed} />
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

function SpeakingReviewCard({
  item,
  tab,
  onReviewed,
}: {
  item: PendingSpeakingReviewItem;
  tab: string;
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
  const alreadyGraded = tab === "BEWERTET" || tab === "ZURUECKGEGEBEN" || item.submission.status === "FINAL";

  async function togglePlay() {
    const audio = document.getElementById("teacher-sprechen-audio") as HTMLAudioElement | null;
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
    <div className="space-y-4 rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
      <div>
        <h3 className="text-base font-bold text-text-primary">{item.task_title}</h3>
        <p className="text-xs text-text-muted">
          {item.student_name} · {item.lesson_title} ({item.level})
        </p>
      </div>

      <div className="flex items-center gap-3 rounded-xl bg-surface-hover p-4">
        <button
          onClick={togglePlay}
          aria-label={playing ? "Pause" : "Abspielen"}
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-accent-blue text-white"
        >
          {playing ? <Pause size={16} /> : <Play size={16} />}
        </button>
        <span className="text-xs text-text-secondary">
          {item.submission.duration_seconds != null ? `${item.submission.duration_seconds}s` : "Aufnahme"}
        </span>
        {audioUrl && (
          <audio id="teacher-sprechen-audio" src={audioUrl} onEnded={() => setPlaying(false)} className="hidden" />
        )}
      </div>

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
            <label className="mb-1 block text-xs font-medium text-text-secondary">Feedback (Text)</label>
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              rows={3}
              className="w-full rounded-xl bg-surface-hover p-3 text-sm text-text-primary ring-1 ring-surface-border outline-none focus:ring-accent-blue"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-text-secondary">Feedback (Audio, optional)</label>
            <input
              type="file"
              accept="audio/*"
              onChange={(e) => setFeedbackAudio(e.target.files?.[0] ?? null)}
              className="block w-full text-xs text-text-secondary file:mr-3 file:rounded-md file:border-0 file:bg-accent-blue/15 file:px-3 file:py-2 file:text-xs file:font-semibold file:text-accent-blue"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleSave(false)}
              disabled={saving}
              className="flex min-h-11 items-center gap-1.5 rounded-xl bg-surface-hover px-4 py-2 text-sm font-semibold text-text-primary ring-1 ring-surface-border transition-colors hover:bg-surface-border disabled:opacity-60"
            >
              <Save size={14} />
              Fortschritt speichern
            </button>
            <button
              onClick={() => handleSave(true)}
              disabled={saving}
              className="flex min-h-11 items-center gap-1.5 rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-60"
            >
              <CheckCircle2 size={14} />
              {saving ? "Wird gespeichert..." : "Bewertung finalisieren"}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
