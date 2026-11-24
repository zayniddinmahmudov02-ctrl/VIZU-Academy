"use client";

/* eslint-disable @next/next/no-img-element -- course images are our own re-encoded WebP files in /uploads */
import { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarDays, CheckCircle2, Clock, Copy, Users } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { resolveMediaUrl } from "@/lib/media";

import { enrollFree, getCheckout, payCourse, setInterest } from "../services/market-service";
import type { CourseItem } from "../types";
import { Modal, Pill, buttonPrimary, buttonSecondary, formatDate, formatPrice, inputClass, useErrorText } from "./ui";

export function CourseCard({ course, onOpen }: { course: CourseItem; onOpen: () => void }) {
  const { t, language } = useTranslation();
  const img = resolveMediaUrl(course.image_url);
  return (
    <article className="flex flex-col overflow-hidden rounded-2xl bg-surface-card shadow-[var(--shadow-md)] ring-1 ring-surface-border" data-testid="course-card">
      <div className="relative aspect-video bg-gradient-to-br from-brand-700/30 to-brand-900/50">
        {img && <img src={img} alt="" className="absolute inset-0 h-full w-full object-cover" loading="lazy" />}
        <span className="absolute left-3 top-3 rounded-full bg-black/60 px-2.5 py-0.5 text-xs font-bold text-white">{course.level}</span>
      </div>
      <div className="flex flex-1 flex-col gap-2 p-4">
        <div className="flex flex-wrap items-center gap-2">
          <Pill tone={course.status} testId="course-status">{t(`market.status_${course.status}`)}</Pill>
          {course.my_enrollment && ["ACTIVE", "PENDING_PAYMENT", "COMPLETED"].includes(course.my_enrollment.status) && (
            <Pill tone="APPROVED">{t(`market.enrollmentStatus_${course.my_enrollment.status}`)}</Pill>
          )}
        </div>
        <h3 className="text-base font-bold text-text-primary" data-testid="course-title">{course.title}</h3>
        <p className="text-sm text-text-secondary">
          {course.language} · {course.start_date ? formatDate(course.start_date, language) : "—"} · {t("market.seats", { taken: course.enrolled, max: course.max_students })}
        </p>
        <div className="mt-auto flex items-center justify-between gap-2 pt-2">
          <span className="text-base font-extrabold text-text-primary" data-testid="course-price">
            {course.course_type === "FREE" ? t("market.free") : t("market.price", { price: formatPrice(course.price) })}
          </span>
          <button type="button" onClick={onOpen} className={buttonSecondary} data-testid="course-open">{t("market.details")}</button>
        </div>
      </div>
    </article>
  );
}

