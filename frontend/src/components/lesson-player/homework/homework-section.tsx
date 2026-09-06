"use client";

import { useState } from "react";
import { CheckCircle2, ClipboardCheck, RotateCcw } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { useTranslation } from "@/lib/i18n/use-translation";
import {
  getLessonHomework,
  getMyHomeworkSubmission,
  submitHomework,
} from "@/features/lessons/services/homework-service";
import LessonSection from "../common/lesson-section";

interface Props {
  lessonId: string;
}

const STATUS_LABEL: Record<string, { de: string; className: string }> = {
  SUBMITTED: { de: "Eingereicht", className: "bg-accent-blue/10 text-accent-blue" },
  GRADED: { de: "Bewertet", className: "bg-success/10 text-success" },
  NEEDS_REVISION: { de: "Zur Überarbeitung", className: "bg-warning/10 text-warning" },
};

/** The real Hausaufgabe workflow — published Homework rows for this
 * lesson (see app/models/homework.py), each with the student's own
 * HomeworkSubmission if one exists (see app/models/homework_submission.py
 * — a new table, this section had no submission concept at all before).
 * A NEEDS_REVISION submission can be resubmitted (same textarea, same
 * submit action — the backend upserts in place); GRADED shows the
 * score/feedback and stays editable is intentionally NOT offered (once
 * graded, the answer is final — matches the spec's "hozircha faqat
 * status + feedback ko'rsat" for the no-formal-resubmission-workflow
 * case, since GRADED has no re-open action here). */
export default function HomeworkSection({ lessonId }: Props) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const { data: homeworks, isLoading } = useQuery({
    queryKey: ["lesson-homework", lessonId],
    queryFn: () => getLessonHomework(lessonId),
  });

  return (
    <LessonSection
      title={t("lessons.sectionHomework")}
      description={t("lessons.homeworkDescription")}
      icon={ClipboardCheck}
    >
      {isLoading && <p className="text-sm text-text-muted">{t("common.loading")}</p>}

      {!isLoading && (homeworks?.length ?? 0) === 0 && (
        <div className="rounded-2xl bg-surface-hover/60 p-6 text-center ring-1 ring-surface-border sm:p-8">
          <p className="text-text-secondary">Für diese Lektion ist noch keine Hausaufgabe verfügbar.</p>
        </div>
      )}

      <div className="space-y-5">
        {homeworks?.map((homework) => (
          <HomeworkTask
            key={homework.id}
            homework={homework}
            onSubmitted={() => queryClient.invalidateQueries({ queryKey: ["section-gate", lessonId] })}
          />
        ))}
      </div>
    </LessonSection>
  );
}

function HomeworkTask({
  homework,
  onSubmitted,
}: {
  homework: { id: string; title: string; description: string; max_score: number };
  onSubmitted: () => void;
}) {
  const { data: submission, isLoading } = useQuery({
    queryKey: ["homework-submission", homework.id],
    queryFn: () => getMyHomeworkSubmission(homework.id),
  });

  const [draft, setDraft] = useState("");
  const [saving, setSaving] = useState(false);
  const [localSubmission, setLocalSubmission] = useState(submission);

  const current = localSubmission ?? submission ?? null;
  const canEdit = !current || current.status === "NEEDS_REVISION";

  async function handleSubmit() {
    const text = (draft || current?.text_content || "").trim();
    if (!text) return;
    setSaving(true);
    try {
      const result = await submitHomework(homework.id, text);
      setLocalSubmission(result);
      setDraft("");
      onSubmitted();
    } finally {
      setSaving(false);
    }
  }

  if (isLoading) {
    return <div className="rounded-2xl bg-surface-hover p-6 text-sm text-text-muted">Wird geladen...</div>;
  }

  const statusMeta = current ? STATUS_LABEL[current.status] : null;

  return (
    <div className="rounded-2xl bg-surface-hover p-6">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h3 className="text-lg font-bold text-text-primary">{homework.title}</h3>
        {statusMeta && (
          <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-bold ${statusMeta.className}`}>
            {statusMeta.de}
          </span>
        )}
      </div>
      <p className="mt-2.5 whitespace-pre-line text-sm text-text-secondary sm:text-base">{homework.description}</p>

      {current && current.status !== "NEEDS_REVISION" && (
        <div className="mt-4 rounded-xl bg-surface-card p-4 ring-1 ring-surface-border">
          <p className="whitespace-pre-line text-sm text-text-secondary">{current.text_content}</p>
        </div>
      )}

      {current?.status === "GRADED" && (
        <div className="mt-4 rounded-xl bg-success/5 p-4 ring-1 ring-success/20">
          <p className="flex items-center gap-1.5 text-sm font-bold text-success">
            <CheckCircle2 size={15} />
            {current.score}/{homework.max_score} Punkte
          </p>
          {current.feedback && <p className="mt-2 text-sm text-text-secondary">{current.feedback}</p>}
        </div>
      )}

      {current?.status === "NEEDS_REVISION" && (
        <>
          {current.feedback && (
            <div className="mt-4 rounded-xl bg-warning/5 p-4 ring-1 ring-warning/20">
              <p className="flex items-center gap-1.5 text-sm font-bold text-warning">
                <RotateCcw size={15} />
                Zur Überarbeitung
              </p>
              <p className="mt-2 text-sm text-text-secondary">{current.feedback}</p>
            </div>
          )}
          <textarea
            defaultValue={current.text_content}
            onChange={(e) => setDraft(e.target.value)}
            rows={6}
            className="mt-4 w-full rounded-xl bg-surface-card p-4 text-sm text-text-primary ring-1 ring-surface-border outline-none focus:ring-accent-blue"
          />
        </>
      )}

      {!current && (
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          rows={6}
          placeholder="Deine Antwort..."
          className="mt-4 w-full rounded-xl bg-surface-card p-4 text-sm text-text-primary ring-1 ring-surface-border outline-none placeholder:text-text-muted focus:ring-accent-blue"
        />
      )}

      {canEdit && (
        <button
          onClick={handleSubmit}
          disabled={saving || (!draft.trim() && !current)}
          className="mt-4 flex min-h-11 items-center gap-1.5 rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-60"
        >
          {saving ? "Wird abgegeben..." : current ? "Erneut abgeben" : "Abgeben"}
        </button>
      )}
    </div>
  );
}
