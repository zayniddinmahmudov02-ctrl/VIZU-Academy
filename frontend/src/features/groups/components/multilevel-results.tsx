"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ChevronRight, Eye, PlayCircle } from "lucide-react";

import { formatDuration, levelLabel, levelTone, SECTION_LABEL_KEY } from "@/features/vorbereitung/lib/multilevel-labels";
import type { ResultLevel } from "@/features/vorbereitung/types/multilevel-exam.types";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import {
  getGroupMultilevel, getGroupMultilevelStudent, getMyGroupMultilevel, ML_SECTIONS, type MlAttempt, type MlStudentDetail,
} from "../groups-service";
import { card, ErrorBox, fmtDate, Loading, secondaryBtn } from "./ui";

type T = (key: string, vars?: Record<string, string | number>) => string;

/** One section cell: score / "baholanmoqda" / "baholanmagan" / "—" (never a score of an unfinished attempt — the API sends none). */
function SectionScore({ t, s }: { t: T; s: MlAttempt["sections"][keyof MlAttempt["sections"]] }) {
  if (!s || s.score === undefined) return <span className="text-text-muted">—</span>;
  if (s.no_key) return <span className="text-xs text-text-muted">{t("groups.ml_noKey")}</span>;
  if (s.awaiting_grading) return <span className="text-xs font-semibold text-amber-600 dark:text-amber-400">{t("groups.ml_awaiting")}</span>;
  return <span className="font-semibold text-text-primary">{s.score ?? "—"}</span>;
}

function LevelChip({ t, level, estimated }: { t: T; level: string | null | undefined; estimated?: boolean }) {
  if (!level) return <span className="text-text-muted">—</span>;
  return (
    <span className={cn("inline-flex rounded-full px-2 py-0.5 text-xs font-bold", levelTone(level as ResultLevel))} title={estimated ? t("groups.ml_estimatedHint") : undefined}>
      {levelLabel(t, level as ResultLevel)}{estimated ? " ≈" : ""}
    </span>
  );
}

function AttemptCard({ t, a, n }: { t: T; a: MlAttempt; n: number }) {
  const [open, setOpen] = useState(false);
  const running = a.status === "IN_PROGRESS";
  const feedback = ML_SECTIONS.map((k) => [k, a.sections[k]?.feedback] as const).filter(([, f]) => !!f);
  return (
    <li className="rounded-xl bg-surface-hover/50 p-3 ring-1 ring-surface-border" data-testid="ml-attempt" data-status={a.status}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-semibold text-text-primary">
          {t("groups.ml_attempt", { n })} · <span className="font-normal text-text-secondary">{fmtDate(a.started_at, true)}</span>
          {!running && a.duration_seconds ? <span className="text-xs text-text-muted"> · {formatDuration(a.duration_seconds)}</span> : null}
        </p>
        {running ? (
          <span className="rounded-full bg-warning/15 px-2 py-0.5 text-xs font-bold text-warning">{t("groups.ml_inProgress")}</span>
        ) : (
          <span className="flex items-center gap-2 text-sm">
            <span className="font-bold text-text-primary" data-testid="ml-attempt-total">{a.total_score ?? "—"} / {a.max_score ?? 300}</span>
            <LevelChip t={t} level={a.result_level} />
            {a.estimated_level && a.estimated_level !== a.result_level && <LevelChip t={t} level={a.estimated_level} estimated />}
          </span>
        )}
      </div>
      {!running && (
        <dl className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {ML_SECTIONS.map((k) => {
            const s = a.sections[k];
            return (
              <div key={k} className="rounded-lg bg-surface-card px-2.5 py-1.5 ring-1 ring-surface-border" data-testid={`ml-sec-${k}`}>
                <dt className="text-[11px] text-text-muted">{t(SECTION_LABEL_KEY[k])}</dt>
                <dd className="flex items-baseline justify-between gap-1 text-sm">
                  <span><SectionScore t={t} s={s} />{s && s.score != null && !s.no_key && <span className="text-xs text-text-muted"> / {s.max ?? 75}</span>}</span>
                  {s?.raw_max ? <span className="text-[11px] text-text-muted">{t("groups.ml_raw", { raw: s.raw_points ?? 0, max: s.raw_max })}</span> : null}
                </dd>
              </div>
            );
          })}
        </dl>
      )}
      {feedback.length > 0 && (
        <div className="mt-2">
          <button type="button" className="text-xs font-semibold text-accent-blue" onClick={() => setOpen(!open)} aria-expanded={open}>{t("groups.ml_feedback")}</button>
          {open && feedback.map(([k, f]) => (
            <p key={k} className="mt-1 whitespace-pre-wrap text-xs text-text-secondary"><b>{t(SECTION_LABEL_KEY[k])}:</b> {f}</p>
          ))}
        </div>
      )}
    </li>
  );
}

