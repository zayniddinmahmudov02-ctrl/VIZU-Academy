"use client";

import { useState } from "react";
import { CheckCircle2, Loader2, Play, RotateCcw } from "lucide-react";

import { getTeacherLegacySpeakingAudioBlobUrl } from "@/features/teacher/services/teacher.service";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import { gradeSubmission, type StudentDetail, type Submission } from "../groups-service";
import { card, fmtDate, input, Pill, primaryBtn, secondaryBtn, Stat, SubmissionBadge, TaskBadge, textarea, useErrorText } from "./ui";

const SKILL_LABEL: Record<string, string> = {
  LESEN: "Lesen", HOEREN: "Hören", SCHREIBEN: "Schreiben", SPRECHEN: "Sprechen", GRAMMATIK: "Grammatik", WORTSCHATZ: "Wortschatz",
};

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <h2 className="text-sm font-bold uppercase tracking-wide text-text-muted">{title}</h2>
      {children}
    </section>
  );
}

function AudioButton({ id }: { id: string }) {
  const { t } = useTranslation();
  const [url, setUrl] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  if (url) return <audio controls src={url} className="w-full" autoPlay />;
  return (
    <button type="button" className={secondaryBtn} disabled={busy}
            onClick={async () => { setBusy(true); try { setUrl(await getTeacherLegacySpeakingAudioBlobUrl(id)); } finally { setBusy(false); } }}>
      {busy ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />} {t("groups.listen")}
    </button>
  );
}

