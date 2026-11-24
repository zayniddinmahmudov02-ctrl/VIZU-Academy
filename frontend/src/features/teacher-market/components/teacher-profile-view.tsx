"use client";

import { useState } from "react";
import { useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Award, BookOpen, Briefcase, FileText, Flag, GraduationCap, Languages, Users } from "lucide-react";

import { EmptyState, Panel } from "@/components/teacher/teacher-ui";
import { useTranslation } from "@/lib/i18n/use-translation";

import { certificateBlobUrl, createReview, getTeacherReviews, reportReview, updateReview } from "../services/market-service";
import type { Review, TeacherProfileView } from "../types";
import { CourseCard, CourseDialog } from "./course-dialog";
import { Modal, Pill, StarInput, Stars, TeacherPhoto, VerifiedBadge, buttonPrimary, buttonSecondary, formatDate, inputClass, useErrorText } from "./ui";

function Fact({ icon: Icon, label, value }: { icon: typeof Users; label: string; value: string | number | null | undefined }) {
  if (value === null || value === undefined || value === "") return null;
  return (
    <div className="flex gap-3">
      <Icon size={18} className="mt-0.5 shrink-0 text-accent-blue" aria-hidden />
      <div className="min-w-0">
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">{label}</p>
        <p className="whitespace-pre-line text-sm text-text-primary">{value}</p>
      </div>
    </div>
  );
}

function ReviewItem({ review, canReport, onReport }: { review: Review; canReport: boolean; onReport: (r: Review) => void }) {
  const { t, language } = useTranslation();
  return (
    <li className="rounded-2xl bg-surface-bg p-4 ring-1 ring-surface-border" data-testid="review-item">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-semibold text-text-primary" data-testid="review-author">{review.author}</span>
          {review.verified_enrollment && <Pill tone="APPROVED">{t("market.verifiedEnrollment")}</Pill>}
        </div>
        <Stars value={review.rating} />
      </div>
      {review.body && <p className="mt-2 whitespace-pre-line text-sm text-text-secondary">{review.body}</p>}
      <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs text-text-muted">
        <span>{review.course.title} · {formatDate(review.created_at, language)}{review.edited_at ? ` · ${t("market.edited")}` : ""}</span>
        {canReport && (
          <button type="button" className="inline-flex items-center gap-1 hover:text-danger" onClick={() => onReport(review)} data-testid="review-report">
            <Flag size={12} /> {t("market.report")}
          </button>
        )}
      </div>
    </li>
  );
}

function ReviewForm({ profile }: { profile: TeacherProfileView }) {
  const { t } = useTranslation();
  const errorText = useErrorText();
  const qc = useQueryClient();
  const options = profile.review;
  const existing = options?.my_reviews.find((r) => r.status !== "hidden") ?? null;
  const [courseId, setCourseId] = useState(options?.can_review[0]?.course_id ?? "");
  const [rating, setRating] = useState(existing?.rating ?? 0);
  const [body, setBody] = useState(existing?.body ?? "");
  const [editing, setEditing] = useState<Review | null>(null);
  const [done, setDone] = useState(false);
  const save = useMutation({
    mutationFn: () => (editing ? updateReview(editing.id, { rating, body }) : createReview({ course_id: courseId, rating, body: body || undefined })),
    onSuccess: () => {
      setDone(true);
      setEditing(null);
      void qc.invalidateQueries({ queryKey: ["teacher-profile", profile.id] });
      void qc.invalidateQueries({ queryKey: ["teacher-reviews", profile.id] });
    },
  });
  if (!options) return null;
  if (!options.can_review.length && !options.my_reviews.length) {
    return <p className="text-xs text-text-muted" data-testid="review-hint">{t("market.reviewHint")}</p>;
  }
  const showForm = editing || options.can_review.length > 0;
  return (
    <div className="space-y-3 rounded-2xl bg-accent-blue/5 p-4 ring-1 ring-accent-blue/15" data-testid="review-form">
      {options.my_reviews.map((r) => (
        <div key={r.id} className="flex flex-wrap items-center justify-between gap-2 text-sm">
          <span className="text-text-secondary">{r.course.title}: <Stars value={r.rating} size={14} /></span>
          {r.status !== "hidden" && (
            <button type="button" className="text-xs font-semibold text-accent-blue" data-testid="review-edit"
                    onClick={() => { setEditing(r); setRating(r.rating); setBody(r.body ?? ""); setDone(false); }}>{t("market.editReview")}</button>
          )}
        </div>
      ))}
      {showForm && (
        <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); save.mutate(); }}>
          <p className="text-sm font-semibold text-text-primary">{editing ? t("market.editReview") : t("market.writeReview")}</p>
          {!editing && options.can_review.length > 1 && (
            <select className={inputClass} value={courseId} onChange={(e) => setCourseId(e.target.value)} aria-label={t("market.reviewCourse")}>
              {options.can_review.map((c) => <option key={c.course_id} value={c.course_id}>{c.title}</option>)}
            </select>
          )}
          <StarInput value={rating} onChange={setRating} />
          <textarea className={inputClass} rows={3} maxLength={2000} value={body} onChange={(e) => setBody(e.target.value)} placeholder={t("market.reviewText")}
                    data-testid="review-body" />
          {save.isError && <p className="text-sm text-danger" role="alert">{errorText(save.error)}</p>}
          <button type="submit" className={buttonPrimary} disabled={rating < 1 || save.isPending} data-testid="review-save">{t("market.reviewSave")}</button>
        </form>
      )}
      {done && <p className="text-sm text-emerald-600" role="status" data-testid="review-saved">{t("market.reviewSaved")}</p>}
    </div>
  );
}

