"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Flag, Plus, Send, Users, Video } from "lucide-react";

import { EmptyState, ErrorState, Loading, Panel, TeacherPageTitle } from "@/components/teacher/teacher-ui";
import { useTranslation } from "@/lib/i18n/use-translation";

import {
  cancelLesson, createCourse, getCourseStudents, getOwnCourses, getOwnLessons, getOwnReviews, openLessonRoom, requestLesson, submitCourse,
  teacherReportReview, updateCourse, uploadCourseImage, type CourseInput,
} from "../services/market-service";
import { LANGUAGES, LEVELS, TEACHER_STATUSES, WEEKDAYS, type SpecialLesson, type TeacherCourseItem } from "../types";
import RatioCropper from "./ratio-cropper";
import { Modal, Pill, Stars, buttonPrimary, buttonSecondary, formatDate, formatDateTime, formatPrice, inputClass, useErrorText } from "./ui";

// ================= Meine Kurse =================

const EMPTY: CourseInput = { title: "", description: "", language: "Deutsch", level: "A1", course_type: "PAID", price: 0, max_students: 12, status: "VORBEREITUNG",
  weekdays: [], lesson_time: "", start_date: null, end_date: null, enrollment_deadline: null, duration_weeks: null, lessons_per_week: null, lesson_minutes: null };

