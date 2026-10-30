"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronRight, RefreshCw } from "lucide-react";

import { AdminButton } from "@/components/admin/admin-ui";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import {
  getA2Processing,
  type A2PipelineStatus,
  type A2ProcessingQuestion,
  type A2ProcessingTask,
} from "@/features/admin/services/media-management-service";

const card = "rounded-2xl bg-[var(--admin-card)] p-4 ring-1 ring-[var(--admin-border)] sm:p-5";

export const PIPELINE: Record<A2PipelineStatus, { label: string; tone: string }> = {
  UPLOADED: { label: "Uploaded · hochgeladen", tone: "bg-[var(--admin-hover)] text-[var(--admin-text-secondary)]" },
  TRANSCRIBING: { label: "Transcribing · wird transkribiert", tone: "bg-[var(--admin-primary)]/15 text-[var(--admin-primary)]" },
  TRANSCRIBED: { label: "Transcribed · transkribiert", tone: "bg-[var(--admin-primary)]/15 text-[var(--admin-primary)]" },
  MATCHED: { label: "Matched · zugeordnet", tone: "bg-[var(--admin-primary)]/15 text-[var(--admin-primary)]" },
  ANSWER_KEY_VERIFIED: { label: "Answer key verified · Lösungen geprüft", tone: "bg-[var(--admin-success)]/15 text-[var(--admin-success)]" },
  PUBLISHED: { label: "Published · veröffentlicht", tone: "bg-[var(--admin-success)]/15 text-[var(--admin-success)]" },
  NEEDS_REVIEW: { label: "Needs review · Prüfung nötig", tone: "bg-[var(--admin-warning)]/15 text-[var(--admin-warning)]" },
  FAILED: { label: "Failed · Fehler", tone: "bg-[var(--admin-danger)]/15 text-[var(--admin-danger)]" },
};
const ORDER: A2PipelineStatus[] = ["PUBLISHED", "ANSWER_KEY_VERIFIED", "MATCHED", "TRANSCRIBED", "TRANSCRIBING", "UPLOADED", "NEEDS_REVIEW", "FAILED"];

function time(s: number | null | undefined) {
  if (s == null) return "—";
  const v = Math.round(s);
  return `${Math.floor(v / 60)}:${String(v % 60).padStart(2, "0")}`;
}

function Badge({ status }: { status: A2PipelineStatus }) {
  return <span className={`whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-semibold ${PIPELINE[status].tone}`} data-testid="a2p-status" data-status={status}>{PIPELINE[status].label}</span>;
}

/** The key of one question in words: the correct option, the accepted gap answers or the pairs. */
function keyText(q: A2ProcessingQuestion): string {
  const correct = q.options.filter((o) => o.is_correct).map((o) => o.text);
  if (correct.length) return correct.join(" / ");
  if (q.config?.gaps) return Object.entries(q.config.gaps).map(([id, g]) => `Lücke ${id}: ${(g.accepted ?? []).join(" | ") || "—"}`).join(" · ");
  if (q.config?.pairs) return Object.entries(q.config.pairs).map(([a, b]) => `${a}→${b}`).join(" ");
  return "—";
}

/** The note most questions share (the task's evidence) — shown once, not under every question. */
function sharedNote(questions: A2ProcessingQuestion[]): string | null {
  const counts = new Map<string, number>();
  for (const q of questions) if (q.note) counts.set(q.note, (counts.get(q.note) ?? 0) + 1);
  const [note, n] = [...counts.entries()].sort((a, b) => b[1] - a[1])[0] ?? [null, 0];
  return note && n > 1 ? note : null;
}

function QuestionRow({ q, shared }: { q: A2ProcessingQuestion; shared: string | null }) {
  const state = !q.has_key ? ["ohne Lösung", "text-[var(--admin-danger)]"] : q.needs_review ? ["Prüfung nötig", "text-[var(--admin-warning)]"]
    : q.verified ? ["geprüft", "text-[var(--admin-success)]"] : ["nicht geprüft", "text-[var(--admin-text-muted)]"];
  return (
    <li className="space-y-1 border-t border-[var(--admin-border)] py-2 first:border-t-0" data-testid="a2p-question">
      <p className="text-sm text-[var(--admin-text-primary)]"><b>{q.number}.</b> {q.question}{q.config?.text ? <span className="text-[var(--admin-text-secondary)]"> — {q.config.text}</span> : null}</p>
      {q.options.length > 0 && (
        <ul className="flex flex-wrap gap-1.5">
          {q.options.map((o, i) => (
            <li key={i} className={`rounded-md px-2 py-0.5 text-xs ring-1 ${o.is_correct ? "bg-[var(--admin-success)]/10 font-semibold text-[var(--admin-success)] ring-[var(--admin-success)]/40" : "text-[var(--admin-text-secondary)] ring-[var(--admin-border)]"}`}>
              {o.is_correct ? "✓ " : ""}{o.text}
            </li>
          ))}
        </ul>
      )}
      {q.options.length === 0 && <p className="text-xs text-[var(--admin-text-secondary)]">Lösung: {keyText(q)}</p>}
      <p className="text-xs"><span className={`font-semibold ${state[1]}`}>{state[0]}</span>{q.note && q.note !== shared ? <span className="text-[var(--admin-text-muted)]"> — {q.note}</span> : null}</p>
    </li>
  );
}

