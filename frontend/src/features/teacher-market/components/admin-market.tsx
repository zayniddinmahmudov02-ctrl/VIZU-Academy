"use client";

/* eslint-disable @next/next/no-img-element -- teacher photos are our own re-encoded WebP files */
import { useState, type ReactNode } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { AdminButton, AdminCard, AdminCheckbox, AdminInput, AdminPageHeader, AdminSelect } from "@/components/admin/admin-ui";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import { resolveMediaUrl } from "@/lib/media";
import { cn } from "@/lib/utils";

import {
  adminCancelLesson, adminCertificates, adminCourses, adminLessons, adminModerateReview, adminOverview, adminReviewCertificate, adminReviewCourse,
  adminReviewLesson, adminReviews, adminSaveSettings, adminTeachers, adminUpdateTeacher, certificateBlobUrl,
} from "../services/market-service";
import { formatPrice } from "./ui";

type Tab = "uebersicht" | "lehrer" | "zertifikate" | "kurse" | "spezialstunden" | "bewertungen" | "einstellungen";
const TABS: { id: Tab; label: string }[] = [
  { id: "uebersicht", label: "Übersicht" }, { id: "lehrer", label: "Lehrer" }, { id: "zertifikate", label: "Zertifikate" },
  { id: "kurse", label: "Kurse" }, { id: "spezialstunden", label: "Spezialstunden" }, { id: "bewertungen", label: "Bewertungen" },
  { id: "einstellungen", label: "Einstellungen" },
];

const dt = (v: string | null | undefined) => (v ? new Date(v).toLocaleString("de-DE", { timeZone: "Asia/Tashkent", dateStyle: "short", timeStyle: "short" }) : "—");

function Badge({ tone, children }: { tone: "ok" | "warn" | "bad" | "muted"; children: ReactNode }) {
  const c = { ok: "bg-emerald-500/15 text-emerald-400", warn: "bg-amber-500/15 text-amber-400", bad: "bg-red-500/15 text-red-400", muted: "bg-white/5 text-[var(--admin-text-secondary)]" }[tone];
  return <span className={cn("inline-flex rounded-full px-2 py-0.5 text-xs font-semibold", c)}>{children}</span>;
}

function tone(status: string): "ok" | "warn" | "bad" | "muted" {
  if (["APPROVED", "verified", "ENDED"].includes(status)) return "ok";
  if (["PENDING", "pending"].includes(status)) return "warn";
  if (["REJECTED", "rejected", "CANCELLED", "UNPUBLISHED"].includes(status)) return "bad";
  return "muted";
}

/** Row action that needs a reason (reject / unpublish / hide / cancel): the reason field opens under the buttons. */
function ReasonAction({ label, onConfirm, busy, variant = "danger", testId }: {
  label: string; onConfirm: (reason: string) => void; busy?: boolean; variant?: "danger" | "secondary"; testId?: string;
}) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  if (!open) return <AdminButton size="sm" variant={variant} onClick={() => setOpen(true)} data-testid={testId}>{label}</AdminButton>;
  return (
    <span className="flex w-full flex-wrap items-center gap-2">
      <AdminInput className="min-w-[200px] flex-1" placeholder="Grund" value={reason} onChange={(e) => setReason(e.target.value)} data-testid={testId ? `${testId}-reason` : undefined} />
      <AdminButton size="sm" variant="danger" disabled={busy || reason.trim().length < 3} onClick={() => onConfirm(reason)} data-testid={testId ? `${testId}-confirm` : undefined}>
        {label}</AdminButton>
      <AdminButton size="sm" variant="ghost" onClick={() => setOpen(false)}>Abbrechen</AdminButton>
    </span>
  );
}

function useAction<T>(fn: (arg: T) => Promise<unknown>, keys: string[][]) {
  const qc = useQueryClient();
  const [error, setError] = useState("");
  const m = useMutation({
    mutationFn: fn,
    onSuccess: () => { setError(""); keys.forEach((k) => void qc.invalidateQueries({ queryKey: k })); },
    onError: (e) => setError(apiErrorMessage(e, "Aktion fehlgeschlagen")),
  });
  return { ...m, error };
}