function CourseForm({ course, onSaved }: { course: TeacherCourseItem | null; onSaved: (c: TeacherCourseItem) => void }) {
  const { t } = useTranslation();
  const errorText = useErrorText();
  const [f, setF] = useState<CourseInput>(course ? {
    title: course.title, description: course.description ?? "", language: course.language, level: course.level, course_type: course.course_type,
    price: course.price, max_students: course.max_students, status: course.teacher_status, weekdays: course.weekdays, lesson_time: course.lesson_time ?? "",
    start_date: course.start_date, end_date: course.end_date, enrollment_deadline: course.enrollment_deadline, duration_weeks: course.duration_weeks,
    lessons_per_week: course.lessons_per_week, lesson_minutes: course.lesson_minutes,
  } : EMPTY);
  const save = useMutation({
    mutationFn: () => {
      const body: CourseInput = { ...f, start_date: f.start_date || null, end_date: f.end_date || null, enrollment_deadline: f.enrollment_deadline || null,
        lesson_time: f.lesson_time || null };
      return course ? updateCourse(course.id, body) : createCourse(body);
    },
    onSuccess: onSaved,
  });
  const num = (k: keyof CourseInput) => (e: React.ChangeEvent<HTMLInputElement>) => setF({ ...f, [k]: e.target.value === "" ? null : Number(e.target.value) });
  const str = (k: keyof CourseInput) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => setF({ ...f, [k]: e.target.value });
  const statuses = f.course_type === "UPCOMING" ? (["BALD", "VORBEREITUNG", "ABGESAGT"] as const) : TEACHER_STATUSES;
  return (
    <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); save.mutate(); }} data-testid="course-form">
      <label className="block text-xs text-text-secondary">{t("market.courseTitle")}<input className={inputClass} value={f.title ?? ""} onChange={str("title")} required minLength={3} maxLength={200} data-testid="cf-title" /></label>
      <label className="block text-xs text-text-secondary">{t("market.description")}<textarea className={inputClass} rows={3} value={f.description ?? ""} onChange={str("description")} maxLength={6000} data-testid="cf-description" /></label>
      <div className="grid gap-3 sm:grid-cols-3">
        <label className="text-xs text-text-secondary">{t("market.courseType")}
          <select className={inputClass} value={f.course_type} onChange={(e) => setF({ ...f, course_type: e.target.value as CourseInput["course_type"],
            status: e.target.value === "UPCOMING" ? "BALD" : f.status })} data-testid="cf-type">
            {(["PAID", "FREE", "UPCOMING"] as const).map((x) => <option key={x} value={x}>{t(`market.type_${x}`)}</option>)}
          </select></label>
        <label className="text-xs text-text-secondary">{t("market.filterLevel")}
          <select className={inputClass} value={f.level} onChange={str("level")} data-testid="cf-level">{LEVELS.map((l) => <option key={l}>{l}</option>)}</select></label>
        <label className="text-xs text-text-secondary">{t("market.filterLanguage")}
          <select className={inputClass} value={f.language} onChange={str("language")}>{LANGUAGES.map((l) => <option key={l}>{l}</option>)}</select></label>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        {f.course_type !== "FREE" && <label className="text-xs text-text-secondary">{t("market.priceUzs")}<input type="number" min={0} step={1000} className={inputClass} value={f.price ?? 0} onChange={num("price")} data-testid="cf-price" /></label>}
        <label className="text-xs text-text-secondary">{t("market.maxStudents")}<input type="number" min={1} max={500} className={inputClass} value={f.max_students ?? 12} onChange={num("max_students")} data-testid="cf-max" /></label>
        <label className="text-xs text-text-secondary">{t("market.publicStatus")}
          <select className={inputClass} value={f.status} onChange={str("status")} data-testid="cf-status">
            {statuses.map((s) => <option key={s} value={s}>{t(`market.status_${s}`)}</option>)}
          </select></label>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <label className="text-xs text-text-secondary">{t("market.startDate")}<input type="date" className={inputClass} value={f.start_date ?? ""} onChange={str("start_date")} data-testid="cf-start" /></label>
        <label className="text-xs text-text-secondary">{t("market.endDate")}<input type="date" className={inputClass} value={f.end_date ?? ""} onChange={str("end_date")} /></label>
        <label className="text-xs text-text-secondary">{t("market.enrollmentDeadline")}<input type="date" className={inputClass} value={f.enrollment_deadline ?? ""} onChange={str("enrollment_deadline")} /></label>
      </div>
      <div className="grid gap-3 sm:grid-cols-4">
        <label className="text-xs text-text-secondary">{t("market.durationWeeks")}<input type="number" min={1} max={104} className={inputClass} value={f.duration_weeks ?? ""} onChange={num("duration_weeks")} /></label>
        <label className="text-xs text-text-secondary">{t("market.lessonsPerWeek")}<input type="number" min={1} max={14} className={inputClass} value={f.lessons_per_week ?? ""} onChange={num("lessons_per_week")} /></label>
        <label className="text-xs text-text-secondary">{t("market.lessonTime")}<input type="time" className={inputClass} value={f.lesson_time ?? ""} onChange={str("lesson_time")} /></label>
        <label className="text-xs text-text-secondary">{t("market.lessonMinutes")}<input type="number" min={15} max={300} className={inputClass} value={f.lesson_minutes ?? ""} onChange={num("lesson_minutes")} /></label>
      </div>
      <div className="space-y-1"><p className="text-xs text-text-secondary">{t("market.weekdays")}</p>
        <div className="flex flex-wrap gap-1.5">
          {WEEKDAYS.map((d) => {
            const on = (f.weekdays ?? []).includes(d);
            return <button key={d} type="button" aria-pressed={on} onClick={() => setF({ ...f, weekdays: on ? (f.weekdays ?? []).filter((x) => x !== d) : [...(f.weekdays ?? []), d] })}
                           className={`h-9 w-11 rounded-lg text-xs font-semibold ring-1 ${on ? "bg-accent-blue text-white ring-accent-blue" : "bg-surface-bg text-text-secondary ring-surface-border"}`}>{d}</button>;
          })}
        </div>
      </div>
      {save.isError && <p className="text-sm text-danger" role="alert">{errorText(save.error)}</p>}
      <button type="submit" className={`${buttonPrimary} w-full`} disabled={save.isPending} data-testid="cf-save">{t("market.save")}</button>
    </form>
  );
}

