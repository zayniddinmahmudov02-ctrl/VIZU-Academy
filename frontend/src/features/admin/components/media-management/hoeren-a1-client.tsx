"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle2, FileText, Loader2, RefreshCw, Send, Upload } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminPageHeader } from "@/components/admin/admin-ui";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import {
  applyHoerenPdf,
  getHoerenA1Status,
  previewHoerenPdf,
  publishReadyHoerenA1,
  type HoerenApplyResult,
  type HoerenLessonPlan,
  type HoerenSummary,
  type SlotStatus,
} from "@/features/admin/services/hoeren-a1-service";

const card = "rounded-2xl bg-[var(--admin-card)] p-4 ring-1 ring-[var(--admin-border)] sm:p-5";
const STATUS: Record<SlotStatus, [string, string]> = {
  new: ["neu", "text-[var(--admin-primary)]"],
  match: ["stimmt schon", "text-[var(--admin-success)]"],
  conflict: ["Konflikt", "text-[var(--admin-danger)]"],
  suspicious: ["prüfen", "text-[var(--admin-warning)]"],
  invalid: ["ungültig", "text-[var(--admin-danger)]"],
};
const LESSON_STATUS: Record<HoerenLessonPlan["status"], string> = {
  ok: "zugeordnet",
  no_answers: "keine Hören-Antworten im PDF",
  no_tasks: "keine Hören-Aufgabe",
  not_assigned: "nicht zugeordnet",
  lesson_missing: "Lektion fehlt",
};

function SummaryLine({ s }: { s: HoerenSummary }) {
  return (
    <p className="text-sm text-[var(--admin-text-secondary)]" data-testid="hoeren-summary">
      {s.lessons_assigned}/{s.lessons} Lektionen zugeordnet · <b className="text-[var(--admin-primary)]">{s.new} neu</b> · {s.match} stimmen schon ·{" "}
      <b className="text-[var(--admin-warning)]">{s.suspicious + s.conflict} zu prüfen</b>{s.invalid ? ` · ${s.invalid} ungültig` : ""}
    </p>
  );
}

/** A1 Hören: answer keys from the VIZU answer-sheet PDF (only the Hören
 * part is read) and automatic publishing of complete tasks (audio file on
 * the server + every question with a key). Everything is decided on the
 * server; this page shows the plan and sends the admin's decisions. */