function Overview({ go }: { go: (t: Tab) => void }) {
  const q = useQuery({ queryKey: ["admin-market-overview"], queryFn: adminOverview });
  const d = q.data;
  const tiles: { label: string; value: number | undefined; tab: Tab; warn?: boolean }[] = [
    { label: "Lehrer", value: d?.teachers.teachers, tab: "lehrer" },
    { label: "Verified Teacher", value: d?.teachers.verified, tab: "lehrer" },
    { label: "Zertifikate zu prüfen", value: d?.teachers.pending_certificates, tab: "zertifikate", warn: true },
    { label: "Kurse zur Freigabe", value: d?.courses.pending ?? 0, tab: "kurse", warn: true },
    { label: "Veröffentlichte Kurse", value: d?.courses.approved ?? 0, tab: "kurse" },
    { label: "Spezialstunden-Anträge", value: d?.special_lessons.pending ?? 0, tab: "spezialstunden", warn: true },
    { label: "Live-Räume jetzt", value: d?.special_lessons.live ?? 0, tab: "spezialstunden" },
    { label: "Gemeldete Bewertungen", value: d?.reviews.open_reports, tab: "bewertungen", warn: true },
  ];
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4" data-testid="market-overview">
      {tiles.map((x) => (
        <button key={x.label} type="button" onClick={() => go(x.tab)} className="text-left">
          <AdminCard className="h-full transition hover:ring-[var(--admin-primary)]">
            <p className={cn("text-2xl font-bold", x.warn && (x.value ?? 0) > 0 ? "text-amber-400" : "text-[var(--admin-text-primary)]")}>{x.value ?? "…"}</p>
            <p className="text-sm text-[var(--admin-text-secondary)]">{x.label}</p>
          </AdminCard>
        </button>
      ))}
    </div>
  );
}