function Roster({ courseId }: { courseId: string }) {
  const { t, language } = useTranslation();
  const q = useQuery({ queryKey: ["teacher-course-roster", courseId], queryFn: () => getCourseStudents(courseId) });
  if (q.isLoading) return <Loading />;
  if (q.isError || !q.data) return <ErrorState onRetry={() => q.refetch()} />;
  if (!q.data.items.length) return <EmptyState text={t("market.noStudents")} />;
  return (
    <div className="overflow-x-auto" data-testid="course-roster">
      <table className="w-full min-w-[560px] text-left text-sm">
        <thead className="text-xs uppercase text-text-muted"><tr>
          <th className="py-2 pr-3">{t("market.students")}</th><th className="py-2 pr-3">{t("market.enrolledAt")}</th>
          <th className="py-2 pr-3">{t("market.payment")}</th><th className="py-2 pr-3">{t("market.attendance")}</th><th className="py-2">Status</th>
        </tr></thead>
        <tbody>
          {q.data.items.map((r) => (
            <tr key={r.id} className="border-t border-surface-border" data-testid="roster-row">
              <td className="py-2 pr-3 font-medium text-text-primary">{r.student.name}</td>
              <td className="py-2 pr-3 text-text-secondary">{formatDate(r.enrolled_at, language)}</td>
              <td className="py-2 pr-3 text-text-secondary">{r.payment ? `${r.payment.status}${r.payment.amount ? ` · ${formatPrice(r.payment.amount)}` : ""}` : "—"}</td>
              <td className="py-2 pr-3 text-text-secondary">{r.attendance.attended} / {r.attendance.held}</td>
              <td className="py-2"><Pill tone={r.status === "ACTIVE" ? "APPROVED" : r.status === "PENDING_PAYMENT" ? "PENDING" : "REJECTED"}>{t(`market.enrollmentStatus_${r.status}`)}</Pill></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function TeacherCoursesManager() {
  const { t, language } = useTranslation();
  const errorText = useErrorText();
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["teacher-market-courses"], queryFn: getOwnCourses });
  const [editing, setEditing] = useState<TeacherCourseItem | "new" | null>(null);
  const [roster, setRoster] = useState<TeacherCourseItem | null>(null);
  const [notice, setNotice] = useState("");
  const refresh = () => void qc.invalidateQueries({ queryKey: ["teacher-market-courses"] });
  const submit = useMutation({ mutationFn: (id: string) => submitCourse(id), onSuccess: refresh });
  const image = useMutation({ mutationFn: ({ id, file, crop }: { id: string; file: File; crop: { x: number; y: number; w: number } }) => uploadCourseImage(id, file, crop),
                              onSuccess: refresh });
  return (
    <div data-testid="teacher-courses-manager">
      <TeacherPageTitle title={t("market.coursesManageTitle")} subtitle={t("market.coursesManageSubtitle")} actions={
        <button type="button" className={buttonPrimary} onClick={() => setEditing("new")} data-testid="course-new"><Plus size={16} /> {t("market.newCourse")}</button>
      } />
      {notice && <p className="mb-4 rounded-xl bg-amber-500/10 px-3 py-2 text-sm text-amber-700 dark:text-amber-300" role="status">{notice}</p>}
      {submit.isError && <p className="mb-4 text-sm text-danger" role="alert">{errorText(submit.error)}</p>}
      {q.isLoading ? <Loading /> : q.isError ? <ErrorState onRetry={() => q.refetch()} /> : !q.data?.length ? <EmptyState text={t("market.noOwnCourses")} /> : (
        <ul className="space-y-3">
          {q.data.map((c) => (
            <li key={c.id} className="rounded-2xl bg-surface-card p-4 shadow-[var(--shadow-md)] ring-1 ring-surface-border" data-testid="own-course">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="font-bold text-text-primary" data-testid="own-course-title">{c.title}</p>
                  <p className="text-sm text-text-secondary">{c.level} · {t(`market.type_${c.course_type}`)}{c.course_type === "PAID" ? ` · ${formatPrice(c.price)} so'm` : ""}
                    {" · "}{formatDate(c.start_date, language)} · {t("market.seats", { taken: c.enrolled, max: c.max_students })}
                    {c.interests ? ` · ${t("market.interests", { n: c.interests })}` : ""}</p>
                  {c.reject_reason && ["REJECTED", "UNPUBLISHED"].includes(c.approval_status) && <p className="text-xs text-danger">{c.reject_reason}</p>}
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Pill tone={c.approval_status} testId="own-course-approval">{t(`market.approval_${c.approval_status}`)}</Pill>
                  <Pill tone={c.status}>{t(`market.status_${c.status}`)}</Pill>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <button type="button" className={buttonSecondary} onClick={() => setEditing(c)} data-testid="own-course-edit">{t("market.editCourse")}</button>
                {["DRAFT", "REJECTED", "UNPUBLISHED"].includes(c.approval_status) && (
                  <button type="button" className={buttonPrimary} onClick={() => submit.mutate(c.id)} disabled={submit.isPending} data-testid="own-course-submit">
                    <Send size={16} /> {t("market.submit")}</button>
                )}
                <button type="button" className={buttonSecondary} onClick={() => setRoster(c)} data-testid="own-course-roster"><Users size={16} /> {t("market.students")}</button>
                {c.group_id && <Link href={`/teacher/groups/${c.group_id}`} className={buttonSecondary}>{t("market.toClassroom")}</Link>}
              </div>
            </li>
          ))}
        </ul>
      )}
      <Modal open={editing !== null} onClose={() => setEditing(null)} title={editing === "new" ? t("market.newCourse") : t("market.editCourse")} wide testId="course-editor">
        {editing !== null && (
          <div className="space-y-6">
            <CourseForm course={editing === "new" ? null : editing} onSaved={(c) => {
              refresh();
              setNotice(c.needs_review ? t("market.needsReview") : t("market.saved"));
              setEditing(editing === "new" ? c : null);
            }} />
            {editing !== "new" && (
              <div className="space-y-2 border-t border-surface-border pt-4">
                <p className="text-sm font-semibold text-text-primary">{t("market.courseImage")}</p>
                <RatioCropper ratio={16 / 9} busy={image.isPending} onSave={(file, crop) => image.mutate({ id: editing.id, file, crop })} testId="course-image" />
                {image.isError && <p className="text-sm text-danger" role="alert">{errorText(image.error)}</p>}
              </div>
            )}
          </div>
        )}
      </Modal>
      <Modal open={!!roster} onClose={() => setRoster(null)} title={`${t("market.rosterTitle")}: ${roster?.title ?? ""}`} wide testId="roster-dialog">
        {roster && <Roster courseId={roster.id} />}
      </Modal>
    </div>
  );
}

// ================= Spezialstunden =================

function toLocalInput(d: Date) {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function LessonForm({ onDone }: { onDone: () => void }) {
  const { t } = useTranslation();
  const errorText = useErrorText();
  // lazy initial state: the default start (tomorrow, same time + 2 h) is computed once, not on every render
  const [f, setF] = useState(() => ({ title: "", topic: "", description: "", objectives: "", language: "Deutsch", level: "A2",
    starts_at: toLocalInput(new Date(Date.now() + 26 * 3600_000)), duration_minutes: 60, max_participants: 50 }));
  const send = useMutation({ mutationFn: () => requestLesson({ ...f, starts_at: new Date(f.starts_at).toISOString() }), onSuccess: onDone });
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setF({ ...f, [k]: ["duration_minutes", "max_participants"].includes(k) ? Number(e.target.value) : e.target.value });
  return (
    <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); send.mutate(); }} data-testid="lesson-form">
      <label className="block text-xs text-text-secondary">{t("market.lessonTitle")}<input className={inputClass} value={f.title} onChange={set("title")} required minLength={3} maxLength={200} data-testid="lf-title" /></label>
      <label className="block text-xs text-text-secondary">{t("market.topic")}<input className={inputClass} value={f.topic} onChange={set("topic")} required minLength={2} maxLength={200} data-testid="lf-topic" /></label>
      <label className="block text-xs text-text-secondary">{t("market.description")}<textarea className={inputClass} rows={3} value={f.description} onChange={set("description")} maxLength={4000} /></label>
      <label className="block text-xs text-text-secondary">{t("market.objectives")}<textarea className={inputClass} rows={2} value={f.objectives} onChange={set("objectives")} maxLength={2000} /></label>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="text-xs text-text-secondary">{t("market.filterLanguage")}<select className={inputClass} value={f.language} onChange={set("language")}>{LANGUAGES.map((l) => <option key={l}>{l}</option>)}</select></label>
        <label className="text-xs text-text-secondary">{t("market.filterLevel")}<select className={inputClass} value={f.level} onChange={set("level")} data-testid="lf-level">{LEVELS.map((l) => <option key={l}>{l}</option>)}</select></label>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <label className="text-xs text-text-secondary">{t("market.lessonStart")}<input type="datetime-local" className={inputClass} value={f.starts_at} onChange={set("starts_at")} required data-testid="lf-start" /></label>
        <label className="text-xs text-text-secondary">{t("market.lessonDuration")}<input type="number" min={15} max={90} className={inputClass} value={f.duration_minutes} onChange={set("duration_minutes")} required data-testid="lf-duration" /></label>
        <label className="text-xs text-text-secondary">{t("market.lessonMax")}<input type="number" min={2} max={500} className={inputClass} value={f.max_participants} onChange={set("max_participants")} required data-testid="lf-max" /></label>
      </div>
      {send.isError && <p className="text-sm text-danger" role="alert">{errorText(send.error)}</p>}
      <button type="submit" className={`${buttonPrimary} w-full`} disabled={send.isPending} data-testid="lf-submit">{t("market.sendRequest")}</button>
    </form>
  );
}

function OwnLesson({ lesson }: { lesson: SpecialLesson }) {
  const { t, language } = useTranslation();
  const errorText = useErrorText();
  const router = useRouter();
  const qc = useQueryClient();
  const open = useMutation({ mutationFn: () => openLessonRoom(lesson.id), onSuccess: (r) => router.push(`/video-room/${r.room_id}`) });
  const cancel = useMutation({ mutationFn: () => cancelLesson(lesson.id), onSuccess: () => void qc.invalidateQueries({ queryKey: ["teacher-special-lessons"] }) });
  const live = lesson.room?.status === "live";
  return (
    <li className="rounded-2xl bg-surface-card p-4 shadow-[var(--shadow-md)] ring-1 ring-surface-border" data-testid="own-lesson">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="font-bold text-text-primary">{lesson.title}</p>
          <p className="text-sm text-text-secondary">{formatDateTime(lesson.starts_at, language)} · {t("market.minutes", { n: lesson.duration_minutes })} · {lesson.level}
            {" · "}{t("market.participants", { n: lesson.signups })}</p>
          {(lesson.reject_reason || lesson.cancel_reason) && <p className="text-xs text-danger">{lesson.reject_reason ?? lesson.cancel_reason}</p>}
        </div>
        <Pill tone={lesson.status} testId="own-lesson-status">{t(`market.lessonStatus_${lesson.status}`)}</Pill>
      </div>
      {lesson.status === "APPROVED" && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {live || lesson.can_open ? (
            <button type="button" className={buttonPrimary} onClick={() => open.mutate()} disabled={open.isPending} data-testid="lesson-open">
              <Video size={16} /> {live ? t("market.enterRoom") : t("market.openRoom")}</button>
          ) : <span className="text-xs text-text-muted" data-testid="lesson-opens-at">{t("market.opensAt", { time: formatDateTime(lesson.opens_at, language) })}</span>}
          {!live && <button type="button" className={buttonSecondary} onClick={() => cancel.mutate()} disabled={cancel.isPending}>{t("market.cancelLesson")}</button>}
        </div>
      )}
      {lesson.status === "PENDING" && (
        <button type="button" className={`${buttonSecondary} mt-3`} onClick={() => cancel.mutate()} disabled={cancel.isPending}>{t("market.cancelLesson")}</button>
      )}
      {(open.isError || cancel.isError) && <p className="mt-2 text-sm text-danger" role="alert">{errorText(open.error ?? cancel.error)}</p>}
    </li>
  );
}

