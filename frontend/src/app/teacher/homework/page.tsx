"use client";

import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, ClipboardList, RotateCcw, Search } from "lucide-react";

import PageHeader from "@/components/dashboard/page-header";
import {
  gradeTeacherHomeworkSubmission,
  getTeacherHomeworkSubmissions,
} from "@/features/teacher/services/teacher.service";
import type { TeacherHomeworkSubmission } from "@/features/teacher/types";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

const TABS = [
  { key: "", labelKey: "teacher.homeworkAll" },
  { key: "SUBMITTED", labelKey: "teacher.homeworkToGrade" },
  { key: "GRADED", labelKey: "teacher.homeworkGraded" },
  { key: "NEEDS_REVISION", labelKey: "teacher.homeworkRevision" },
] as const;

const STATUS_BADGE: Record<string, string> = {
  SUBMITTED: "bg-accent-blue/10 text-accent-blue",
  GRADED: "bg-success/10 text-success",
  NEEDS_REVISION: "bg-warning/10 text-warning",
};

/** Real Hausaufgaben submissions (HomeworkSubmission — see
 * backend/app/models/homework_submission.py), scoped server-side to this
 * teacher's TeacherAssignment courses (GET /teacher/homework). Grading
 * (score + feedback + status) writes through PATCH
 * /teacher/homework/{id}/grade, re-checked server-side against the exact
 * same course scope on every write — never trust the list the client
 * happens to be looking at. */