const count = (n: number) => new Intl.NumberFormat("ru-RU").format(n);

/** Students: the career figure (the teacher's own number incl. before VIZU — labelled so — never below the VIZU total) and the
 *  VIZU numbers computed by the server (all students ever on VIZU, of them active now). */
export function StudentStats({ stats }: { stats: TeacherProfileView["stats"] }) {
  const { t } = useTranslation();
  return (
    <div className="grid grid-cols-2 gap-3" data-testid="profile-stats">
      <div className="rounded-2xl bg-surface-bg p-4 ring-1 ring-surface-border">
        <p className="text-2xl font-extrabold text-text-primary" data-testid="stat-career">{count(stats.career_students)}</p>
        <p className="text-xs font-medium text-text-secondary">{t("market.careerStudents")}</p>
        <p className="mt-1 text-[11px] text-text-muted" data-testid="stat-career-source">
          {stats.career_reported ? t("market.careerReported") : t("market.careerFromVizu")}</p>
      </div>
      <div className="rounded-2xl bg-surface-bg p-4 ring-1 ring-surface-border">
        <p className="text-2xl font-extrabold text-text-primary" data-testid="stat-total">{count(stats.total_students)}</p>
        <p className="text-xs font-medium text-text-secondary">{t("market.vizuStudents")}</p>
        <p className="mt-1 text-[11px] text-text-muted">{t("market.activeNow")}: <span data-testid="stat-current">{count(stats.current_students)}</span></p>
      </div>
    </div>
  );
}