export function TeacherSpecialLessons() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["teacher-special-lessons"], queryFn: getOwnLessons, refetchInterval: 30_000 });
  const [form, setForm] = useState(false);
  return (
    <div data-testid="teacher-special-lessons">
      <TeacherPageTitle title={t("market.specialTitle")} subtitle={t("market.specialSubtitle")} actions={
        <button type="button" className={buttonPrimary} onClick={() => setForm(true)} data-testid="lesson-new"><Plus size={16} /> {t("market.requestLesson")}</button>
      } />
      <p className="mb-4 text-xs text-text-muted">{t("market.windowNote", { n: 90 })}</p>
      {q.isLoading ? <Loading /> : q.isError ? <ErrorState onRetry={() => q.refetch()} /> : !q.data?.length ? <EmptyState text={t("market.noOwnLessons")} /> : (
        <ul className="space-y-3">{q.data.map((l) => <OwnLesson key={l.id} lesson={l} />)}</ul>
      )}
      <Modal open={form} onClose={() => setForm(false)} title={t("market.requestLesson")} wide testId="lesson-dialog">
        <LessonForm onDone={() => { setForm(false); void qc.invalidateQueries({ queryKey: ["teacher-special-lessons"] }); }} />
      </Modal>
    </div>
  );
}

// ================= Bewertungen =================

