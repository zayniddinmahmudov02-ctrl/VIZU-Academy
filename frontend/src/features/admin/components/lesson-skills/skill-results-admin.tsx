"use client";

import { Fragment, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, ChevronRight, History, Play, RefreshCw } from "lucide-react";

import { AdminButton, AdminInput, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import type { SkillResult, SkillKey } from "@/features/lessons/services/lesson-skills-service";
import {
  apiErrorMessage,
  getLessonSkillsResults,
  getSpeakingAudioBlobUrl,
  overrideSubmissionScore,
  reevaluateSubmission,
  type AdminStudentResult,
  type AdminSubmission,
} from "@/features/admin/services/lesson-skills-admin-service";

const STATUS_LABEL: Record<string, string> = {
  not_available: "—",
  not_started: "nicht begonnen",
  in_progress: "läuft",
  pending_evaluation: "wird bewertet",
  evaluation_failed: "Bewertung fehlgeschlagen",
  completed: "fertig",
  SUBMITTED: "eingereicht",
  EVALUATING: "wird bewertet",
  GRADED: "bewertet",
  EVALUATION_FAILED: "Bewertung fehlgeschlagen",
  NEEDS_REVISION: "Überarbeitung",
};

const STATUS_TONE: Record<string, string> = {
  completed: "text-emerald-400",
  GRADED: "text-emerald-400",
  pending_evaluation: "text-amber-400",
  SUBMITTED: "text-amber-400",
  EVALUATING: "text-amber-400",
  evaluation_failed: "text-[var(--admin-danger)]",
  EVALUATION_FAILED: "text-[var(--admin-danger)]",
  NEEDS_REVISION: "text-amber-400",
};

function fmtDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "—" : d.toLocaleString("de-DE", { dateStyle: "short", timeStyle: "short" });
}

const SKILL_COLUMNS: { key: SkillKey; label: string }[] = [
  { key: "frage", label: "Frage" },
  { key: "grammatik", label: "Grammatik" },
  { key: "lesen", label: "Lesen" },
  { key: "hoeren", label: "Hören" },
  { key: "schreiben", label: "Schreiben" },
  { key: "sprechen", label: "Sprechen" },
  { key: "wortschatz", label: "Wortschatz" },
  { key: "yakuniy", label: "Yakuniy" },
];

function SkillCell({ skill }: { skill: SkillResult | undefined }) {
  if (!skill || !skill.available) return <span className="text-[var(--admin-text-muted)]">—</span>;
  return (
    <div className="leading-tight">
      <span className="font-bold tabular-nums text-[var(--admin-text-primary)]">{skill.score ?? "—"}</span>
      <span className={`block text-[11px] ${STATUS_TONE[skill.status] ?? "text-[var(--admin-text-muted)]"}`}>{STATUS_LABEL[skill.status] ?? skill.status}</span>
    </div>
  );
}