function Teachers() {
  const [q, setQ] = useState("");
  const [flag, setFlag] = useState("");
  const list = useQuery({ queryKey: ["admin-market-teachers", q, flag], queryFn: () => adminTeachers({ q: q || undefined, flag: flag || undefined }) });
  const act = useAction(({ id, data }: { id: string; data: Record<string, boolean> }) => adminUpdateTeacher(id, data), [["admin-market-teachers"], ["admin-market-overview"]]);
  return (
    <AdminCard>
      <div className="mb-4 flex flex-wrap gap-2">
        <AdminInput className="max-w-xs" placeholder="Name / Benutzername" value={q} onChange={(e) => setQ(e.target.value)} data-testid="admin-teacher-search" />
        <AdminSelect value={flag} onChange={(e) => setFlag(e.target.value)}>
          <option value="">Alle</option><option value="verified">Verified</option><option value="unverified">Nicht verifiziert</option>
          <option value="hidden">Ausgeblendet</option><option value="disabled">Deaktiviert</option>
        </AdminSelect>
      </div>
      {act.error && <p className="mb-3 text-sm text-red-400" role="alert">{act.error}</p>}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[820px] text-left text-sm text-[var(--admin-text-primary)]">
          <thead className="text-xs uppercase text-[var(--admin-text-muted)]"><tr>
            <th className="py-2 pr-3">Lehrer</th><th className="py-2 pr-3">Profil</th><th className="py-2 pr-3">Bewertung</th><th className="py-2 pr-3">Kurse</th>
            <th className="py-2 pr-3">Katalog</th><th className="py-2 pr-3">Verified</th><th className="py-2">Deaktiviert</th>
          </tr></thead>
          <tbody>
            {list.data?.items.map((x) => (
              <tr key={x.id} className="border-t border-[var(--admin-border)]" data-testid="admin-teacher-row">
                <td className="py-2 pr-3">
                  <div className="flex items-center gap-2">
                    {x.photo_url ? <img src={resolveMediaUrl(x.photo_url)!} alt="" className="h-12 w-[27px] rounded object-cover" /> : <span className="h-12 w-[27px] rounded bg-white/5" />}
                    <div><p className="font-semibold">{x.name}</p><p className="text-xs text-[var(--admin-text-muted)]">{x.username}{x.admin_account ? " · Admin + Lehrkraft" : ""}{!x.account_active ? " · Konto inaktiv" : ""}</p></div>
                  </div>
                </td>
                <td className="py-2 pr-3">{x.profile_complete ? <Badge tone="ok">vollständig</Badge> : <Badge tone="muted">unvollständig</Badge>}</td>
                <td className="py-2 pr-3">{x.rating_count ? `${x.rating_avg.toFixed(1)} ★ (${x.rating_count})` : "—"}</td>
                <td className="py-2 pr-3">{x.courses}{x.pending_courses ? ` (${x.pending_courses} offen)` : ""}</td>
                <td className="py-2 pr-3">
                  <AdminCheckbox checked={!x.catalog_hidden} onCheckedChange={(v) => act.mutate({ id: x.id, data: { catalog_hidden: !v } })} aria-label="Im Katalog zeigen" data-testid="admin-teacher-visible" />
                </td>
                <td className="py-2 pr-3">
                  <AdminCheckbox checked={x.verified} onCheckedChange={(v) => act.mutate({ id: x.id, data: { verified: !!v } })} aria-label="Verified Teacher" data-testid="admin-teacher-verified" />
                </td>
                <td className="py-2">
                  <AdminCheckbox checked={x.profile_disabled} onCheckedChange={(v) => act.mutate({ id: x.id, data: { profile_disabled: !!v } })} aria-label="Profil deaktivieren" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-xs text-[var(--admin-text-muted)]">Konten anlegen / sperren: Admin → Team. Bewertungen ändert niemand von Hand — sie entstehen nur aus Schülerbewertungen.</p>
    </AdminCard>
  );
}

function Certificates() {
  const [status, setStatus] = useState("pending");
  const list = useQuery({ queryKey: ["admin-market-certs", status], queryFn: () => adminCertificates(status || undefined) });
  const act = useAction(({ id, decision, reason }: { id: string; decision: "verify" | "reject"; reason?: string }) => adminReviewCertificate(id, decision, reason),
                        [["admin-market-certs"], ["admin-market-overview"]]);
  const open = async (url: string) => { const w = window.open("", "_blank"); try { const b = await certificateBlobUrl(url); if (w) w.location.href = b; } catch { w?.close(); } };
  return (
    <AdminCard>
      <AdminSelect className="mb-4 max-w-xs" value={status} onChange={(e) => setStatus(e.target.value)}>
        <option value="pending">Zu prüfen</option><option value="verified">Geprüft</option><option value="rejected">Abgelehnt</option><option value="">Alle</option>
      </AdminSelect>
      {act.error && <p className="mb-3 text-sm text-red-400" role="alert">{act.error}</p>}
      {!list.data?.length ? <p className="text-sm text-[var(--admin-text-secondary)]">Keine Zertifikate.</p> : (
        <ul className="space-y-3">
          {list.data.map((c) => (
            <li key={c.id} className="rounded-xl bg-white/5 p-3" data-testid="admin-cert-row">
              <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-[var(--admin-text-primary)]">
                <span><b>{c.title}</b> · {c.issuer}{c.level ? ` · ${c.level}` : ""} — {c.teacher.name}</span><Badge tone={tone(c.status!)}>{c.status}</Badge>
              </div>
              {c.reject_reason && <p className="text-xs text-red-400">{c.reject_reason}</p>}
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <AdminButton size="sm" variant="secondary" onClick={() => open(c.file_url)}>Datei ansehen ({c.file_type})</AdminButton>
                {c.status !== "verified" && <AdminButton size="sm" onClick={() => act.mutate({ id: c.id, decision: "verify" })} data-testid="admin-cert-verify">Bestätigen</AdminButton>}
                {c.status !== "rejected" && <ReasonAction label="Ablehnen" busy={act.isPending} onConfirm={(r) => act.mutate({ id: c.id, decision: "reject", reason: r })} />}
              </div>
            </li>
          ))}
        </ul>
      )}
    </AdminCard>
  );
}

function Courses() {
  const [approval, setApproval] = useState("PENDING");
  const list = useQuery({ queryKey: ["admin-market-courses", approval], queryFn: () => adminCourses(approval || undefined) });
  const act = useAction(({ id, decision, reason }: { id: string; decision: "approve" | "reject" | "unpublish"; reason?: string }) => adminReviewCourse(id, decision, reason),
                        [["admin-market-courses"], ["admin-market-overview"]]);
  return (
    <AdminCard>
      <AdminSelect className="mb-4 max-w-xs" value={approval} onChange={(e) => setApproval(e.target.value)} data-testid="admin-course-filter">
        <option value="PENDING">Zur Freigabe</option><option value="APPROVED">Veröffentlicht</option><option value="REJECTED">Abgelehnt</option>
        <option value="UNPUBLISHED">Zurückgezogen</option><option value="DRAFT">Entwürfe</option><option value="">Alle</option>
      </AdminSelect>
      {act.error && <p className="mb-3 text-sm text-red-400" role="alert">{act.error}</p>}
      {!list.data?.length ? <p className="text-sm text-[var(--admin-text-secondary)]">Keine Kurse.</p> : (
        <ul className="space-y-3">
          {list.data.map((c) => (
            <li key={c.id} className="rounded-xl bg-white/5 p-3 text-sm text-[var(--admin-text-primary)]" data-testid="admin-course-row">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span><b>{c.title}</b> · {c.teacher.name} · {c.level} · {c.course_type === "FREE" ? "kostenlos" : `${formatPrice(c.price)} so'm`} ({c.course_type})</span>
                <Badge tone={tone(c.approval_status)}>{c.approval_status}</Badge>
              </div>
              <p className="mt-1 text-xs text-[var(--admin-text-secondary)]">
                Status {c.status} · Plätze {c.enrolled}/{c.max_students} · Beginn {c.start_date ?? "—"} · eingereicht {dt(c.submitted_at)}
                {c.revenue ? ` · bestätigte Zahlungen ${formatPrice(c.revenue)} so'm` : ""}
              </p>
              {c.description && <p className="mt-1 line-clamp-3 whitespace-pre-line text-xs text-[var(--admin-text-secondary)]">{c.description}</p>}
              {c.reject_reason && <p className="text-xs text-red-400">{c.reject_reason}</p>}
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {["PENDING", "REJECTED", "UNPUBLISHED"].includes(c.approval_status) && (
                  <AdminButton size="sm" disabled={act.isPending} onClick={() => act.mutate({ id: c.id, decision: "approve" })} data-testid="admin-course-approve">Freigeben</AdminButton>
                )}
                {c.approval_status === "PENDING" && <ReasonAction label="Ablehnen" busy={act.isPending} onConfirm={(r) => act.mutate({ id: c.id, decision: "reject", reason: r })} testId="admin-course-reject" />}
                {c.approval_status === "APPROVED" && <ReasonAction label="Zurückziehen" busy={act.isPending} onConfirm={(r) => act.mutate({ id: c.id, decision: "unpublish", reason: r })} />}
              </div>
            </li>
          ))}
        </ul>
      )}
      <p className="mt-3 text-xs text-[var(--admin-text-muted)]">Zahlungen für kostenpflichtige Kurse: Admin → Payments → Zahlungsanfragen („My Teacher Kurs“). Erst die bestätigte Zahlung meldet den Schüler an.</p>
    </AdminCard>
  );
}

function Lessons() {
  const [status, setStatus] = useState("PENDING");
  const list = useQuery({ queryKey: ["admin-market-lessons", status], queryFn: () => adminLessons(status || undefined), refetchInterval: 30_000 });
  const [moveTo, setMoveTo] = useState<Record<string, string>>({});
  const act = useAction(({ id, decision, reason, startsAt }: { id: string; decision: "approve" | "reject"; reason?: string; startsAt?: string }) =>
    adminReviewLesson(id, decision, reason, startsAt), [["admin-market-lessons"], ["admin-market-overview"]]);
  const cancel = useAction(({ id, reason }: { id: string; reason: string }) => adminCancelLesson(id, reason), [["admin-market-lessons"], ["admin-market-overview"]]);
  return (
    <AdminCard>
      <AdminSelect className="mb-4 max-w-xs" value={status} onChange={(e) => setStatus(e.target.value)} data-testid="admin-lesson-filter">
        <option value="PENDING">Anträge</option><option value="APPROVED">Freigegeben</option><option value="ENDED">Beendet</option>
        <option value="REJECTED">Abgelehnt</option><option value="CANCELLED">Abgesagt</option><option value="">Alle</option>
      </AdminSelect>
      {(act.error || cancel.error) && <p className="mb-3 text-sm text-red-400" role="alert">{act.error || cancel.error}</p>}
      {!list.data?.length ? <p className="text-sm text-[var(--admin-text-secondary)]">Keine Spezialstunden.</p> : (
        <ul className="space-y-3">
          {list.data.map((l) => (
            <li key={l.id} className="rounded-xl bg-white/5 p-3 text-sm text-[var(--admin-text-primary)]" data-testid="admin-lesson-row">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span><b>{l.title}</b> · {l.teacher.name} · {l.topic} · {l.level} · {l.language}</span>
                <span className="flex gap-2"><Badge tone={tone(l.status)}>{l.status}</Badge>{l.room && <Badge tone={l.room.status === "live" ? "warn" : "muted"}>Raum: {l.room.status}</Badge>}</span>
              </div>
              <p className="mt-1 text-xs text-[var(--admin-text-secondary)]">
                Beginn {dt(l.starts_at)} · {l.duration_minutes} Min. · max. {l.max_participants} · Anmeldungen {l.signups}
                {l.room ? ` · online ${l.room.online} · teilgenommen ${l.participants_total ?? 0}` : ""}
              </p>
              {l.objectives && <p className="mt-1 text-xs text-[var(--admin-text-secondary)]">Lernziele: {l.objectives}</p>}
              {(l.reject_reason || l.cancel_reason) && <p className="text-xs text-red-400">{l.reject_reason ?? l.cancel_reason}</p>}
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {l.status === "PENDING" && (
                  <>
                    <AdminInput type="datetime-local" className="w-56" aria-label="Neuer Beginn (optional)" value={moveTo[l.id] ?? ""}
                                onChange={(e) => setMoveTo({ ...moveTo, [l.id]: e.target.value })} />
                    <AdminButton size="sm" disabled={act.isPending} data-testid="admin-lesson-approve"
                                 onClick={() => act.mutate({ id: l.id, decision: "approve", startsAt: moveTo[l.id] ? new Date(moveTo[l.id]).toISOString() : undefined })}>
                      Freigeben</AdminButton>
                    <ReasonAction label="Ablehnen" busy={act.isPending} onConfirm={(r) => act.mutate({ id: l.id, decision: "reject", reason: r })} />
                  </>
                )}
                {l.status === "APPROVED" && <ReasonAction label="Freigabe zurücknehmen / absagen" busy={cancel.isPending} onConfirm={(r) => cancel.mutate({ id: l.id, reason: r })} />}
                {l.room?.status === "live" && <Link href="/admin/video-rooms" className="text-xs font-semibold text-[var(--admin-primary)]">Live-Räume überwachen</Link>}
              </div>
            </li>
          ))}
        </ul>
      )}
    </AdminCard>
  );
}

function Reviews() {
  const [view, setView] = useState<"reported" | "hidden" | "all">("reported");
  const list = useQuery({ queryKey: ["admin-market-reviews", view], queryFn: () => adminReviews(view) });
  const act = useAction(({ id, action, reason }: { id: string; action: "hide" | "show" | "dismiss"; reason?: string }) => adminModerateReview(id, action, reason),
                        [["admin-market-reviews"], ["admin-market-overview"]]);
  return (
    <AdminCard>
      <AdminSelect className="mb-4 max-w-xs" value={view} onChange={(e) => setView(e.target.value as typeof view)}>
        <option value="reported">Gemeldet</option><option value="hidden">Ausgeblendet</option><option value="all">Alle</option>
      </AdminSelect>
      {act.error && <p className="mb-3 text-sm text-red-400" role="alert">{act.error}</p>}
      {!list.data?.length ? <p className="text-sm text-[var(--admin-text-secondary)]">Keine Bewertungen.</p> : (
        <ul className="space-y-3">
          {list.data.map((r) => (
            <li key={r.id} className="rounded-xl bg-white/5 p-3 text-sm text-[var(--admin-text-primary)]" data-testid="admin-review-row">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span>{"★".repeat(r.rating)}{"☆".repeat(5 - r.rating)} · {r.student.name} → {r.teacher.name} · {r.course.title}</span>
                <span className="flex gap-2">{r.open_reports > 0 && <Badge tone="warn">{r.open_reports} Meldung(en)</Badge>}<Badge tone={r.status === "hidden" ? "bad" : "ok"}>{r.status}</Badge></span>
              </div>
              {r.body && <p className="mt-1 whitespace-pre-line text-xs text-[var(--admin-text-secondary)]">{r.body}</p>}
              {r.reports.map((rep, i) => <p key={i} className="text-xs text-amber-400">Meldung: {rep.reason} ({rep.status}, {dt(rep.created_at)})</p>)}
              {r.hidden_reason && <p className="text-xs text-red-400">Ausgeblendet: {r.hidden_reason}</p>}
              <div className="mt-2 flex flex-wrap gap-2">
                {r.status === "visible" ? (
                  <ReasonAction label="Ausblenden" busy={act.isPending} onConfirm={(reason) => act.mutate({ id: r.id, action: "hide", reason })} testId="admin-review-hide" />
                ) : <AdminButton size="sm" variant="secondary" onClick={() => act.mutate({ id: r.id, action: "show" })}>Wieder zeigen</AdminButton>}
                {r.open_reports > 0 && <AdminButton size="sm" variant="ghost" onClick={() => act.mutate({ id: r.id, action: "dismiss" })}>Meldungen schließen</AdminButton>}
              </div>
            </li>
          ))}
        </ul>
      )}
      <p className="mt-3 text-xs text-[var(--admin-text-muted)]">Die Durchschnittsbewertung wird nach jeder Änderung automatisch aus den sichtbaren Bewertungen berechnet. Jede Moderation steht im Audit-Log.</p>
    </AdminCard>
  );
}

function SettingsTab() {
  const q = useQuery({ queryKey: ["admin-market-overview"], queryFn: adminOverview });
  const act = useAction((v: boolean) => adminSaveSettings(v), [["admin-market-overview"]]);
  const on = q.data?.settings.course_auto_publish ?? false;
  return (
    <AdminCard className="space-y-3">
      <label className="flex items-center gap-3 text-sm text-[var(--admin-text-primary)]">
        <AdminCheckbox checked={on} onCheckedChange={(v) => act.mutate(!!v)} aria-label="Kurse automatisch veröffentlichen" data-testid="admin-auto-publish" />
        Kurse ohne Prüfung automatisch veröffentlichen
      </label>
      <p className="text-xs text-[var(--admin-text-secondary)]">Empfohlen: aus. Dann prüft ein Super Admin jeden neuen Kurs und jede Änderung von Titel, Beschreibung, Niveau, Sprache, Art oder Preis.
        Spezialstunden brauchen immer eine Freigabe.</p>
      <p className="text-xs text-[var(--admin-text-secondary)]">Zahlungen: Kartenüberweisung + Beleg, Prüfung in Admin → Payments (kein Online-Zahlungsanbieter eingerichtet; für Click / Payme werden
        Händler-ID und Geheimschlüssel als Server-Einstellungen gebraucht).</p>
      {act.error && <p className="text-sm text-red-400" role="alert">{act.error}</p>}
    </AdminCard>
  );
}

export default function AdminMarket() {
  const [tab, setTab] = useState<Tab>(() => {
    if (typeof window === "undefined") return "uebersicht";
    const p = new URLSearchParams(window.location.search).get("tab") as Tab | null;
    return p && TABS.some((x) => x.id === p) ? p : "uebersicht";
  });
  return (
    <div data-testid="admin-teacher-market">
      <AdminPageHeader title="Lehrer-Marktplatz" description="My Teacher: Lehrerprofile, Zertifikate, Kurse, kostenlose Spezialstunden und Bewertungen" />
      <div className="mb-5 flex flex-wrap gap-1" role="tablist">
        {TABS.map((x) => (
          <button key={x.id} type="button" role="tab" aria-selected={tab === x.id} onClick={() => setTab(x.id)} data-testid={`market-tab-${x.id}`}
                  className={cn("rounded-lg px-3 py-2 text-sm font-semibold", tab === x.id ? "bg-[var(--admin-primary)] text-white" : "text-[var(--admin-text-secondary)] hover:bg-[var(--admin-hover)]")}>
            {x.label}
          </button>
        ))}
      </div>
      {tab === "uebersicht" && <Overview go={setTab} />}
      {tab === "lehrer" && <Teachers />}
      {tab === "zertifikate" && <Certificates />}
      {tab === "kurse" && <Courses />}
      {tab === "spezialstunden" && <Lessons />}
      {tab === "bewertungen" && <Reviews />}
      {tab === "einstellungen" && <SettingsTab />}
    </div>
  );
}