export default function HoerenA1Client() {
  const queryClient = useQueryClient();
  const status = useQuery({ queryKey: ["hoeren-a1", "status"], queryFn: getHoerenA1Status });
  const fileInput = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [plan, setPlan] = useState<{ summary: HoerenSummary; lessons: HoerenLessonPlan[] } | null>(null);
  const [accepted, setAccepted] = useState<Set<string>>(new Set());
  const [result, setResult] = useState<HoerenApplyResult | null>(null);
  const [busy, setBusy] = useState<"preview" | "apply" | "publish" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [published, setPublished] = useState<string | null>(null);

  async function onFile(f: File | undefined) {
    if (fileInput.current) fileInput.current.value = "";
    if (!f) return;
    setFile(f);
    setPlan(null);
    setResult(null);
    setAccepted(new Set());
    setError(null);
    setBusy("preview");
    try {
      setPlan(await previewHoerenPdf(f));
    } catch (err) {
      setError(apiErrorMessage(err, "PDF konnte nicht gelesen werden."));
    } finally {
      setBusy(null);
    }
  }

  async function apply() {
    if (!file) return;
    setBusy("apply");
    setError(null);
    try {
      const r = await applyHoerenPdf(file, [...accepted]);
      setResult(r);
      setPlan({ summary: r.summary_after, lessons: r.lessons_after });
      setAccepted(new Set());
      await queryClient.invalidateQueries({ queryKey: ["hoeren-a1", "status"] });
      await queryClient.invalidateQueries({ queryKey: ["media-mgmt"] });
    } catch (err) {
      setError(apiErrorMessage(err, "Übernehmen fehlgeschlagen."));
    } finally {
      setBusy(null);
    }
  }

  async function publishReady() {
    setBusy("publish");
    setError(null);
    try {
      const out = await publishReadyHoerenA1();
      const n = out.filter((o) => o.result === "published").length;
      setPublished(n ? `${n} Aufgabe(n) veröffentlicht.` : "Keine weitere Aufgabe ist vollständig — nichts veröffentlicht.");
      await queryClient.invalidateQueries({ queryKey: ["hoeren-a1", "status"] });
    } catch (err) {
      setError(apiErrorMessage(err, "Veröffentlichen fehlgeschlagen."));
    } finally {
      setBusy(null);
    }
  }

  const toggle = (id: string, on: boolean) =>
    setAccepted((prev) => {
      const next = new Set(prev);
      if (on) next.add(id);
      else next.delete(id);
      return next;
    });

  const writable = plan ? plan.summary.new + accepted.size : 0;

  return (
    <div className="space-y-6" data-testid="hoeren-a1">
      <Link href="/admin/media-management" className="inline-flex items-center gap-1.5 text-sm text-[var(--admin-text-secondary)] hover:text-[var(--admin-primary)]">
        <ArrowLeft size={15} /> Media Management
      </Link>
      <AdminPageHeader title="A1 Hören — Antworten & Veröffentlichung"
                       description="Lösungen aus dem VIZU-Antwort-PDF übernehmen (nur der Hören-Teil) und vollständige A1 Hören-Aufgaben automatisch veröffentlichen." />
      <input ref={fileInput} type="file" accept=".pdf,application/pdf" className="hidden" onChange={(e) => onFile(e.target.files?.[0])} data-testid="hoeren-pdf-file" />

      <section className={`${card} space-y-4`}>
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="mr-auto text-sm font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">1. Antwort-PDF</h2>
          {file && <span className="inline-flex items-center gap-1.5 text-sm text-[var(--admin-text-secondary)]"><FileText size={15} /> {file.name}</span>}
          <AdminButton variant="secondary" disabled={!!busy} onClick={() => fileInput.current?.click()} data-testid="hoeren-pdf-upload">
            {busy === "preview" ? <Loader2 size={15} className="animate-spin" /> : <Upload size={15} />} PDF wählen und prüfen
          </AdminButton>
        </div>
        <p className="text-xs text-[var(--admin-text-muted)]">
          Gelesen wird nur „Hören – Eshitish qismi javoblari“ jeder Lektion. Antworten werden den vorhandenen Fragen in ihrer Reihenfolge zugeordnet;
          es werden keine Fragen angelegt oder gelöscht. Was nicht eindeutig passt, wird erst nach Ihrer Bestätigung übernommen.
        </p>

        {plan && (
          <>
            <SummaryLine s={plan.summary} />
            <div className="space-y-3">
              {plan.lessons.map((lesson) => (
                <details key={lesson.lesson_number} className="rounded-xl ring-1 ring-[var(--admin-border)]" open={lesson.tasks.some((t) => t.slots.some((s) => s.status !== "match")) || lesson.status === "not_assigned"}
                         data-testid="hoeren-plan-lesson" data-lesson={lesson.lesson_number} data-status={lesson.status}>
                  <summary className="cursor-pointer px-4 py-3 text-sm">
                    <b className="text-[var(--admin-text-primary)]">Lektion {lesson.lesson_number}</b>
                    <span className="text-[var(--admin-text-secondary)]">{lesson.lesson_title ? ` · ${lesson.lesson_title}` : ""}</span>
                    <span className={`ml-2 text-xs ${lesson.status === "ok" ? "text-[var(--admin-success)]" : "text-[var(--admin-text-muted)]"}`}>— {LESSON_STATUS[lesson.status]}</span>
                    {lesson.note && <span className="block text-xs text-[var(--admin-warning)]">{lesson.note}</span>}
                  </summary>
                  <div className="space-y-4 px-4 pb-4">
                    {lesson.tasks.map((task) => (
                      <div key={task.listening_id} className="space-y-2">
                        <p className="text-sm font-semibold text-[var(--admin-text-primary)]">{task.title}</p>
                        {task.problem && <p className="text-xs text-[var(--admin-danger)]">{task.problem}</p>}
                        {task.slots.length === 0 ? (
                          task.pdf_answers.length > 0 && <p className="text-xs text-[var(--admin-text-secondary)]">PDF: {task.pdf_answers.join(", ")}</p>
                        ) : (
                          <div className="overflow-x-auto">
                            <table className="w-full min-w-[760px] text-left text-xs">
                              <thead className="text-[var(--admin-text-muted)]">
                                <tr>{["Frage", "Stelle", "bisher", "PDF", "Status", "übernehmen"].map((h) => <th key={h} className="px-2 py-1.5 font-semibold">{h}</th>)}</tr>
                              </thead>
                              <tbody>
                                {task.slots.map((s) => {
                                  const review = s.status === "conflict" || s.status === "suspicious";
                                  return (
                                    <tr key={s.id} className="border-t border-[var(--admin-border)] align-top" data-testid="hoeren-slot" data-status={s.status}>
                                      <td className="px-2 py-1.5 text-[var(--admin-text-secondary)]">{s.question_no}{s.gap_id ? ` / Lücke ${s.gap_id}` : ""}</td>
                                      <td className="max-w-[18rem] px-2 py-1.5 text-[var(--admin-text-secondary)]">{s.kind === "GAP" ? s.context : s.question}</td>
                                      <td className="px-2 py-1.5 text-[var(--admin-text-muted)]">{s.current ?? "—"}</td>
                                      <td className="px-2 py-1.5 font-semibold text-[var(--admin-text-primary)]">{s.answer}</td>
                                      <td className={`px-2 py-1.5 ${STATUS[s.status][1]}`}>{STATUS[s.status][0]}{s.note && <span className="block text-[var(--admin-text-muted)]">{s.note}</span>}</td>
                                      <td className="px-2 py-1.5">
                                        {review ? (
                                          <AdminCheckbox checked={accepted.has(s.id)} onCheckedChange={(v) => toggle(s.id, Boolean(v))} data-testid="hoeren-accept" />
                                        ) : s.status === "new" ? <span className="text-[var(--admin-primary)]">automatisch</span> : "—"}
                                      </td>
                                    </tr>
                                  );
                                })}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </details>
              ))}
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <AdminButton onClick={apply} disabled={!!busy || writable === 0} data-testid="hoeren-apply">
                {busy === "apply" ? <Loader2 size={15} className="animate-spin" /> : <CheckCircle2 size={15} />}
                {writable} Antwort(en) übernehmen
              </AdminButton>
              <span className="text-xs text-[var(--admin-text-muted)]">„prüfen“ / „Konflikt“ nur mit Haken. Danach werden vollständige A1-Aufgaben mit Audio veröffentlicht.</span>
            </div>
          </>
        )}

        {result && (
          <div className="rounded-xl bg-[var(--admin-success)]/10 p-3 text-sm text-[var(--admin-success)]" data-testid="hoeren-result">
            {result.written} Antwort(en) gespeichert{result.review_skipped ? `, ${result.review_skipped} ohne Bestätigung nicht übernommen` : ""}.{" "}
            {result.publish.filter((p) => p.result === "published").length} Aufgabe(n) veröffentlicht.
            {result.publish.filter((p) => p.result === "not_ready").map((p) => (
              <span key={p.listening_id} className="block text-xs text-[var(--admin-text-secondary)]">L{p.lesson_number} {p.title}: Entwurf — {p.reasons.join(", ")}</span>
            ))}
          </div>
        )}
        {error && <p className="rounded-xl bg-[var(--admin-danger)]/10 p-3 text-sm text-[var(--admin-danger)]" role="alert">{error}</p>}
      </section>

      <section className={`${card} space-y-3`}>
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="mr-auto text-sm font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">2. A1 Hören-Aufgaben</h2>
          <AdminButton variant="ghost" size="sm" onClick={() => status.refetch()} aria-label="Aktualisieren"><RefreshCw size={14} /></AdminButton>
          <AdminButton size="sm" onClick={publishReady} disabled={!!busy} data-testid="hoeren-publish-ready">
            {busy === "publish" ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />} Vollständige veröffentlichen
          </AdminButton>
        </div>
        {published && <p className="text-sm text-[var(--admin-success)]">{published}</p>}
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm" data-testid="hoeren-status">
            <thead className="text-xs uppercase tracking-wide text-[var(--admin-text-muted)]">
              <tr>{["Lektion", "Aufgabe", "Audio", "Fragen", "ohne Lösung", "Status", "Grund"].map((h) => <th key={h} className="px-3 py-2">{h}</th>)}</tr>
            </thead>
            <tbody>
              {(status.data ?? []).map((t) => (
                <tr key={t.listening_id} className="border-t border-[var(--admin-border)]" data-testid="hoeren-status-row" data-published={t.is_published}>
                  <td className="px-3 py-2 font-semibold text-[var(--admin-text-primary)]">{t.lesson_number}</td>
                  <td className="px-3 py-2 text-[var(--admin-text-secondary)]">{t.title}</td>
                  <td className={`px-3 py-2 text-xs ${t.audio === "ok" ? "text-[var(--admin-success)]" : "text-[var(--admin-warning)]"}`}>
                    {t.audio === "ok" ? t.audio_name || "vorhanden" : t.audio === "file_missing" ? "Datei fehlt" : "kein Audio"}
                  </td>
                  <td className="px-3 py-2">{t.questions}</td>
                  <td className={`px-3 py-2 ${t.key_missing ? "text-[var(--admin-warning)]" : ""}`}>{t.key_missing}</td>
                  <td className="px-3 py-2">
                    <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${t.is_published ? "bg-[var(--admin-success)]/15 text-[var(--admin-success)]" : "bg-[var(--admin-hover)] text-[var(--admin-text-secondary)]"}`}>
                      {t.is_published ? "Veröffentlicht" : "Entwurf"}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-xs text-[var(--admin-text-muted)]">{t.reasons.join(", ") || (t.is_published ? "" : "bereit")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
