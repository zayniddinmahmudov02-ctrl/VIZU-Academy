"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";

import { EmptyState, ErrorState, fieldClass, Loading, Panel, TeacherPageTitle } from "@/components/teacher/teacher-ui";
import { formatDateTime } from "@/features/activity/lib/format";
import type { HomeworkSubmission } from "@/features/teacher/panel-types";
import { getHomeworkSubmissions, gradeHomework } from "@/features/teacher/services/teacher-panel.service";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

const FILTERS = [["", "homeworkAll"], ["SUBMITTED", "homeworkNew"], ["NEEDS_REVISION", "homeworkRevision"], ["GRADED", "homeworkGraded"]] as const;

function Grader({ item }: { item: HomeworkSubmission }) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const [score, setScore] = useState(String(item.score ?? ""));
  const [feedback, setFeedback] = useState(item.feedback ?? "");
  const [note, setNote] = useState<{ ok: boolean; text: string } | null>(null);
  const save = useMutation({
    mutationFn: (status: "GRADED" | "NEEDS_REVISION") => gradeHomework(item.id, { score: Number(score), feedback: feedback.trim(), status }),
    onSuccess: () => { setNote({ ok: true, text: t("tpanel.saved") }); qc.invalidateQueries({ queryKey: ["teacher-homework"] }); qc.invalidateQueries({ queryKey: ["teacher-dashboard"] }); },
    onError: () => setNote({ ok: false, text: t("tpanel.saveError") }),
  });
  const valid = score !== "" && Number(score) >= 0 && Number(score) <= 100 && feedback.trim().length > 0;

  return (
    <div className="space-y-3" data-testid="homework-grader">
      <div>
        <p className="font-semibold text-text-primary">{item.homework_title}</p>
        <p className="text-xs text-text-muted">{item.student_name} · {item.course_level} · Lektion {item.lesson_number}: {item.lesson_title}</p>
      </div>
      <div>
        <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-text-muted">{t("tpanel.answer")}</p>
        <p className="whitespace-pre-wrap rounded-xl bg-surface-hover p-3 text-sm text-text-primary">{item.text_content}</p>
      </div>
      <label className="block text-sm font-medium text-text-primary">{t("tpanel.score")}
        <input type="number" min={0} max={100} value={score} onChange={(e) => setScore(e.target.value)} className={`${fieldClass} mt-1 w-32`} data-testid="homework-score" />
      </label>
      <label className="block text-sm font-medium text-text-primary">{t("tpanel.feedback")}
        <textarea value={feedback} onChange={(e) => setFeedback(e.target.value)} rows={4} maxLength={5000} className={`${fieldClass} mt-1 w-full`} data-testid="homework-feedback" />
      </label>
      {note && <p className={cn("text-sm", note.ok ? "text-success" : "text-danger")} role="status">{note.text}</p>}
      <div className="flex flex-wrap gap-2">
        <button type="button" disabled={!valid || save.isPending} onClick={() => save.mutate("GRADED")} className="inline-flex items-center gap-2 rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white disabled:opacity-50" data-testid="homework-save">
          {save.isPending && <Loader2 size={15} className="animate-spin" />}{t("tpanel.saveGrade")}
        </button>
        <button type="button" disabled={!valid || save.isPending} onClick={() => save.mutate("NEEDS_REVISION")} className="rounded-xl px-4 py-2 text-sm font-medium text-text-primary ring-1 ring-surface-border disabled:opacity-50">{t("tpanel.sendRevision")}</button>
      </div>
    </div>
  );
}

export default function TeacherHomeworkPage() {
  const { t, language } = useTranslation();
  const [status, setStatus] = useState("SUBMITTED");
  const [selected, setSelected] = useState<string | null>(null);
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ["teacher-homework", status], queryFn: () => getHomeworkSubmissions(status || undefined) });
  const current = data?.find((d) => d.id === selected) ?? null;

  return (
    <div data-testid="teacher-hausaufgaben">
      <TeacherPageTitle title={t("tpanel.homeworkTitle")} subtitle={t("tpanel.homeworkSubtitle")} />
      <div className="mb-4 flex flex-wrap gap-2" role="tablist">
        {FILTERS.map(([value, key]) => (
          <button key={key} role="tab" aria-selected={status === value} onClick={() => { setStatus(value); setSelected(null); }}
                  className={cn("rounded-full px-4 py-1.5 text-sm font-semibold transition", status === value ? "bg-accent-blue text-white" : "bg-surface-card text-text-secondary ring-1 ring-surface-border hover:bg-surface-hover")}>
            {t(`teacher.${key}`)}
          </button>
        ))}
      </div>
      {isLoading && <Loading />}
      {isError && <ErrorState onRetry={() => refetch()} />}
      {data && data.length === 0 && <EmptyState text={t("tpanel.noSubmissions")} />}
      {data && data.length > 0 && (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)]">
          <Panel>
            <ul className="space-y-1.5">
              {data.map((h) => (
                <li key={h.id}>
                  <button type="button" onClick={() => setSelected(h.id)} data-testid="homework-item"
                          className={cn("w-full rounded-xl p-2.5 text-left transition", selected === h.id ? "bg-accent-blue/10 ring-1 ring-accent-blue/30" : "hover:bg-surface-hover")}>
                    <span className="block truncate text-sm font-medium text-text-primary">{h.student_name} · {h.homework_title}</span>
                    <span className="block text-xs text-text-muted">{h.course_level} · Lektion {h.lesson_number} · {formatDateTime(h.submitted_at, language)} · {t(`tpanel.hwStatus_${h.status}`)}</span>
                  </button>
                </li>
              ))}
            </ul>
          </Panel>
          <Panel>{current ? <Grader key={current.id} item={current} /> :<p className="py-8 text-center text-sm text-text-muted">{t("tpanel.pickSubmission")}</p>}</Panel>
        </div>
      )}
    </div>
  );
}