export default function TeacherHomeworkPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<string>("");
  const [search, setSearch] = useState("");
  const [active, setActive] = useState<TeacherHomeworkSubmission | null>(null);

  const { data: items, isLoading } = useQuery({
    queryKey: ["teacher-homework", status, search],
    queryFn: () => getTeacherHomeworkSubmissions({ status: status || undefined, search: search || undefined }),
  });

  function handleGraded(updated: TeacherHomeworkSubmission) {
    setActive(updated);
    queryClient.invalidateQueries({ queryKey: ["teacher-homework"] });
    queryClient.invalidateQueries({ queryKey: ["teacher-overview"] });
  }

  return (
    <div className="space-y-6">
      <PageHeader icon={ClipboardList} titleKey="teacher.navHomework" gradient="from-accent-blue to-purple-600" />

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex gap-1.5 overflow-x-auto rounded-xl bg-surface-hover p-1 ring-1 ring-surface-border">
          {TABS.map((tb) => (
            <button
              key={tb.key}
              onClick={() => {
                setStatus(tb.key);
                setActive(null);
              }}
              className={cn(
                "min-h-11 shrink-0 whitespace-nowrap rounded-lg px-3 py-2 text-xs font-semibold transition-colors",
                status === tb.key ? "bg-accent-blue text-white" : "text-text-secondary hover:bg-surface-card",
              )}
            >
              {t(tb.labelKey)}
            </button>
          ))}
        </div>

        <div className="relative sm:w-64">
          <Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t("teacher.homeworkSearchPlaceholder")}
            className="h-11 w-full rounded-xl bg-surface-card pl-9 pr-3 text-sm text-text-primary ring-1 ring-surface-border outline-none focus:ring-accent-blue"
          />
        </div>
      </div>

      {isLoading && <p className="text-sm text-text-muted">{t("common.loading")}</p>}

      {!isLoading && (items?.length ?? 0) === 0 && (
        <div className="rounded-card bg-surface-card p-10 text-center shadow-[var(--shadow-md)] ring-1 ring-surface-border">
          <ClipboardList className="mx-auto mb-2 text-text-muted" size={22} />
          <p className="text-sm text-text-muted">{t("teacher.homeworkEmpty")}</p>
        </div>
      )}

      {!isLoading && (items?.length ?? 0) > 0 && (
        <div className="grid gap-4 lg:grid-cols-[380px_1fr]">
          <div className="space-y-2">
            {items!.map((item) => (
              <button
                key={item.id}
                onClick={() => setActive(item)}
                className={cn(
                  "w-full rounded-2xl p-4 text-left ring-1 transition-colors",
                  active?.id === item.id
                    ? "bg-accent-blue/10 ring-accent-blue/30"
                    : "bg-surface-card ring-surface-border hover:bg-surface-hover",
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="truncate text-sm font-bold text-text-primary">{item.student_name}</p>
                  <span className={cn("shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold", STATUS_BADGE[item.status])}>
                    {t(`teacher.homework${item.status === "SUBMITTED" ? "ToGrade" : item.status === "GRADED" ? "Graded" : "Revision"}`)}
                  </span>
                </div>
                <p className="mt-0.5 truncate text-xs text-text-muted">
                  {item.homework_title} · {item.lesson_title} ({item.course_level})
                </p>
              </button>
            ))}
          </div>

          <div>
            {active ? (
              <HomeworkGradeCard item={active} onGraded={handleGraded} />
            ) : (
              <div className="flex h-full min-h-[200px] items-center justify-center rounded-card bg-surface-card text-sm text-text-muted ring-1 ring-surface-border">
                {t("teacher.homeworkSelectPrompt")}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function HomeworkGradeCard({
  item,
  onGraded,
}: {
  item: TeacherHomeworkSubmission;
  onGraded: (updated: TeacherHomeworkSubmission) => void;
}) {
  const { t } = useTranslation();
  const [score, setScore] = useState(item.score ?? 0);
  const [feedback, setFeedback] = useState(item.feedback ?? "");
  const [saving, setSaving] = useState<"GRADED" | "NEEDS_REVISION" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const maxScore = 100;
  const scoreValid = useMemo(() => Number.isFinite(score) && score >= 0 && score <= maxScore, [score]);

  async function submit(nextStatus: "GRADED" | "NEEDS_REVISION") {
    if (!scoreValid || feedback.trim().length === 0) {
      setError("Bewertung (0-100) und Feedback sind erforderlich.");
      return;
    }
    setError(null);
    setSaving(nextStatus);
    try {
      const updated = await gradeTeacherHomeworkSubmission(item.id, { score, feedback, status: nextStatus });
      onGraded(updated);
    } catch {
      setError("Speichern fehlgeschlagen.");
    } finally {
      setSaving(null);
    }
  }

  return (
    <div className="space-y-4 rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
      <div>
        <h3 className="text-base font-bold text-text-primary">{item.homework_title}</h3>
        <p className="text-xs text-text-muted">
          {item.student_name} ({item.student_email}) · {item.course_title} ({item.course_level}) · Lektion{" "}
          {item.lesson_number}: {item.lesson_title}
        </p>
      </div>

      <div>
        <p className="mb-1 text-xs font-medium text-text-secondary">{t("teacher.homeworkStudentAnswer")}</p>
        <div className="whitespace-pre-line rounded-xl bg-surface-hover p-4 text-sm text-text-secondary">
          {item.text_content}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-[120px_1fr]">
        <div>
          <label className="mb-1 block text-xs font-medium text-text-secondary">{t("teacher.homeworkScore")}</label>
          <input
            type="number"
            min={0}
            max={100}
            value={score}
            onChange={(e) => setScore(Number(e.target.value))}
            className="h-11 w-full rounded-xl bg-surface-hover px-3 text-sm text-text-primary ring-1 ring-surface-border outline-none focus:ring-accent-blue"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-text-secondary">{t("teacher.homeworkFeedback")}</label>
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            rows={4}
            className="w-full rounded-xl bg-surface-hover p-3 text-sm text-text-primary ring-1 ring-surface-border outline-none focus:ring-accent-blue"
          />
        </div>
      </div>

      {error && <p className="text-xs text-danger">{error}</p>}

      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => submit("NEEDS_REVISION")}
          disabled={saving !== null}
          className="flex min-h-11 items-center gap-1.5 rounded-xl bg-surface-hover px-4 py-2 text-sm font-semibold text-text-primary ring-1 ring-surface-border transition-colors hover:bg-surface-border disabled:opacity-60"
        >
          <RotateCcw size={14} />
          {saving === "NEEDS_REVISION" ? t("teacher.homeworkSaving") : t("teacher.homeworkMarkRevision")}
        </button>
        <button
          onClick={() => submit("GRADED")}
          disabled={saving !== null}
          className="flex min-h-11 items-center gap-1.5 rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-60"
        >
          <CheckCircle2 size={14} />
          {saving === "GRADED" ? t("teacher.homeworkSaving") : t("teacher.homeworkMarkGraded")}
        </button>
      </div>
    </div>
  );
}
