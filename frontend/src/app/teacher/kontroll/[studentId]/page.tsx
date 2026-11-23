"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Eye } from "lucide-react";

import { EmptyState, ErrorState, fieldClass, Loading, Panel, StudentStatusBadge, TeacherPageTitle } from "@/components/teacher/teacher-ui";
import ActivityBars, { AREA_COLORS } from "@/features/activity/components/activity-bars";
import { formatDate, formatDateTime, formatDuration } from "@/features/activity/lib/format";
import { useTeacherMe } from "@/features/teacher/hooks/use-teacher-me";
import { getKontrollStudent, getKontrollTimeline } from "@/features/teacher/services/teacher-panel.service";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

const AREAS = ["COURSE", "WORTSCHATZ", "MUSIC", "BOOK", "FILM", "EXAM"];

function Fact({ label, value, testId }: { label: string; value: React.ReactNode; testId?: string }) {
  return (
    <div className="rounded-xl bg-surface-hover/60 p-3" data-testid={testId}>
      <p className="text-xs text-text-muted">{label}</p>
      <p className="mt-0.5 text-base font-semibold text-text-primary">{value}</p>
    </div>
  );
}

function Timeline({ studentId }: { studentId: string }) {
  const { t, language } = useTranslation();
  const [day, setDay] = useState<string | undefined>(undefined);
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ["kontroll-timeline", studentId, day], queryFn: () => getKontrollTimeline(studentId, day) });
  return (
    <Panel title={t("tpanel.kTimeline")} testId="kontroll-timeline"
           actions={data && data.days.length > 0 ? (
             <select value={day ?? data.day ?? ""} onChange={(e) => setDay(e.target.value)} aria-label={t("tpanel.kDay")} className={fieldClass} data-testid="kontroll-day">
               {data.days.map((d) => <option key={d} value={d}>{formatDate(d, language)}</option>)}
             </select>
           ) : undefined}>
      {isLoading && <Loading />}
      {isError && <ErrorState onRetry={() => refetch()} />}
      {data && data.items.length === 0 && <p className="text-sm text-text-muted">{data.day ? t("tpanel.kNoTimeline") : t("tpanel.emptyActivity")}</p>}
      {data && data.items.length > 0 && (
        <ol className="relative space-y-3 border-l border-surface-border pl-5">
          {data.items.map((i) => (
            <li key={i.id} className="relative" data-testid="timeline-item">
              <span className={cn("absolute -left-[26px] top-1 h-3 w-3 rounded-full ring-2 ring-surface-card", AREA_COLORS[i.area])} aria-hidden />
              <p className="text-sm text-text-primary">
                <span className="font-mono font-semibold">{i.time}</span>
                {" — "}{i.area === "COURSE" && i.title ? i.title : `${t(`tpanel.area_${i.area}`)}${i.title ? ` — ${i.title}` : ""}`}
                <span className="text-text-muted">{" — "}{formatDuration(i.seconds, language)}</span>
              </p>
            </li>
          ))}
        </ol>
      )}
    </Panel>
  );
}

