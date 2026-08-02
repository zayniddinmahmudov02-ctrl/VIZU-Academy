"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Sparkles } from "lucide-react";

import { AdminButton, AdminPageHeader, AdminTextarea } from "@/components/admin/admin-ui";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FormDialog from "@/components/admin/form-dialog";
import {
  evaluateSpeakingSubmission,
  evaluateWritingSubmission,
  listAttempts,
  listSpeakingSubmissions,
  listWritingSubmissions,
  reviewSpeakingSubmission,
  reviewWritingSubmission,
} from "@/features/admin/services/mock-exam-service";
import type { MockSpeakingSubmission, MockTestAttempt, MockWritingSubmission } from "@/features/admin/types/mock-exam.types";

const STATUS_STYLE: Record<string, string> = {
  IN_PROGRESS: "bg-white/5 text-[var(--admin-text-muted)]",
  SUBMITTED: "bg-[var(--admin-primary)]/15 text-[var(--admin-primary)]",
  GRADED: "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]",
};

export default function MockExamResultsPage() {
  const { data: attempts, isLoading } = useQuery({
    queryKey: ["mock-exam-attempts"],
    queryFn: () => listAttempts(),
  });

  const [reviewing, setReviewing] = useState<MockTestAttempt | null>(null);

  const columns: DataTableColumn<MockTestAttempt>[] = [
    { key: "user", header: "Nutzer-ID", render: (item) => item.user_id.slice(0, 8) },
    {
      key: "status",
      header: "Status",
      render: (item) => (
        <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${STATUS_STYLE[item.status]}`}>
          {item.status}
        </span>
      ),
    },
    {
      key: "score",
      header: "Punktzahl",
      render: (item) =>
        item.total_score !== null && item.max_score !== null
          ? `${item.total_score} / ${item.max_score} (${Math.round((item.total_score / item.max_score) * 100)}%)`
          : "—",
    },
    { key: "started_at", header: "Gestartet", render: (item) => new Date(item.started_at).toLocaleString("de-DE") },
    {
      key: "review",
      header: "",
      render: (item) => (
        <button
          onClick={() => setReviewing(item)}
          className="text-xs font-medium text-[var(--admin-primary)] hover:underline"
        >
          Details & Bewertung
        </button>
      ),
    },
  ];

  return (
    <div>
      <Link
        href="/admin/mock-exams"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--admin-text-muted)] hover:text-[var(--admin-text-primary)]"
      >
        <ArrowLeft size={14} />
        Mock Test Management
      </Link>

      <AdminPageHeader title="Ergebnisse" description="Alle Prüfungsversuche der Schüler, dauerhaft gespeichert." />

      <DataTable
        columns={columns}
        data={attempts}
        isLoading={isLoading}
        getRowId={(item) => item.id}
        emptyMessage="Noch keine Prüfungsversuche."
      />

      <FormDialog
        open={!!reviewing}
        onOpenChange={(open) => !open && setReviewing(null)}
        title="Versuch-Details"
        size="xl"
      >
        {reviewing && <AttemptDetail attempt={reviewing} />}
      </FormDialog>
    </div>
  );
}

function AttemptDetail({ attempt }: { attempt: MockTestAttempt }) {
  const { data: writingSubs } = useQuery({
    queryKey: ["mock-exam-writing-submissions", attempt.id],
    queryFn: () => listWritingSubmissions(attempt.id),
  });
  const { data: speakingSubs } = useQuery({
    queryKey: ["mock-exam-speaking-submissions", attempt.id],
    queryFn: () => listSpeakingSubmissions(attempt.id),
  });

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-3 text-sm">
        <div>
          <p className="text-[var(--admin-text-muted)]">Status</p>
          <p className="font-semibold text-[var(--admin-text-primary)]">{attempt.status}</p>
        </div>
        <div>
          <p className="text-[var(--admin-text-muted)]">Punktzahl</p>
          <p className="font-semibold text-[var(--admin-text-primary)]">
            {attempt.total_score ?? "—"} / {attempt.max_score ?? "—"}
          </p>
        </div>
        <div>
          <p className="text-[var(--admin-text-muted)]">Zeit</p>
          <p className="font-semibold text-[var(--admin-text-primary)]">{attempt.time_spent_seconds}s</p>
        </div>
      </div>

      {(writingSubs ?? []).map((sub) => (
        <WritingSubmissionCard key={sub.id} submission={sub} />
      ))}

      {(speakingSubs ?? []).map((sub) => (
        <SpeakingSubmissionCard key={sub.id} submission={sub} />
      ))}

      {!writingSubs?.length && !speakingSubs?.length && (
        <p className="text-sm text-[var(--admin-text-muted)]">
          Keine Schreiben/Sprechen-Einreichungen für diesen Versuch (nur automatisch bewertete Fragen).
        </p>
      )}
    </div>
  );
}

function WritingSubmissionCard({ submission }: { submission: MockWritingSubmission }) {
  const queryClient = useQueryClient();
  const [evaluating, setEvaluating] = useState(false);
  const [teacherScore, setTeacherScore] = useState(submission.teacher_score?.toString() ?? "");
  const [teacherFeedback, setTeacherFeedback] = useState(submission.teacher_feedback ?? "");

  async function handleEvaluate() {
    setEvaluating(true);
    try {
      await evaluateWritingSubmission(submission.id);
      queryClient.invalidateQueries({ queryKey: ["mock-exam-writing-submissions"] });
    } finally {
      setEvaluating(false);
    }
  }

  async function handleSaveReview() {
    await reviewWritingSubmission(submission.id, {
      teacher_score: teacherScore ? Number(teacherScore) : null,
      teacher_feedback: teacherFeedback || null,
    });
    queryClient.invalidateQueries({ queryKey: ["mock-exam-writing-submissions"] });
  }

  return (
    <div className="rounded-xl bg-white/[0.02] p-4 ring-1 ring-[var(--admin-border)]">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--admin-text-muted)]">
        Schreiben — {submission.word_count} Wörter
      </p>
      <p className="mb-3 whitespace-pre-wrap text-sm text-[var(--admin-text-secondary)]">{submission.answer_text}</p>

      {submission.ai_score !== null ? (
        <div className="mb-3 grid grid-cols-3 gap-2 rounded-lg bg-white/[0.02] p-3 text-xs">
          <p>Grammatik: {submission.ai_grammar_score}</p>
          <p>Wortschatz: {submission.ai_vocabulary_score}</p>
          <p>Struktur: {submission.ai_structure_score}</p>
          <p>Aufgabe: {submission.ai_task_achievement_score}</p>
          <p>Kohärenz: {submission.ai_coherence_score}</p>
          <p className="font-semibold">Gesamt: {submission.ai_score}</p>
          <p className="col-span-3 mt-1 text-[var(--admin-text-secondary)]">{submission.ai_feedback}</p>
        </div>
      ) : (
        <AdminButton size="sm" variant="secondary" onClick={handleEvaluate} disabled={evaluating}>
          <Sparkles size={14} />
          {evaluating ? "Wird bewertet..." : "KI-Bewertung starten"}
        </AdminButton>
      )}

      <div className="mt-3 grid grid-cols-4 gap-2">
        <input
          type="number"
          value={teacherScore}
          onChange={(e) => setTeacherScore(e.target.value)}
          placeholder="Lehrerpunkte"
          className="h-9 rounded-lg bg-[var(--admin-card)] px-3 text-sm ring-1 ring-[var(--admin-border-strong)]"
        />
        <div className="col-span-3">
          <AdminTextarea
            value={teacherFeedback}
            onChange={(e) => setTeacherFeedback(e.target.value)}
            placeholder="Lehrer-Feedback"
            rows={1}
          />
        </div>
      </div>
      <AdminButton size="sm" variant="ghost" className="mt-2" onClick={handleSaveReview}>
        Bewertung speichern
      </AdminButton>
    </div>
  );
}

function SpeakingSubmissionCard({ submission }: { submission: MockSpeakingSubmission }) {
  const queryClient = useQueryClient();
  const [evaluating, setEvaluating] = useState(false);
  const [teacherScore, setTeacherScore] = useState(submission.teacher_score?.toString() ?? "");
  const [teacherFeedback, setTeacherFeedback] = useState(submission.teacher_feedback ?? "");

  async function handleEvaluate() {
    setEvaluating(true);
    try {
      await evaluateSpeakingSubmission(submission.id);
      queryClient.invalidateQueries({ queryKey: ["mock-exam-speaking-submissions"] });
    } finally {
      setEvaluating(false);
    }
  }

  async function handleSaveReview() {
    await reviewSpeakingSubmission(submission.id, {
      teacher_score: teacherScore ? Number(teacherScore) : null,
      teacher_feedback: teacherFeedback || null,
    });
    queryClient.invalidateQueries({ queryKey: ["mock-exam-speaking-submissions"] });
  }

  return (
    <div className="rounded-xl bg-white/[0.02] p-4 ring-1 ring-[var(--admin-border)]">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--admin-text-muted)]">Sprechen</p>
      <audio controls src={submission.audio_url} className="mb-3 w-full">
        <track kind="captions" />
      </audio>

      {submission.ai_score !== null ? (
        <div className="mb-3 rounded-lg bg-white/[0.02] p-3 text-xs">
          <p className="font-semibold">KI-Punktzahl: {submission.ai_score}</p>
          <p className="mt-1 text-[var(--admin-text-secondary)]">Transkript: {submission.transcript}</p>
          <p className="mt-1 text-[var(--admin-text-secondary)]">{submission.ai_feedback}</p>
        </div>
      ) : (
        <AdminButton size="sm" variant="secondary" onClick={handleEvaluate} disabled={evaluating}>
          <Sparkles size={14} />
          {evaluating ? "Wird bewertet..." : "KI-Bewertung starten"}
        </AdminButton>
      )}

      <div className="mt-3 grid grid-cols-4 gap-2">
        <input
          type="number"
          value={teacherScore}
          onChange={(e) => setTeacherScore(e.target.value)}
          placeholder="Lehrerpunkte"
          className="h-9 rounded-lg bg-[var(--admin-card)] px-3 text-sm ring-1 ring-[var(--admin-border-strong)]"
        />
        <div className="col-span-3">
          <AdminTextarea
            value={teacherFeedback}
            onChange={(e) => setTeacherFeedback(e.target.value)}
            placeholder="Lehrer-Feedback"
            rows={1}
          />
        </div>
      </div>
      <AdminButton size="sm" variant="ghost" className="mt-2" onClick={handleSaveReview}>
        Bewertung speichern
      </AdminButton>
    </div>
  );
}