function PaymentForm({ course, onDone }: { course: CourseItem; onDone: () => void }) {
  const { t } = useTranslation();
  const errorText = useErrorText();
  const qc = useQueryClient();
  const checkout = useQuery({ queryKey: ["course-checkout", course.id], queryFn: () => getCheckout(course.id) });
  const [noReceipt, setNoReceipt] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [paidDate, setPaidDate] = useState("");
  const [paidTime, setPaidTime] = useState("");
  const [note, setNote] = useState("");
  const [copied, setCopied] = useState("");
  const pay = useMutation({
    mutationFn: () => payCourse(course.id, { noReceipt, paidDate: paidDate || undefined, paidTime: paidTime || undefined, note: note || undefined,
                                            proof: noReceipt ? null : file }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["teacher-profile"] });
      void qc.invalidateQueries({ queryKey: ["my-teacher-courses"] });
      onDone();
    },
  });
  if (checkout.isLoading) return <p className="text-sm text-text-muted">…</p>;
  const data = checkout.data;
  if (!data) return <p className="text-sm text-danger">{t("market.loadError")}</p>;
  if (data.blocked) return <p className="text-sm text-danger" role="alert">{t("market.payBlocked")}</p>;
  if (data.pending_order) return <p className="text-sm text-text-secondary" data-testid="payment-pending">{t("market.paySent")}</p>;

  return (
    <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); pay.mutate(); }} data-testid="payment-form">
      <p className="rounded-xl bg-accent-blue/5 px-3 py-2 text-xs text-text-secondary ring-1 ring-accent-blue/15">{t("market.payNoProvider")}</p>
      <div className="flex items-center justify-between rounded-xl bg-surface-bg px-3 py-2.5 ring-1 ring-surface-border">
        <span className="text-sm text-text-secondary">{t("market.amount")}</span>
        <span className="text-lg font-extrabold text-text-primary" data-testid="payment-amount">{t("market.price", { price: formatPrice(data.course.price) })}</span>
      </div>
      <div>
        <p className="mb-2 text-sm font-medium text-text-primary">{t("market.payStep1")}</p>
        {data.cards.map((card) => (
          <div key={card.number} className="mb-2 flex items-center justify-between gap-2 rounded-xl bg-surface-bg px-3 py-2 ring-1 ring-surface-border">
            <span className="font-mono text-sm text-text-primary">{card.label} · {card.number.replace(/(\d{4})(?=\d)/g, "$1 ")}</span>
            <button type="button" className="inline-flex items-center gap-1 text-xs font-semibold text-accent-blue"
                    onClick={() => { void navigator.clipboard?.writeText(card.number); setCopied(card.number); }}>
              <Copy size={14} /> {copied === card.number ? t("market.copied") : t("market.copy")}
            </button>
          </div>
        ))}
      </div>
      <p className="text-sm font-medium text-text-primary">{t("market.payStep2")}</p>
      <label className="flex items-center gap-2 text-sm text-text-primary">
        <input type="checkbox" checked={noReceipt} onChange={(e) => setNoReceipt(e.target.checked)} data-testid="payment-no-receipt" /> {t("market.noReceipt")}
      </label>
      {noReceipt ? (
        <div className="grid grid-cols-2 gap-2">
          <label className="text-xs text-text-secondary">{t("market.paidDate")}
            <input type="date" className={inputClass} value={paidDate} onChange={(e) => setPaidDate(e.target.value)} data-testid="payment-date" required />
          </label>
          <label className="text-xs text-text-secondary">{t("market.paidTime")}
            <input type="time" className={inputClass} value={paidTime} onChange={(e) => setPaidTime(e.target.value)} data-testid="payment-time" required />
          </label>
        </div>
      ) : (
        <label className="block text-xs text-text-secondary">{t("market.receipt")}
          <input type="file" accept="image/jpeg,image/png,application/pdf" className={inputClass} onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                 data-testid="payment-file" required />
        </label>
      )}
      <label className="block text-xs text-text-secondary">{t("market.note")}
        <textarea className={inputClass} rows={2} maxLength={1000} value={note} onChange={(e) => setNote(e.target.value)} />
      </label>
      {pay.isError && <p className="text-sm text-danger" role="alert">{errorText(pay.error)}</p>}
      <button type="submit" className={`${buttonPrimary} w-full`} disabled={pay.isPending} data-testid="payment-submit">{t("market.paySend")}</button>
    </form>
  );
}