export function TeacherReviews() {
  const { t, language } = useTranslation();
  const errorText = useErrorText();
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["teacher-own-reviews"], queryFn: getOwnReviews });
  const [reporting, setReporting] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const report = useMutation({ mutationFn: () => teacherReportReview(reporting!, reason),
                               onSuccess: () => { setReporting(null); setReason(""); void qc.invalidateQueries({ queryKey: ["teacher-own-reviews"] }); } });
  return (
    <div data-testid="teacher-reviews">
      <TeacherPageTitle title={t("market.reviewsManageTitle")} subtitle={t("market.reviewsManageSubtitle")} />
      {q.isLoading ? <Loading /> : q.isError || !q.data ? <ErrorState onRetry={() => q.refetch()} /> : (
        <div className="space-y-4">
          <Panel title={t("market.ratingTitle")}>
            <div className="flex items-center gap-3"><Stars value={q.data.rating.avg} size={20} />
              <span className="font-bold text-text-primary" data-testid="own-rating-value">{q.data.rating.count ? `${q.data.rating.avg.toFixed(1)}/5` : "—"}</span>
              <span className="text-sm text-text-muted">{t("market.ratingCount", { n: q.data.rating.count })}</span></div>
            <p className="mt-2 text-xs text-text-muted">{t("market.ratingReadOnly")}</p>
          </Panel>
          {!q.data.items.length ? <EmptyState text={t("market.noReviews")} /> : (
            <ul className="space-y-3">
              {q.data.items.map((r) => (
                <li key={r.id} className="rounded-2xl bg-surface-card p-4 ring-1 ring-surface-border" data-testid="teacher-review">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-sm font-semibold text-text-primary">{r.author} · {r.course.title}</span><Stars value={r.rating} />
                  </div>
                  {r.body && <p className="mt-2 whitespace-pre-line text-sm text-text-secondary">{r.body}</p>}
                  <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs text-text-muted">
                    <span>{formatDate(r.created_at, language)}{r.status === "hidden" ? ` · ${t("market.hiddenByAdmin")}` : ""}</span>
                    {r.reported_by_me ? <span>{t("market.reportedByMe")}</span> : r.status === "visible" && (
                      <button type="button" className="inline-flex items-center gap-1 hover:text-danger" onClick={() => setReporting(r.id)} data-testid="teacher-review-report">
                        <Flag size={12} /> {t("market.report")}</button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
      <Modal open={!!reporting} onClose={() => setReporting(null)} title={t("market.report")}>
        <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); report.mutate(); }}>
          <label className="block text-sm text-text-primary">{t("market.reportReason")}
            <textarea className={inputClass} rows={3} maxLength={500} value={reason} onChange={(e) => setReason(e.target.value)} required minLength={3} /></label>
          {report.isError && <p className="text-sm text-danger" role="alert">{errorText(report.error)}</p>}
          <button type="submit" className={buttonPrimary} disabled={report.isPending || reason.trim().length < 3}>{t("market.report")}</button>
        </form>
      </Modal>
    </div>
  );
}