function TaskRow({ task }: { task: A2ProcessingTask }) {
  const [open, setOpen] = useState(false);
  return (
    <li className="rounded-xl ring-1 ring-[var(--admin-border)]" data-testid="a2p-task" data-status={task.status}>
      <button type="button" onClick={() => setOpen(!open)} className="flex w-full flex-wrap items-center gap-2 px-3 py-2.5 text-left" aria-expanded={open}>
        {open ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
        <span className="mr-auto min-w-0 flex-1 text-sm font-semibold text-[var(--admin-text-primary)]">{task.title}</span>
        <span className="text-xs text-[var(--admin-text-muted)]">
          {task.files.length} Audio · {task.keys.total ? `${task.keys.verified}/${task.keys.total} Lösungen geprüft` : "ohne Fragen"}
        </span>
        <Badge status={task.status} />
      </button>
      {task.problems.length > 0 && (
        <ul className="px-9 pb-2 text-xs text-[var(--admin-warning)]" data-testid="a2p-problems">{task.problems.map((p, i) => <li key={i}>• {p}</li>)}</ul>
      )}
      {open && (
        <div className="space-y-4 border-t border-[var(--admin-border)] px-3 py-3 sm:px-4" data-testid="a2p-details">
          <dl className="grid gap-x-4 gap-y-1 text-xs sm:grid-cols-[auto_1fr]">
            <dt className="text-[var(--admin-text-muted)]">Zuordnung</dt>
            <dd className="text-[var(--admin-text-secondary)]">{task.match ? `${task.match.status} — ${task.match.note ?? ""}` : "noch nicht verglichen"}</dd>
            <dt className="text-[var(--admin-text-muted)]">Veröffentlicht</dt>
            <dd className="text-[var(--admin-text-secondary)]">{task.is_published ? "ja — für Lernende sichtbar" : "nein (Entwurf)"}</dd>
            <dt className="text-[var(--admin-text-muted)]">Transkript für Lernende</dt>
            <dd className="text-[var(--admin-text-secondary)]">{task.student_transcript ? "gespeichert (nach dem ersten Versuch sichtbar)" : "keins"}</dd>
          </dl>
          {task.files.map((f) => (
            <div key={f.slot} className="space-y-1.5" data-testid="a2p-file">
              <p className="text-xs font-semibold text-[var(--admin-text-primary)]">
                {f.label ? `${f.label}: ` : ""}{f.name ?? "—"} · {time(f.duration_seconds ?? f.transcript?.duration_seconds)}
                {f.size_bytes ? ` · ${(f.size_bytes / 1048576).toFixed(1)} MB` : ""}{f.on_disk ? "" : " · Datei fehlt!"}
              </p>
              {f.transcript ? (
                <>
                  <p className="text-xs text-[var(--admin-text-muted)]">
                    {f.transcript.status} · {f.transcript.model}
                    {f.transcript.quality?.agreement != null ? ` · Übereinstimmung mit ${f.transcript.quality.second_model}: ${Math.round(f.transcript.quality.agreement * 100)} %` : ""}
                    {f.transcript.review_note ? ` · ${f.transcript.review_note}` : ""}
                  </p>
                  <div className="max-h-64 overflow-y-auto rounded-lg bg-[var(--admin-hover)] p-2.5 text-xs leading-relaxed text-[var(--admin-text-secondary)]" data-testid="a2p-transcript">
                    {(f.transcript.segments ?? []).map((s, i) => (
                      <p key={i}><span className="mr-2 font-mono text-[var(--admin-text-muted)]">[{time(s.start)}]</span>{s.text}</p>
                    ))}
                  </div>
                </>
              ) : <p className="text-xs text-[var(--admin-text-muted)]">Kein Transkript.</p>}
            </div>
          ))}
          {task.questions.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">Fragen und Lösungen</p>
              {sharedNote(task.questions) && (
                <p className="mb-2 rounded-lg bg-[var(--admin-hover)] p-2.5 text-xs text-[var(--admin-text-secondary)]" data-testid="a2p-evidence">
                  <b>Nachweis:</b> {sharedNote(task.questions)}
                </p>
              )}
              <ul>{task.questions.map((q) => <QuestionRow key={q.number} q={q} shared={sharedNote(task.questions)} />)}</ul>
            </div>
          )}
        </div>
      )}
    </li>
  );
}