function GradeForm({ sub, onGraded }: { sub: Submission; onGraded: () => void }) {
  const { t } = useTranslation();
  const errorText = useErrorText();
  const [score, setScore] = useState(String(sub.score ?? ""));
  const [feedback, setFeedback] = useState(sub.feedback ?? "");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(status: "GRADED" | "NEEDS_REVISION") {
    const n = Number(score);
    if (score === "" || Number.isNaN(n) || n < 0 || n > 100 || !feedback.trim()) {
      setError(t("groups.gradeRequired"));
      return;
    }
    setBusy(status);
    setError(null);
    try {
      await gradeSubmission(sub.kind, sub.id, { score: Math.round(n), feedback: feedback.trim(), status });
      onGraded();
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-2 rounded-xl bg-surface-hover/60 p-3">
      <div className="grid gap-2 sm:grid-cols-[120px_1fr]">
        <input type="number" min={0} max={100} className={input} aria-label={t("groups.scoreField")} placeholder={t("groups.scoreField")}
               value={score} onChange={(e) => setScore(e.target.value)} />
        <textarea className={textarea} rows={2} maxLength={5000} aria-label={t("groups.feedback")} placeholder={t("groups.feedback")}
                  value={feedback} onChange={(e) => setFeedback(e.target.value)} />
      </div>
      {error && <p role="alert" className="text-xs text-danger">{error}</p>}
      <div className="flex flex-wrap justify-end gap-2">
        <button type="button" className={secondaryBtn} disabled={!!busy} onClick={() => submit("NEEDS_REVISION")}>
          {busy === "NEEDS_REVISION" ? <Loader2 size={14} className="animate-spin" /> : <RotateCcw size={14} />} {t("groups.needsRevision")}
        </button>
        <button type="button" className={primaryBtn} disabled={!!busy} onClick={() => submit("GRADED")}>
          {busy === "GRADED" ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle2 size={14} />} {t("groups.accept")}
        </button>
      </div>
    </div>
  );
}

function SubmissionCard({ sub, grading, onGraded }: { sub: Submission; grading: boolean; onGraded: () => void }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  return (
    <li className={cn(card, "p-4")}>
      <button type="button" className="flex w-full items-start justify-between gap-3 text-left" onClick={() => setOpen((v) => !v)} aria-expanded={open}>
        <div className="min-w-0">
          <p className="truncate text-sm font-bold text-text-primary">{sub.title}</p>
          <p className="text-xs text-text-muted">
            {t(`groups.kind_${sub.kind}`)} · {sub.course_level} · {sub.lesson_number}. {sub.lesson_title}
            {sub.submitted_at && <> · {t("groups.submittedAt")} {fmtDate(sub.submitted_at, true)}</>}
            {sub.deadline && <> · {t("groups.deadline")} {fmtDate(sub.deadline, true)}</>}
          </p>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-1">
          <SubmissionBadge status={sub.status} />
          {sub.score != null && <span className="text-xs font-bold text-text-primary">{t("groups.points", { n: sub.score })}</span>}
        </div>
      </button>
      {open && (
        <div className="mt-3 space-y-3">
          {sub.kind === "speaking" ? <AudioButton id={sub.id} /> : sub.answer_text ? (
            <div className="whitespace-pre-wrap break-words rounded-xl bg-surface-hover p-3 text-sm text-text-secondary">{sub.answer_text}</div>
          ) : null}
          {sub.feedback && (
            <p className="rounded-xl bg-accent-blue/5 p-3 text-sm text-text-secondary ring-1 ring-accent-blue/20"><b>{t("groups.feedback")}:</b> {sub.feedback}</p>
          )}
          {grading && sub.status !== "in_progress" && <GradeForm sub={sub} onGraded={onGraded} />}
        </div>
      )}
    </li>
  );
}

/** One student's work in a group, all from the LMS: tasks, lessons,
 *  competencies, submissions (gradable for the teacher) and activity. */
export default function ProgressDetail({ detail, grading = false, onGraded }: { detail: StudentDetail; grading?: boolean; onGraded?: () => void }) {
  const { t } = useTranslation();
  const s = detail.summary;
  const refresh = onGraded ?? (() => undefined);

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label={t("groups.d_progress")} value={s.progress == null ? "—" : `${s.progress}%`} />
        <Stat label={t("groups.col_lessons")} value={`${s.lessons_completed}/${s.lessons_total}`} />
        <Stat label={t("groups.d_overdue")} value={s.tasks_overdue} tone={s.tasks_overdue ? "danger" : undefined} />
        <Stat label={t("groups.d_avgGrade")} value={s.average_grade ?? "—"} />
      </div>

      <Section title={t("groups.tabTasks")}>
        {detail.tasks.length === 0 ? <p className="text-sm text-text-muted">{t("groups.noTasks")}</p> : (
          <ul className="space-y-2">
            {detail.tasks.map((task) => (
              <li key={task.id} className={cn(card, "flex flex-col gap-2 p-4 sm:flex-row sm:items-center sm:justify-between")}>
                <div className="min-w-0">
                  <p className="text-sm font-bold text-text-primary">{task.title}</p>
                  <p className="text-xs text-text-muted">
                    {task.module} · {task.lesson_title} · {task.due_at ? `${t("groups.due")}: ${fmtDate(task.due_at, true)}` : t("groups.noDue")}
                  </p>
                  {task.note && <p className="mt-1 text-xs text-text-secondary">{task.note}</p>}
                </div>
                <TaskBadge status={task.status} />
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title={t("groups.submissions")}>
        {detail.submissions.length === 0 ? <p className="text-sm text-text-muted">{t("groups.noSubmissions")}</p> : (
          <ul className="space-y-2">
            {detail.submissions.map((sub) => <SubmissionCard key={`${sub.kind}-${sub.id}`} sub={sub} grading={grading} onGraded={refresh} />)}
          </ul>
        )}
      </Section>

      <Section title={t("groups.skills")}>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {detail.skills.map((k) => (
            <div key={k.skill} className={cn(card, "p-4")}>
              <p className="text-sm font-bold text-text-primary">{SKILL_LABEL[k.skill] ?? k.skill}</p>
              <p className="mt-1 text-xs text-text-muted">{k.lessons_total ? `${k.completed}/${k.lessons_total} ${t("groups.lessons")}` : t("groups.noData")}</p>
              {k.average_score != null && <p className="text-xs font-semibold text-text-secondary">Ø {k.average_score}</p>}
            </div>
          ))}
        </div>
      </Section>

      <Section title={t("groups.lessons")}>
        <div className={cn(card, "overflow-x-auto")}>
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="text-[11px] uppercase tracking-wide text-text-muted">
              <tr className="border-b border-surface-border">
                {[t("groups.lesson"), t("groups.status"), t("groups.started"), t("groups.completed"), t("groups.progress"), t("groups.lastActivity")].map((h) => <th key={h} className="px-3 py-2.5">{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {detail.lessons.map((l) => (
                <tr key={l.id} className="border-b border-surface-border last:border-0">
                  <td className="px-3 py-2.5"><p className="font-semibold text-text-primary">{l.number}. {l.title}</p><p className="text-xs text-text-muted">{l.level} · {l.module}</p></td>
                  <td className="px-3 py-2.5">
                    <Pill className={l.status === "completed" ? "bg-success/10 text-success ring-success/30" : l.status === "in_progress" ? "bg-accent-blue/10 text-accent-blue ring-accent-blue/30" : "bg-surface-hover text-text-secondary ring-surface-border"}>
                      {t(`groups.lesson_${l.status}`)}
                    </Pill>
                  </td>
                  <td className="px-3 py-2.5 text-xs text-text-secondary">{fmtDate(l.started_at)}</td>
                  <td className="px-3 py-2.5 text-xs text-text-secondary">{fmtDate(l.completed_at)}</td>
                  <td className="px-3 py-2.5 text-xs text-text-secondary">{l.progress == null ? "—" : `${l.progress}%`}{l.score != null && ` · ${t("groups.points", { n: l.score })}`}</td>
                  <td className="px-3 py-2.5 text-xs text-text-secondary">{fmtDate(l.last_activity_at, true)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {detail.lessons.length === 0 && <p className="p-4 text-sm text-text-muted">{t("groups.noCourses")}</p>}
        </div>
      </Section>

      <Section title={t("groups.activity")}>
        <dl className={cn(card, "grid gap-3 p-5 sm:grid-cols-2")}>
          {[[t("groups.lastLogin"), fmtDate(detail.activity.last_login, true)],
            [t("groups.lastLessonActivity"), fmtDate(detail.activity.last_lesson_activity, true)],
            [t("groups.lastSubmission"), fmtDate(detail.activity.last_submission, true)],
            [t("groups.chatMessages"), `${detail.activity.chat_messages}${detail.activity.last_chat_message ? ` · ${fmtDate(detail.activity.last_chat_message, true)}` : ""}`],
          ].map(([k, v]) => (
            <div key={k}><dt className="text-xs text-text-muted">{k}</dt><dd className="text-sm font-semibold text-text-primary">{v}</dd></div>
          ))}
          {detail.activity.recent_reviews.length > 0 && (
            <div className="sm:col-span-2">
              <dt className="text-xs text-text-muted">{t("groups.recentReviews")}</dt>
              <dd className="mt-1 space-y-1">
                {detail.activity.recent_reviews.map((r, i) => (
                  <p key={i} className="text-sm text-text-secondary">{fmtDate(r.reviewed_at)} · {t(`groups.kind_${r.kind}`)} · {r.title}{r.score != null && ` · ${t("groups.points", { n: r.score })}`}</p>
                ))}
              </dd>
            </div>
          )}
        </dl>
      </Section>
    </div>
  );
}