export default function KontrollStudentPage() {
  const { studentId } = useParams<{ studentId: string }>();
  const { t, language } = useTranslation();
  const me = useTeacherMe();
  const allowed = !!me.data?.can_access_student_control;
  const { data, isLoading, isError, error, refetch } = useQuery({ queryKey: ["kontroll-student", studentId], queryFn: () => getKontrollStudent(studentId), enabled: allowed, retry: false });
  const status = (error as { response?: { status?: number } } | null)?.response?.status;

  if (me.isLoading) return <Loading />;
  if (!allowed) return <EmptyState text={t("tpanel.kNoAccess")} testId="kontroll-denied" />;

  return (
    <div data-testid="kontroll-student">
      <Link href="/teacher/kontroll" className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary hover:text-accent-blue"><ArrowLeft size={16} /> {t("tpanel.back")}</Link>
      {isLoading && <Loading />}
      {isError && (status === 404 ? <EmptyState text={t("tpanel.emptyStudents")} /> : <ErrorState onRetry={() => refetch()} />)}
      {data && (
        <div className="space-y-4">
          <TeacherPageTitle title={data.student.name} subtitle={`${data.student.email} · ${t("tpanel.colRegistered")}: ${formatDate(data.student.registered_at, language)}`}
                            actions={<StudentStatusBadge status={data.student.status} />} />
          <p className="flex items-center gap-2 text-xs text-text-muted"><Eye size={14} /> {t("tpanel.kReadOnly")}</p>

          <Panel title={t("tpanel.kGeneral")} testId="kontroll-general">
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <Fact label={t("tpanel.kTotal")} value={formatDuration(data.general.total_seconds, language)} testId="k-total" />
              <Fact label={t("tpanel.kToday")} value={formatDuration(data.general.today_seconds, language)} />
              <Fact label={t("tpanel.kWeek")} value={formatDuration(data.general.week_seconds, language)} />
              <Fact label={t("tpanel.kMonth")} value={formatDuration(data.general.month_seconds, language)} />
              <Fact label={t("tpanel.kActiveDays")} value={data.general.active_days} />
              <Fact label={t("tpanel.kLastLogin")} value={data.general.last_login_at ? formatDateTime(data.general.last_login_at, language) : t("tpanel.never")} />
              <Fact label={t("tpanel.kLastActivity")} value={data.general.last_activity_at ? formatDateTime(data.general.last_activity_at, language) : t("tpanel.never")} />
              <Fact label={t("tpanel.kTrackingSince")} value={data.general.tracking_since ? formatDate(data.general.tracking_since, language) : "—"} />
            </div>
            {!data.general.tracking_since && <p className="mt-3 text-xs text-text-muted">{t("tpanel.kNotYet")}</p>}
          </Panel>

          <ActivityBars days={data.daily} language={language} title={t("tpanel.kChart")} tableLabel={t("tpanel.kTable")} emptyLabel={t("tpanel.kChartEmpty")}
                        series={AREAS.map((a) => ({ key: a, label: t(`tpanel.area_${a}`) }))} testId="kontroll-chart" />

          <Panel title={t("tpanel.kCourses")} testId="kontroll-courses">
            {data.courses.length === 0 ? <p className="text-sm text-text-muted">{t("tpanel.noProgress")}</p> : (
              <ul className="space-y-3">
                {data.courses.map((c) => (
                  <li key={c.course_id}>
                    <div className="flex flex-wrap items-baseline justify-between gap-2 text-sm">
                      <span className="font-semibold text-text-primary">{c.level} — {t("tpanel.lessonsOf", { done: c.lessons_completed, total: c.lessons_total })} — {c.percent}%</span>
                      <span className="text-xs text-text-muted">{c.title}</span>
                    </div>
                    <div className="mt-1 h-2 overflow-hidden rounded-full bg-surface-hover" role="progressbar" aria-valuenow={c.percent} aria-valuemin={0} aria-valuemax={100}>
                      <div className="h-full rounded-full bg-accent-blue" style={{ width: `${c.percent}%` }} />
                    </div>
                    <p className="mt-1 text-xs text-text-muted">
                      {c.started_at ? t("tpanel.kStarted", { date: formatDate(c.started_at, language) }) : ""}
                      {c.last_lesson ? ` · ${t("tpanel.lastLesson", { n: c.last_lesson.number })} (${formatDateTime(c.last_lesson.at, language)})` : ""}
                      {` · ${t("tpanel.kTimeSpent", { time: formatDuration(c.seconds, language) })}`}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </Panel>

          <div className="grid gap-4 lg:grid-cols-2">
            <Panel title={t("tpanel.kMusic")} testId="kontroll-music">
              <div className="mb-3 grid grid-cols-3 gap-2">
                <Fact label={t("tpanel.kSongsCount")} value={data.music.songs_listened} />
                <Fact label={t("mstats.listened")} value={formatDuration(data.music.listened_seconds, language)} />
                <Fact label={t("tpanel.kLastSong")} value={<span className="text-sm">{data.music.last?.title ?? "—"}</span>} />
              </div>
              <ul className="max-h-64 space-y-1 overflow-y-auto text-sm">
                {data.music.history.map((s) => (
                  <li key={s.id} className="flex justify-between gap-2"><span className="truncate text-text-primary">{s.title}{s.artist ? <span className="text-text-muted"> · {s.artist}</span> : null}</span>
                    <span className="shrink-0 text-xs text-text-muted">{s.play_count}× · {formatDuration(s.listened_seconds, language)} · {formatDate(s.last_listened_at, language)}</span></li>
                ))}
              </ul>
            </Panel>

            <Panel title={t("tpanel.kVocab")} testId="kontroll-vocab">
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                <Fact label={t("tpanel.kVocabTime")} value={formatDuration(data.vocabulary.seconds, language)} />
                <Fact label={t("tpanel.kWordsLearned")} value={data.vocabulary.words_learned} />
                <Fact label={t("tpanel.kWordsRepeated")} value={data.vocabulary.words_repeated} />
                <Fact label={t("tpanel.kWordsSaved")} value={data.vocabulary.words_saved} />
                <Fact label={t("tpanel.kBlocks")} value={data.vocabulary.blocks_completed} />
                <Fact label={t("tpanel.kVocabLast")} value={<span className="text-sm">{data.vocabulary.last_activity_at ? formatDateTime(data.vocabulary.last_activity_at, language) : t("tpanel.never")}</span>} />
              </div>
            </Panel>

            <Panel title={t("tpanel.kBooks")} testId="kontroll-books">
              <div className="mb-3 grid grid-cols-2 gap-2">
                <Fact label={t("tpanel.kBooksCount")} value={data.books.books_opened} />
                <Fact label={t("mstats.reading")} value={formatDuration(data.books.reading_seconds, language)} />
              </div>
              <ul className="max-h-64 space-y-1 overflow-y-auto text-sm">
                {data.books.history.map((b) => (
                  <li key={b.id} className="flex justify-between gap-2"><span className="truncate text-text-primary">{b.title}</span>
                    <span className="shrink-0 text-xs text-text-muted">{b.completed ? t("mstats.done") : b.page ? t("mstats.pageOf", { page: b.page, total: b.pages ?? "?" }) : ""} · {formatDuration(b.reading_seconds, language)} · {formatDate(b.last_opened_at, language)}</span></li>
                ))}
              </ul>
            </Panel>

            <Panel title={t("tpanel.kFilms")} testId="kontroll-films">
              <div className="mb-3 grid grid-cols-3 gap-2">
                <Fact label={t("tpanel.kFilmsCount")} value={data.films.films_watched} />
                <Fact label={t("mstats.watching")} value={formatDuration(data.films.watched_seconds, language)} />
                <Fact label={t("tpanel.kLastFilm")} value={<span className="text-sm">{data.films.last?.title ?? "—"}</span>} />
              </div>
              <ul className="max-h-64 space-y-1 overflow-y-auto text-sm">
                {data.films.history.map((f) => (
                  <li key={f.id} className="flex justify-between gap-2"><span className="truncate text-text-primary">{f.title}</span>
                    <span className="shrink-0 text-xs text-text-muted">{formatDuration(f.watched_seconds, language)} · {formatDate(f.last_watched_at, language)}</span></li>
                ))}
              </ul>
            </Panel>
          </div>

          <Timeline studentId={studentId} />
        </div>
      )}
    </div>
  );
}