/** Every Modelltest of the level with the attempts (newest first). */
export function TestsWithAttempts({ detail, emptyHint }: { detail: MlStudentDetail; emptyHint?: string }) {
  const { t } = useTranslation();
  const shown = detail.tests.filter((x) => x.attempts.length > 0 || x.available);
  return (
    <ul className="space-y-3" data-testid="ml-tests">
      {shown.map((test) => (
        <li key={test.id} className={cn(card, "p-4")} data-testid="ml-test" data-number={test.number}>
          <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-bold text-text-primary">Modelltest {test.number} · <span className="font-semibold text-text-secondary">{test.title}</span></p>
            {test.best_total != null && <span className="text-xs text-text-secondary">{t("groups.ml_best")}: <b className="text-text-primary">{test.best_total}</b></span>}
          </div>
          {test.attempts.length === 0 ? (
            <p className="text-xs text-text-muted">{test.available ? t("groups.ml_notTaken") : t("groups.ml_preparing")}</p>
          ) : (
            <ul className="space-y-2">
              {test.attempts.map((a, i) => <AttemptCard key={a.attempt_id} t={t} a={a} n={test.attempts.length - i} />)}
            </ul>
          )}
        </li>
      ))}
      {shown.length === 0 && <p className={cn(card, "p-6 text-center text-sm text-text-muted")}>{emptyHint ?? t("groups.noData")}</p>}
    </ul>
  );
}

function StudentDrillDown({ groupId, studentId, onBack }: { groupId: string; studentId: string; onBack: () => void }) {
  const { t } = useTranslation();
  const q = useQuery({ queryKey: ["groups", groupId, "multilevel", studentId], queryFn: () => getGroupMultilevelStudent(groupId, studentId) });
  return (
    <div className="space-y-3" data-testid="ml-student-detail">
      <button type="button" className={secondaryBtn} onClick={onBack}><ArrowLeft size={14} /> {t("groups.back")}</button>
      {q.isLoading ? <Loading /> : q.isError || !q.data ? <ErrorBox error={q.error} onRetry={() => q.refetch()} /> : (
        <>
          <p className="text-base font-bold text-text-primary">{q.data.student?.name} <span className="text-xs font-normal text-text-muted">{q.data.student?.email}</span></p>
          <TestsWithAttempts detail={q.data} />
        </>
      )}
    </div>
  );
}