/** Course details with the one action that fits: enroll (free), pay (paid), interest (upcoming), or the classroom link. */
export function CourseDialog({ course, open, onClose }: { course: CourseItem | null; open: boolean; onClose: () => void }) {
  const { t, language } = useTranslation();
  const errorText = useErrorText();
  const qc = useQueryClient();
  const [paying, setPaying] = useState(false);
  const [message, setMessage] = useState("");
  const refresh = () => {
    void qc.invalidateQueries({ queryKey: ["teacher-profile"] });
    void qc.invalidateQueries({ queryKey: ["my-teacher-courses"] });
  };
  const enroll = useMutation({ mutationFn: () => enrollFree(course!.id), onSuccess: () => { setMessage(t("market.enrollDone")); refresh(); } });
  const interest = useMutation({ mutationFn: (on: boolean) => setInterest(course!.id, on), onSuccess: (r) => { setMessage(r.interested ? t("market.interestOn") : ""); refresh(); } });
  const close = () => { setPaying(false); setMessage(""); enroll.reset(); onClose(); };
  if (!course) return null;
  const mine = course.my_enrollment && ["ACTIVE", "PENDING_PAYMENT", "COMPLETED"].includes(course.my_enrollment.status) ? course.my_enrollment : null;
  const img = resolveMediaUrl(course.image_url);

  return (
    <Modal open={open} onClose={close} title={course.title} wide testId="course-dialog">
      {img && <img src={img} alt="" className="mb-4 aspect-video w-full rounded-2xl object-cover" />}
      <div className="mb-3 flex flex-wrap gap-2">
        <Pill tone={course.status}>{t(`market.status_${course.status}`)}</Pill>
        <Pill tone="DRAFT">{course.level} · {course.language}</Pill>
        <Pill tone="DRAFT">{t(`market.type_${course.course_type}`)}</Pill>
      </div>
      {course.description && <p className="mb-4 whitespace-pre-line text-sm text-text-secondary">{course.description}</p>}
      <dl className="mb-4 grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
        <div className="flex items-center gap-2"><CalendarDays size={16} className="text-text-muted" />
          <dt className="text-text-muted">{t("market.start")}:</dt><dd className="text-text-primary">{formatDate(course.start_date, language)}</dd></div>
        <div className="flex items-center gap-2"><CalendarDays size={16} className="text-text-muted" />
          <dt className="text-text-muted">{t("market.end")}:</dt><dd className="text-text-primary">{formatDate(course.end_date, language)}</dd></div>
        <div className="flex items-center gap-2"><Clock size={16} className="text-text-muted" />
          <dt className="text-text-muted">{t("market.schedule")}:</dt>
          <dd className="text-text-primary">{[course.weekdays.join(", "), course.lesson_time, course.lesson_minutes ? t("market.minutes", { n: course.lesson_minutes }) : null,
            course.lessons_per_week ? t("market.perWeek", { n: course.lessons_per_week }) : null].filter(Boolean).join(" · ") || "—"}</dd></div>
        <div className="flex items-center gap-2"><Users size={16} className="text-text-muted" />
          <dt className="sr-only">{t("market.maxStudents")}</dt>
          <dd className="text-text-primary">{t("market.seats", { taken: course.enrolled, max: course.max_students })} · {t("market.seatsLeft", { n: course.seats_left })}</dd></div>
        {course.duration_weeks && <div><dt className="inline text-text-muted">{t("market.durationWeeks")}: </dt><dd className="inline text-text-primary">{t("market.weeks", { n: course.duration_weeks })}</dd></div>}
        {course.enrollment_deadline && <div><dt className="inline text-text-muted">{t("market.deadline")}: </dt><dd className="inline text-text-primary">{formatDate(course.enrollment_deadline, language)}</dd></div>}
      </dl>
      <div className="mb-4 text-2xl font-extrabold text-text-primary">
        {course.course_type === "FREE" ? t("market.free") : t("market.price", { price: formatPrice(course.price) })}
      </div>

      {message && <p className="mb-3 flex items-center gap-2 rounded-xl bg-emerald-500/10 px-3 py-2 text-sm text-emerald-700 dark:text-emerald-300" role="status" data-testid="course-message">
        <CheckCircle2 size={16} /> {message}</p>}
      {(enroll.isError || interest.isError) && <p className="mb-3 text-sm text-danger" role="alert">{errorText(enroll.error ?? interest.error)}</p>}

      {mine ? (
        <div className="flex flex-wrap items-center gap-3">
          <Pill tone={mine.status === "PENDING_PAYMENT" ? "PENDING" : "APPROVED"} testId="my-enrollment">{t(`market.enrollmentStatus_${mine.status}`)}</Pill>
          {mine.group_id && <Link href={`/groups/${mine.group_id}`} className={buttonPrimary} data-testid="to-classroom">{t("market.toClassroom")}</Link>}
        </div>
      ) : paying ? (
        <PaymentForm course={course} onDone={() => { setPaying(false); setMessage(t("market.paySent")); }} />
      ) : course.can_enroll && course.course_type === "FREE" ? (
        <button type="button" className={buttonPrimary} disabled={enroll.isPending} onClick={() => enroll.mutate()} data-testid="enroll-free">{t("market.enroll")}</button>
      ) : course.can_enroll && course.course_type === "PAID" ? (
        <button type="button" className={buttonPrimary} onClick={() => setPaying(true)} data-testid="enroll-paid">{t("market.enroll")}</button>
      ) : course.can_interest ? (
        <button type="button" className={course.interested ? buttonSecondary : buttonPrimary} disabled={interest.isPending}
                onClick={() => interest.mutate(!course.interested)} data-testid="course-interest">
          {course.interested ? t("market.interestOff") : t("market.interest")}
        </button>
      ) : null}
    </Modal>
  );
}
