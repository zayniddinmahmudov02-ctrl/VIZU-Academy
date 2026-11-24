"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CalendarClock, Radio, Users } from "lucide-react";

import { EmptyState, ErrorState, Loading, Panel, TeacherPageTitle } from "@/components/teacher/teacher-ui";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import { getLessonBoard, getMyCourses, setLessonSignup } from "../services/market-service";
import type { SpecialLesson } from "../types";
import { Pill, buttonPrimary, buttonSecondary, formatDate, formatDateTime, formatPrice, useErrorText } from "./ui";

export function BackToCatalog() {
  const { t } = useTranslation();
  return (
    <Link href="/my-teacher" className="mb-4 inline-flex min-h-10 items-center gap-2 text-sm font-semibold text-text-secondary hover:text-text-primary">
      <ArrowLeft size={16} /> {t("market.title")}
    </Link>
  );
}

export function MyCoursesPage() {
  const { t, language } = useTranslation();
  const q = useQuery({ queryKey: ["my-teacher-courses"], queryFn: getMyCourses });
  return (
    <div data-testid="my-teacher-my-courses">
      <BackToCatalog />
      <TeacherPageTitle title={t("market.myCourses")} />
      {q.isLoading ? <Loading /> : q.isError ? <ErrorState onRetry={() => q.refetch()} /> : !q.data?.length ? <EmptyState text={t("market.noMyCourses")} /> : (
        <ul className="space-y-3">
          {q.data.map((e) => (
            <li key={e.id} className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-surface-card p-4 shadow-[var(--shadow-md)] ring-1 ring-surface-border"
                data-testid="my-course-row">
              <div className="min-w-0">
                <p className="font-semibold text-text-primary">{e.course.title} <span className="text-sm font-normal text-text-muted">({e.course.level})</span></p>
                <p className="text-sm text-text-secondary">
                  <Link href={`/my-teacher/${e.course.teacher.id}`} className="hover:underline">{e.course.teacher.name}</Link>
                  {" · "}{formatDate(e.course.start_date, language)}{e.price ? ` · ${formatPrice(e.price)} so'm` : ""}
                </p>
                {e.order?.rejection_reason && e.status === "REJECTED" && <p className="text-xs text-danger">{e.order.rejection_reason}</p>}
              </div>
              <div className="flex items-center gap-2">
                <Pill tone={e.status === "ACTIVE" ? "APPROVED" : e.status === "PENDING_PAYMENT" ? "PENDING" : "REJECTED"} testId="my-course-status">
                  {t(`market.enrollmentStatus_${e.status}`)}
                </Pill>
                {e.course.group_id && <Link href={`/groups/${e.course.group_id}`} className={buttonSecondary}>{t("market.toClassroom")}</Link>}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function LessonCard({ lesson, compact = false }: { lesson: SpecialLesson; compact?: boolean }) {
  const { t, language } = useTranslation();
  const errorText = useErrorText();
  const qc = useQueryClient();
  const signup = useMutation({ mutationFn: (on: boolean) => setLessonSignup(lesson.id, on),
                               onSuccess: () => void qc.invalidateQueries({ queryKey: ["special-lesson-board"] }) });
  const live = lesson.room?.status === "live";
  return (
    <article className={cn("rounded-2xl bg-surface-card ring-1 ring-surface-border", compact ? "p-3" : "p-4 shadow-[var(--shadow-md)]")} data-testid="lesson-card">
      <div className="flex flex-wrap items-center gap-2">
        {live && <span className="inline-flex items-center gap-1 rounded-full bg-danger px-2 py-0.5 text-xs font-bold text-white"><Radio size={12} /> {t("market.liveNow")}</span>}
        <Pill tone="DRAFT">{lesson.level} · {lesson.language}</Pill>
      </div>
      <h3 className={cn("mt-2 font-bold text-text-primary", compact ? "text-sm" : "text-base")} data-testid="lesson-title">{lesson.title}</h3>
      <p className="text-sm text-text-secondary">{lesson.teacher.name} · {t("market.topic")}: {lesson.topic}</p>
      <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-text-muted">
        <span className="inline-flex items-center gap-1"><CalendarClock size={12} /> {formatDateTime(lesson.starts_at, language)} · {t("market.minutes", { n: lesson.duration_minutes })}</span>
        <span className="inline-flex items-center gap-1"><Users size={12} /> {live ? t("market.online", { n: lesson.room?.online ?? 0 }) : t("market.participants", { n: lesson.signups })} · {t("market.maxParticipants", { n: lesson.max_participants })}</span>
      </p>
      {!compact && lesson.description && <p className="mt-2 whitespace-pre-line text-sm text-text-secondary">{lesson.description}</p>}
      {!compact && lesson.objectives && <p className="mt-2 text-sm text-text-secondary"><span className="font-semibold">{t("market.objectives")}:</span> {lesson.objectives}</p>}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        {live && lesson.room ? (
          <Link href={`/video-room/${lesson.room.id}`} className={buttonPrimary} data-testid="lesson-join">{t("market.join")}</Link>
        ) : lesson.status === "APPROVED" ? (
          <button type="button" className={lesson.signed_up ? buttonSecondary : buttonPrimary} disabled={signup.isPending}
                  onClick={() => signup.mutate(!lesson.signed_up)} data-testid="lesson-signup">
            {lesson.signed_up ? t("market.signupOff") : t("market.signup")}
          </button>
        ) : null}
        {lesson.signed_up && !live && <span className="text-xs text-emerald-600">{t("market.signedUp")}</span>}
      </div>
      {signup.isError && <p className="mt-2 text-xs text-danger" role="alert">{errorText(signup.error)}</p>}
      {!compact && live && <p className="mt-2 text-xs text-text-muted">{t("market.mutedNote")}</p>}
    </article>
  );
}

export function useLessonBoard(enabled = true) {
  return useQuery({ queryKey: ["special-lesson-board"], queryFn: getLessonBoard, enabled, refetchInterval: 30_000 });
}

export function LiveLessonsPage() {
  const { t } = useTranslation();
  const q = useLessonBoard();
  return (
    <div data-testid="my-teacher-live">
      <BackToCatalog />
      <TeacherPageTitle title={t("market.liveTitle")} subtitle={t("market.liveSubtitle")} />
      {q.isLoading ? <Loading /> : q.isError ? <ErrorState onRetry={() => q.refetch()} /> : (
        <div className="space-y-6">
          {q.data!.live.length > 0 && (
            <Panel title={t("market.liveNow")} testId="lessons-live">
              <div className="grid gap-3 md:grid-cols-2">{q.data!.live.map((l) => <LessonCard key={l.id} lesson={l} />)}</div>
            </Panel>
          )}
          <Panel title={t("market.upcoming")} testId="lessons-upcoming">
            {q.data!.upcoming.length === 0 ? <EmptyState text={t("market.noLessons")} /> : (
              <div className="grid gap-3 md:grid-cols-2">{q.data!.upcoming.map((l) => <LessonCard key={l.id} lesson={l} />)}</div>
            )}
          </Panel>
          {q.data!.past.length > 0 && (
            <Panel title={t("market.pastLessons")} testId="lessons-past">
              <ul className="space-y-1 text-sm text-text-secondary">
                {q.data!.past.map((l) => <li key={l.id}>{l.title} — {l.teacher.name} · {formatDate(l.starts_at, "de")}</li>)}
              </ul>
            </Panel>
          )}
        </div>
      )}
    </div>
  );
}

/** Compact strip for the Global Chat panel: live lessons first, then the next two; Join opens the meeting page. */
export function LiveLessonsStrip() {
  const { t } = useTranslation();
  const q = useLessonBoard();
  // the panel is small: live lessons (at most two), otherwise only the next one
  const live = q.data?.live ?? [];
  const items = live.length ? live.slice(0, 2) : (q.data?.upcoming ?? []).slice(0, 1);
  if (!items.length) return null;
  return (
    <div className="space-y-2 border-b border-surface-border bg-accent-blue/5 px-3 py-2" data-testid="chat-live-lessons">
      <div className="flex items-center justify-between">
        <p className="inline-flex items-center gap-1 text-xs font-bold uppercase tracking-wide text-accent-blue"><Radio size={12} /> {t("market.liveTitle")}</p>
        <Link href="/my-teacher/live" className="text-xs font-semibold text-accent-blue">{t("market.details")}</Link>
      </div>
      {items.map((l) => <LessonCard key={l.id} lesson={l} compact />)}
    </div>
  );
}