/** Teacher Panel → group → "Multilevel": every member's Modelltest results. Read only (the Super Admin grades / overrides). */
export function TeacherMultilevelTab({ groupId }: { groupId: string }) {
  const { t } = useTranslation();
  const [student, setStudent] = useState<string | null>(null);
  const q = useQuery({ queryKey: ["groups", groupId, "multilevel"], queryFn: () => getGroupMultilevel(groupId) });
  if (student) return <StudentDrillDown groupId={groupId} studentId={student} onBack={() => setStudent(null)} />;
  if (q.isLoading) return <Loading />;
  if (q.isError || !q.data) return <ErrorBox error={q.error} onRetry={() => q.refetch()} />;
  const d = q.data;
  return (
    <div className="space-y-3" data-testid="ml-overview">
      <p className="flex items-center gap-1.5 text-xs text-text-muted"><Eye size={13} /> {t("groups.ml_readOnly")}</p>
      {d.students.length === 0 ? <p className={cn(card, "p-6 text-center text-sm text-text-muted")}>{t("groups.noStudents")}</p> : (
        <div className={cn(card, "overflow-x-auto")}>
          <table className="w-full min-w-[920px] text-left text-sm" data-testid="ml-students-table">
            <thead className="text-[11px] uppercase tracking-wide text-text-muted">
              <tr className="border-b border-surface-border">
                {[t("groups.col_student"), t("groups.ml_col_tests"), t("groups.ml_col_attempts"), t("groups.ml_col_last"),
                  ...ML_SECTIONS.map((k) => t(SECTION_LABEL_KEY[k])), t("groups.ml_col_total"), t("groups.ml_col_level"), ""].map((h, i) => <th key={i} className="px-3 py-2.5">{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {d.students.map((r) => (
                <tr key={r.user_id} className="cursor-pointer border-b border-surface-border last:border-0 hover:bg-surface-hover/50" data-testid="ml-student-row"
                    onClick={() => setStudent(r.user_id)}>
                  <td className="px-3 py-2.5"><p className="font-semibold text-text-primary">{r.name}</p><p className="text-xs text-text-muted">{r.email}</p></td>
                  <td className="px-3 py-2.5 text-text-secondary" data-testid="ml-tests-taken">{r.tests_taken} / {d.tests.filter((x) => x.available).length}</td>
                  <td className="px-3 py-2.5 text-text-secondary" data-testid="ml-attempts">{r.attempts}{r.in_progress ? <span className="text-xs text-warning"> ({t("groups.ml_inProgress")})</span> : null}</td>
                  <td className="px-3 py-2.5 text-xs text-text-secondary">{r.last_attempt_at ? fmtDate(r.last_attempt_at, true) : t("groups.ml_noAttempts")}</td>
                  {ML_SECTIONS.map((k) => <td key={k} className="px-3 py-2.5"><SectionScore t={t} s={r.latest?.sections[k] ?? null} /></td>)}
                  <td className="px-3 py-2.5 font-bold text-text-primary" data-testid="ml-total">{r.latest ? `${r.latest.total_score ?? "—"} / ${r.latest.max_score ?? d.total_max}` : "—"}</td>
                  <td className="px-3 py-2.5" data-testid="ml-level"><LevelChip t={t} level={r.latest?.estimated_level ?? r.latest?.result_level} estimated={!!r.latest?.estimated_level} /></td>
                  <td className="px-3 py-2.5 text-right"><button type="button" aria-label={t("groups.ml_details")} title={t("groups.ml_details")}
                    className="rounded-lg p-1.5 text-text-muted hover:text-accent-blue" data-testid="ml-open-student"><ChevronRight size={16} /></button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className="text-xs text-text-muted">{t("groups.ml_latestHint")}</p>
    </div>
  );
}

/** Student → group → "Multilevel": the level's Modelltests (open through the group) and the student's own attempts. */
export function StudentMultilevelTab({ groupId }: { groupId: string }) {
  const { t } = useTranslation();
  const q = useQuery({ queryKey: ["groups", groupId, "multilevel", "me"], queryFn: () => getMyGroupMultilevel(groupId) });
  if (q.isLoading) return <Loading />;
  if (q.isError || !q.data) return <ErrorBox error={q.error} onRetry={() => q.refetch()} />;
  return (
    <div className="space-y-3" data-testid="ml-mine">
      <div className={cn(card, "flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between")}>
        <div>
          <p className="text-sm font-bold text-text-primary">{t("groups.ml_mineTitle")}</p>
          <p className="text-sm text-text-secondary">{t("groups.ml_mineHint")}</p>
        </div>
        <Link href="/vorbereitung/multilevel" data-testid="ml-go-tests"
              className="inline-flex min-h-11 shrink-0 items-center justify-center gap-1.5 rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white hover:opacity-90">
          <PlayCircle size={16} /> {t("groups.ml_start")}
        </Link>
      </div>
      <TestsWithAttempts detail={q.data} emptyHint={t("groups.ml_noAttempts")} />
    </div>
  );
}