function StudentsTable({ students }: { students: AdminStudentResult[] }) {
  if (students.length === 0) {
    return <p className="text-sm text-[var(--admin-text-muted)]">Noch keine Schülerergebnisse in dieser Lektion.</p>;
  }
  return (
    <div className="overflow-x-auto rounded-2xl bg-[var(--admin-card)] ring-1 ring-[var(--admin-border)]">
      <table className="w-full min-w-[1040px] text-left text-sm" data-testid="admin-skill-students">
        <thead>
          <tr className="border-b border-[var(--admin-border)] text-xs uppercase tracking-wide text-[var(--admin-text-muted)]">
            <th className="px-4 py-3">Schüler</th>
            {SKILL_COLUMNS.map((c) => (
              <th key={c.key} className="px-3 py-3">{c.label}</th>
            ))}
            <th className="px-3 py-3">Gesamt</th>
          </tr>
        </thead>
        <tbody>
          {students.map((s) => (
            <tr key={s.user_id} className="border-b border-[var(--admin-border)] last:border-0">
              <td className="px-4 py-3">
                <span className="font-semibold text-[var(--admin-text-primary)]">{s.student_name}</span>
                {s.email && <span className="block text-xs text-[var(--admin-text-muted)]">{s.email}</span>}
              </td>
              {SKILL_COLUMNS.map((c) => (
                <td key={c.key} className="px-3 py-3"><SkillCell skill={s.skills[c.key]} /></td>
              ))}
              <td className="px-3 py-3">
                {s.overall.score === null ? (
                  <span className="text-[var(--admin-text-muted)]">—</span>
                ) : (
                  <div className="leading-tight" title={s.overall.method ?? undefined}>
                    <span className="font-bold tabular-nums text-[var(--admin-text-primary)]">{s.overall.score}</span>
                    <span className="block text-[11px] text-[var(--admin-text-muted)]">
                      {s.overall.status === "final" ? "endgültig" : `vorläufig (${s.overall.graded_skills}/${s.overall.required_skills})`}
                    </span>
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SubmissionDetail({ sub, onChanged }: { sub: AdminSubmission; onChanged: () => Promise<unknown> }) {
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [score, setScore] = useState<string>(sub.score != null ? String(sub.score) : "");
  const [feedback, setFeedback] = useState(sub.feedback ?? "");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const ev = sub.ai_evaluation;

  async function loadAudio() {
    try {
      setAudioUrl(await getSpeakingAudioBlobUrl(sub.id));
    } catch {
      setMessage("Audio konnte nicht geladen werden.");
    }
  }

  async function saveOverride() {
    const value = Number(score);
    if (!Number.isInteger(value) || value < 0 || value > 100) {
      setMessage("Punktzahl 0–100.");
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      await overrideSubmissionScore(sub.kind, sub.id, { score: value, feedback: feedback.trim() || null, reason: reason.trim() || null });
      setReason("");
      await onChanged();
      setMessage("Gespeichert. Die ursprüngliche KI-Bewertung bleibt im Verlauf.");
    } catch (err) {
      setMessage(apiErrorMessage(err, "Speichern fehlgeschlagen."));
    } finally {
      setBusy(false);
    }
  }

  async function reevaluate() {
    setBusy(true);
    setMessage(null);
    try {
      await reevaluateSubmission(sub.kind, sub.id);
      await onChanged();
      setMessage("Neue KI-Bewertung gestartet.");
    } catch (err) {
      const code = apiErrorMessage(err, "Fehlgeschlagen.");
      setMessage(code === "AI_EVALUATION_DISABLED" ? "KI-Bewertung ist für diese Aufgabe deaktiviert." : code === "EVALUATION_IN_PROGRESS" ? "Bewertung läuft bereits." : code);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4 p-4 text-sm" data-testid="admin-submission-detail">
      {sub.kind === "WRITING" ? (
        <div>
          <p className="mb-1 text-xs font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">Text des Schülers</p>
          <p className="whitespace-pre-wrap rounded-xl bg-white/[0.03] p-3 text-[var(--admin-text-primary)] ring-1 ring-[var(--admin-border)]">{sub.answer_text || "—"}</p>
        </div>
      ) : (
        <div className="space-y-2">
          <p className="text-xs font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">
            Aufnahme {sub.duration_seconds ? `· ${sub.duration_seconds}s` : ""}
          </p>
          {audioUrl ? (
            <audio controls src={audioUrl} className="w-full max-w-md" />
          ) : sub.has_audio ? (
            <AdminButton size="sm" variant="secondary" onClick={loadAudio}>
              <Play size={14} /> Anhören
            </AdminButton>
          ) : (
            <p className="text-[var(--admin-text-muted)]">Keine Aufnahme.</p>
          )}
          {sub.transcript && (
            <div>
              <p className="mb-1 text-xs font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">Transkript (STT)</p>
              <p className="whitespace-pre-wrap rounded-xl bg-white/[0.03] p-3 text-[var(--admin-text-primary)] ring-1 ring-[var(--admin-border)]">{sub.transcript}</p>
            </div>
          )}
        </div>
      )}

      {sub.evaluation_error && <p className="text-xs text-[var(--admin-danger)]">Letzter Fehler: {sub.evaluation_error}</p>}

      {ev?.criteria && (
        <div className="space-y-2">
          <p className="text-xs font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">
            KI-Bewertung: {sub.ai_score ?? "—"} / 100
          </p>
          <ul className="grid gap-1.5 sm:grid-cols-2">
            {ev.criteria.map((c) => (
              <li key={c.key} className="rounded-lg bg-white/[0.03] px-3 py-2 ring-1 ring-[var(--admin-border)]">
                <div className="flex justify-between gap-2">
                  <span className="text-[var(--admin-text-primary)]">{c.name}</span>
                  <span className="font-bold tabular-nums text-[var(--admin-text-primary)]">
                    {c.status === "assessed" ? `${c.score} / ${c.max}` : "nicht bewertet"}
                  </span>
                </div>
                {c.comment && <p className="mt-0.5 text-xs text-[var(--admin-text-muted)]">{c.comment}</p>}
              </li>
            ))}
          </ul>
          {!!ev.errors?.length && (
            <ul className="space-y-1 text-xs">
              {ev.errors.map((e, i) => (
                <li key={i} className="text-[var(--admin-text-secondary)]">
                  <span className="text-[var(--admin-danger)] line-through">{e.original}</span> → <span className="font-semibold text-emerald-400">{e.correction}</span>
                  {e.explanation && <> — {e.explanation}</>}
                </li>
              ))}
            </ul>
          )}
          {ev.recommendation && <p className="text-xs text-[var(--admin-text-secondary)]">Empfehlung: {ev.recommendation}</p>}
          {!!ev.limitations?.length && <p className="text-xs text-[var(--admin-text-muted)]">ⓘ {ev.limitations.join(" ")}</p>}
        </div>
      )}

      <div className="space-y-2 rounded-xl bg-white/[0.03] p-3 ring-1 ring-[var(--admin-border)]">
        <p className="text-xs font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">Punktzahl korrigieren</p>
        <div className="flex flex-wrap gap-2">
          <AdminInput className="w-24" type="number" min={0} max={100} value={score} onChange={(e) => setScore(e.target.value)} aria-label="Punktzahl" data-testid="override-score" />
          <div className="min-w-48 flex-1">
            <AdminInput value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Grund (für den Verlauf)" />
          </div>
        </div>
        <AdminTextarea rows={2} value={feedback} onChange={(e) => setFeedback(e.target.value)} placeholder="Feedback für den Schüler (optional)" />
        <div className="flex flex-wrap gap-2">
          <AdminButton size="sm" onClick={saveOverride} disabled={busy || score === ""} data-testid="override-save">
            Speichern
          </AdminButton>
          <AdminButton size="sm" variant="secondary" onClick={reevaluate} disabled={busy || sub.status === "EVALUATING"} data-testid="reevaluate">
            <RefreshCw size={13} /> KI neu bewerten
          </AdminButton>
        </div>
        {message && <p className="text-xs text-[var(--admin-text-secondary)]" role="status">{message}</p>}
      </div>

      {sub.history.length > 0 && (
        <div>
          <p className="mb-1 flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">
            <History size={12} /> Verlauf
          </p>
          <ul className="space-y-1 text-xs text-[var(--admin-text-secondary)]" data-testid="admin-history">
            {sub.history.map((h) => (
              <li key={h.id}>
                {fmtDate(h.created_at)} · {h.source === "AI" ? `KI${h.model ? ` (${h.model})` : ""}` : "Manuell"} · {h.status}
                {h.score != null && <> · {h.score}/100</>}
                {h.source === "MANUAL_OVERRIDE" && h.result?.previous_score != null && <> (vorher {h.result.previous_score})</>}
                {h.result?.reason && <> · „{h.result.reason}“</>}
                {h.error && <span className="text-[var(--admin-danger)]"> · {h.error}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

/** "O'quvchilar natijalari": per-student skill results of this lesson and
 * every Schreiben / Sprechen submission with its AI evaluation, manual
 * score correction (audited) and re-evaluation. */
export default function SkillResultsAdmin({ lessonId }: { lessonId: string }) {
  const queryClient = useQueryClient();
  const key = ["admin-lesson-skill-results", lessonId];
  const { data, isLoading, isError } = useQuery({
    queryKey: key,
    queryFn: () => getLessonSkillsResults(lessonId),
    refetchInterval: (q) =>
      q.state.data?.submissions.some((s) => s.status === "SUBMITTED" || s.status === "EVALUATING") ? 5000 : false,
  });
  const [open, setOpen] = useState<string | null>(null);
  const [kind, setKind] = useState("");
  const [status, setStatus] = useState("");

  const submissions = (data?.submissions ?? []).filter((s) => (!kind || s.kind === kind) && (!status || s.status === status));
  const refresh = () => queryClient.invalidateQueries({ queryKey: key });

  if (isLoading) return <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>;
  if (isError || !data) return <p className="text-sm text-[var(--admin-danger)]">Ergebnisse konnten nicht geladen werden.</p>;

  return (
    <div className="space-y-6" data-testid="admin-skill-results">
      <section className="space-y-3">
        <h3 className="text-base font-bold text-[var(--admin-text-primary)]">Ergebnisse nach Fertigkeiten</h3>
        <StudentsTable students={data.students} />
      </section>

      <section className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h3 className="text-base font-bold text-[var(--admin-text-primary)]">Schreiben / Sprechen Abgaben</h3>
          <div className="flex gap-2">
            <AdminSelect value={kind} onChange={(e) => setKind(e.target.value)} aria-label="Fertigkeit">
              <option value="">Alle</option>
              <option value="WRITING">Schreiben</option>
              <option value="SPEAKING">Sprechen</option>
            </AdminSelect>
            <AdminSelect value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Status">
              <option value="">Jeder Status</option>
              {["SUBMITTED", "EVALUATING", "GRADED", "EVALUATION_FAILED", "NEEDS_REVISION"].map((s) => (
                <option key={s} value={s}>{STATUS_LABEL[s]}</option>
              ))}
            </AdminSelect>
          </div>
        </div>

        {submissions.length === 0 ? (
          <p className="text-sm text-[var(--admin-text-muted)]">Keine Abgaben.</p>
        ) : (
          <div className="overflow-x-auto rounded-2xl bg-[var(--admin-card)] ring-1 ring-[var(--admin-border)]">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead>
                <tr className="border-b border-[var(--admin-border)] text-xs uppercase tracking-wide text-[var(--admin-text-muted)]">
                  <th className="w-8 px-3 py-3" />
                  <th className="px-3 py-3">Schüler</th>
                  <th className="px-3 py-3">Aufgabe</th>
                  <th className="px-3 py-3">Status</th>
                  <th className="px-3 py-3">Punkte</th>
                  <th className="px-3 py-3">KI</th>
                  <th className="px-3 py-3">Versuch</th>
                  <th className="px-3 py-3">Eingereicht</th>
                </tr>
              </thead>
              <tbody>
                {submissions.map((s) => {
                  const isOpen = open === s.id;
                  return (
                    <Fragment key={s.id}>
                      <tr
                        className="cursor-pointer border-b border-[var(--admin-border)] hover:bg-white/[0.02]"
                        onClick={() => setOpen(isOpen ? null : s.id)}
                        data-testid="admin-submission-row"
                      >
                        <td className="px-3 py-3 text-[var(--admin-text-muted)]">{isOpen ? <ChevronDown size={15} /> : <ChevronRight size={15} />}</td>
                        <td className="px-3 py-3 font-semibold text-[var(--admin-text-primary)]">{s.student_name}</td>
                        <td className="px-3 py-3 text-[var(--admin-text-secondary)]">
                          {s.kind === "WRITING" ? "Schreiben" : "Sprechen"} · {s.task_title}
                        </td>
                        <td className={`px-3 py-3 text-xs font-semibold ${STATUS_TONE[s.status] ?? "text-[var(--admin-text-secondary)]"}`}>{STATUS_LABEL[s.status] ?? s.status}</td>
                        <td className="px-3 py-3 font-bold tabular-nums text-[var(--admin-text-primary)]">{s.score ?? "—"}</td>
                        <td className="px-3 py-3 tabular-nums text-[var(--admin-text-secondary)]">{s.ai_score ?? "—"}</td>
                        <td className="px-3 py-3 tabular-nums text-[var(--admin-text-secondary)]">{s.attempt_count || 1}</td>
                        <td className="px-3 py-3 text-xs text-[var(--admin-text-muted)]">{fmtDate(s.submitted_at)}</td>
                      </tr>
                      {isOpen && (
                        <tr className="border-b border-[var(--admin-border)] bg-black/10">
                          <td colSpan={8}>
                            <SubmissionDetail key={`${s.id}-${s.score}-${s.history.length}`} sub={s} onChanged={refresh} />
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