/** The public mini profile; `preview` = the teacher looks at the own profile (no actions). */
export default function TeacherProfileView({ profile, preview = false }: { profile: TeacherProfileView; preview?: boolean }) {
  const { t, language } = useTranslation();
  const errorText = useErrorText();
  const [openCourse, setOpenCourse] = useState<string | null>(null);
  const [reporting, setReporting] = useState<Review | null>(null);
  const [reason, setReason] = useState("");
  const [reported, setReported] = useState(false);
  const reviews = useInfiniteQuery({
    queryKey: ["teacher-reviews", profile.id],
    queryFn: ({ pageParam }) => getTeacherReviews(profile.id, pageParam),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page * last.page_size < last.total ? last.page + 1 : undefined),
    enabled: !preview,
  });
  const report = useMutation({ mutationFn: () => reportReview(reporting!.id, reason), onSuccess: () => { setReported(true); setReason(""); } });
  const items = reviews.data?.pages.flatMap((p) => p.items) ?? [];
  const course = profile.courses.find((c) => c.id === openCourse) ?? null;
  const exp = profile.experience;

  const openCert = async (url: string) => {
    const win = window.open("", "_blank");
    try {
      const blob = await certificateBlobUrl(url);
      if (win) win.location.href = blob;
    } catch {
      win?.close();
    }
  };

  return (
    <div className="space-y-6" data-testid="teacher-profile">
      <section className="grid gap-6 rounded-3xl bg-surface-card p-4 shadow-[var(--shadow-md)] ring-1 ring-surface-border sm:p-6 md:grid-cols-[minmax(0,260px)_minmax(0,1fr)]">
        <div className="mx-auto w-full max-w-[260px]"><TeacherPhoto url={profile.photo_url} name={profile.name} /></div>
        <div className="min-w-0 space-y-4">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-extrabold tracking-tight text-text-primary sm:text-3xl" data-testid="profile-name">{profile.name}</h1>
              {profile.verified && <VerifiedBadge />}
            </div>
            {profile.headline && <p className="mt-1 text-base text-text-secondary" data-testid="profile-headline">{profile.headline}</p>}
          </div>
          <div className="flex flex-wrap items-center gap-3" data-testid="profile-rating">
            {profile.rating.count > 0 ? (
              <>
                <Stars value={profile.rating.avg} size={20} />
                <span className="text-lg font-bold text-text-primary">{profile.rating.avg.toFixed(1)}/5</span>
                <span className="text-sm text-text-muted">{t("market.ratingCount", { n: profile.rating.count })}</span>
              </>
            ) : <span className="text-sm text-text-muted">{t("market.noRating")}</span>}
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <Fact icon={Languages} label={t("market.languages")} value={profile.languages.join(", ")} />
            <Fact icon={GraduationCap} label={t("market.levels")} value={profile.levels.join(", ")} />
          </div>
          <StudentStats stats={profile.stats} />
        </div>
      </section>

      <Panel title={t("market.experienceTitle")} testId="profile-experience">
        <div className="grid gap-4 md:grid-cols-2">
          <Fact icon={Briefcase} label={t("market.experienceTitle")} value={[exp.years != null ? t("market.years", { n: exp.years }) : null,
            exp.teaching_since ? t("market.since", { year: exp.teaching_since }) : null].filter(Boolean).join(" · ")} />
          <Fact icon={BookOpen} label={t("market.specialization")} value={exp.specialization} />
          <Fact icon={Award} label={t("market.examPrep")} value={exp.exam_prep.join(", ")} />
          <Fact icon={GraduationCap} label={t("market.methodology")} value={exp.methodology} />
          <div className="md:col-span-2"><Fact icon={Users} label={t("market.about")} value={exp.bio} /></div>
        </div>
      </Panel>

      <Panel title={t("market.certificatesTitle")} testId="profile-certificates">
        {profile.certificates.length === 0 ? <p className="text-sm text-text-muted">{t("market.noCertificates")}</p> : (
          <ul className="grid gap-3 sm:grid-cols-2">
            {profile.certificates.map((c) => (
              <li key={c.id} className="flex items-start gap-3 rounded-2xl bg-surface-bg p-4 ring-1 ring-surface-border" data-testid="certificate-item">
                <FileText size={20} className="mt-0.5 shrink-0 text-accent-blue" aria-hidden />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-text-primary">{c.title}</p>
                  <p className="text-xs text-text-secondary">{c.issuer}{c.level ? ` · ${c.level}` : ""}{c.issued_on ? ` · ${formatDate(c.issued_on, language)}` : ""}</p>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    {c.verified ? <Pill tone="APPROVED">{t("market.verifiedCertificate")}</Pill>
                      : c.status ? <Pill tone={c.status === "rejected" ? "REJECTED" : "PENDING"}>{t(`market.cert_${c.status}`)}</Pill> : null}
                    <button type="button" className="text-xs font-semibold text-accent-blue" onClick={() => openCert(c.file_url)}>{t("market.openFile")}</button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Panel>

      <Panel title={t("market.coursesTitle")} testId="profile-courses">
        {profile.courses.length === 0 ? <EmptyState text={t("market.noCourses")} testId="profile-no-courses" /> : (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {profile.courses.map((c) => <CourseCard key={c.id} course={c} onOpen={() => !preview && setOpenCourse(c.id)} />)}
          </div>
        )}
      </Panel>

      <Panel title={t("market.reviewsTitle")} testId="profile-reviews">
        <div className="space-y-4">
          {!preview && <ReviewForm profile={profile} />}
          {preview ? null : items.length === 0 ? <p className="text-sm text-text-muted">{t("market.noReviews")}</p> : (
            <ul className="space-y-3">
              {items.map((r) => <ReviewItem key={r.id} review={r} canReport={!profile.review?.my_reviews.some((m) => m.id === r.id)}
                                              onReport={(x) => { setReporting(x); setReported(false); }} />)}
            </ul>
          )}
          {reviews.hasNextPage && (
            <button type="button" className={buttonSecondary} onClick={() => reviews.fetchNextPage()}>{t("market.loadMore")}</button>
          )}
        </div>
      </Panel>

      <CourseDialog course={course} open={!!course} onClose={() => setOpenCourse(null)} />
      <Modal open={!!reporting} onClose={() => setReporting(null)} title={t("market.report")} testId="report-dialog">
        {reported ? <p className="text-sm text-text-secondary" role="status">{t("market.reported")}</p> : (
          <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); report.mutate(); }}>
            <label className="block text-sm text-text-primary">{t("market.reportReason")}
              <textarea className={inputClass} rows={3} maxLength={500} value={reason} onChange={(e) => setReason(e.target.value)} required minLength={3} />
            </label>
            {report.isError && <p className="text-sm text-danger" role="alert">{errorText(report.error)}</p>}
            <button type="submit" className={buttonPrimary} disabled={report.isPending || reason.trim().length < 3}>{t("market.report")}</button>
          </form>
        )}
      </Modal>
    </div>
  );
}