/** Admin → Media Management → A2: every Hören audio of lessons 1-13 with its
 * transcript, the task it belongs to, questions and keys, and where it stands
 * (Uploaded … Published / Needs review / Failed). Read-only: keys are edited
 * in LMS → Lösung, audio in the A2 Audio Manager. */
export default function A2AudioProcessing() {
  const data = useQuery({ queryKey: ["a2-audio-processing"], queryFn: getA2Processing });
  const [openLessons, setOpenLessons] = useState<Set<number>>(new Set());
  const s = data.data?.summary;

  function toggle(n: number) {
    setOpenLessons((prev) => {
      const next = new Set(prev);
      if (next.has(n)) next.delete(n);
      else next.add(n);
      return next;
    });
  }

  return (
    <section className={`${card} space-y-4`} data-testid="a2-audio-processing">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="mr-auto text-sm font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">A2 Audio-Verarbeitung · 1.–13. Unterricht</h2>
        <AdminButton variant="ghost" size="sm" onClick={() => data.refetch()} aria-label="Aktualisieren"><RefreshCw size={14} /></AdminButton>
      </div>
      {data.isLoading && <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen …</p>}
      {data.isError && <p className="text-sm text-[var(--admin-danger)]" role="alert">{apiErrorMessage(data.error, "Konnte nicht geladen werden.")}</p>}
      {s && (
        <>
          <div className="space-y-2" data-testid="a2p-summary">
            <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1 text-sm text-[var(--admin-text-secondary)]">
              <span><b className="text-[var(--admin-text-primary)]">{s.published}/{s.tasks}</b> Hören-Aufgaben veröffentlicht ({s.percent_published} %)</span>
              <span>{s.audio_files} Audiodateien · {s.unique_contents} verschiedene Inhalte (SHA-256) · {s.transcribed} transkribiert</span>
              <span>{s.matched} zugeordnet · {s.keys_verified} mit allen Lösungen geprüft</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-[var(--admin-hover)]" aria-label={`${s.percent_published} % veröffentlicht`}>
              <div className="h-full bg-[var(--admin-success)]" style={{ width: `${s.percent_published}%` }} />
            </div>
            <div className="flex flex-wrap gap-1.5">
              {ORDER.filter((k) => s.by_status[k]).map((k) => (
                <span key={k} className={`rounded-full px-2.5 py-1 text-xs font-semibold ${PIPELINE[k].tone}`}>{PIPELINE[k].label}: {s.by_status[k]}</span>
              ))}
            </div>
          </div>
          <ul className="space-y-2">
            {data.data!.lessons.map((lesson) => {
              const open = openLessons.has(lesson.number);
              const waiting = lesson.tasks.filter((t) => t.status !== "PUBLISHED").length;
              return (
                <li key={lesson.number} className="rounded-xl bg-[var(--admin-hover)]/40" data-testid="a2p-lesson" data-lesson={lesson.number}>
                  <button type="button" onClick={() => toggle(lesson.number)} className="flex w-full flex-wrap items-center gap-2 px-3 py-2.5 text-left" aria-expanded={open}>
                    {open ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
                    <b className="text-sm text-[var(--admin-text-primary)]">{lesson.number}. Unterricht</b>
                    <span className="mr-auto min-w-0 truncate text-sm text-[var(--admin-text-secondary)]">{lesson.title}</span>
                    <span className={`text-xs font-semibold ${waiting ? "text-[var(--admin-warning)]" : "text-[var(--admin-success)]"}`}>
                      {lesson.published_tasks}/{lesson.task_count} veröffentlicht
                    </span>
                  </button>
                  {open && <ul className="space-y-2 px-2 pb-3 sm:px-3">{lesson.tasks.map((t) => <TaskRow key={t.listening_id} task={t} />)}</ul>}
                </li>
              );
            })}
          </ul>
          <p className="text-xs text-[var(--admin-text-muted)]">
            Ein Audio wird pro Inhalt (SHA-256) nur einmal transkribiert. Veröffentlicht wird nur, wenn das Audio auf dem Server liegt, das Transkript zur Aufgabe
            passt und jede Lösung geprüft ist. „Prüfung nötig“-Lösungen bearbeiten Sie in LMS → Lösung; ein falsches Audio ersetzen Sie im A2 Audio Manager.
          </p>
        </>
      )}
    </section>
  );
}
