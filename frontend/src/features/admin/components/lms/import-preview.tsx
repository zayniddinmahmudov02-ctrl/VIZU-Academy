"use client";

import { useState } from "react";
import Link from "next/link";
import { AlertTriangle, CheckCircle2, ChevronDown, XCircle } from "lucide-react";

import type { AdminQuestion } from "@/features/admin/services/lesson-skills-admin-service";
import { SKILL_LABELS, type ImportItemReport, type ImportPreview, type SkillKey } from "@/features/admin/services/lms-service";

const TYPE_LABEL: Record<string, string> = {
  MULTIPLE_CHOICE: "Multiple Choice",
  TRUE_FALSE: "Richtig / Falsch",
  MATCHING: "Zuordnung",
  GAP_FILL: "Lückentext",
  SHORT_ANSWER: "Kurzantwort",
};

export function skillLabel(skill: string | null | undefined) {
  return skill && skill in SKILL_LABELS ? SKILL_LABELS[skill as SkillKey] : (skill ?? "?");
}

function QuestionKey({ q }: { q: AdminQuestion }) {
  const c = q.config ?? {};
  if (q.question_type === "MATCHING") {
    const target = (id: string) => c.targets?.find((t) => t.id === id)?.text ?? id;
    return (
      <ul className="mt-1 space-y-0.5">
        {(c.items ?? []).map((i) => (
          <li key={i.id}>
            {i.id}. {i.text} → <b className="text-[var(--admin-accent)]">{c.pairs?.[i.id]}) {target(c.pairs?.[i.id] ?? "")}</b>
          </li>
        ))}
        {(c.targets ?? []).length > (c.items ?? []).length && (
          <li className="text-[var(--admin-text-muted)]">
            Distraktoren: {(c.targets ?? []).filter((t) => !Object.values(c.pairs ?? {}).includes(t.id)).map((t) => `${t.id}) ${t.text}`).join(", ")}
          </li>
        )}
      </ul>
    );
  }
  if (q.question_type === "GAP_FILL") {
    return (
      <div className="mt-1 space-y-0.5">
        <p className="italic">{c.text}</p>
        {Object.entries(c.gaps ?? {}).map(([id, g]) => (
          <p key={id}>
            [[{id}]] → <b className="text-[var(--admin-accent)]">{g.accepted.join(" | ")}</b>
            {g.options ? <span className="text-[var(--admin-text-muted)]"> · Auswahl: {g.options.join(", ")}</span> : null}
          </p>
        ))}
      </div>
    );
  }
  if (q.question_type === "SHORT_ANSWER") {
    return (
      <p className="mt-1">
        Akzeptiert: <b className="text-[var(--admin-accent)]">{(c.accepted ?? []).join(" | ")}</b>
      </p>
    );
  }
  return (
    <ul className="mt-1 space-y-0.5">
      {q.options.map((o, i) => (
        <li key={i} className={o.is_correct ? "font-semibold text-[var(--admin-accent)]" : ""}>
          {q.question_type === "TRUE_FALSE" ? "" : `${String.fromCharCode(65 + i)}) `}
          {o.text} {o.is_correct && "✓"}
        </li>
      ))}
    </ul>
  );
}

function Preview({ skill, p }: { skill: string | null; p: ImportPreview }) {
  const row = "text-xs text-[var(--admin-text-secondary)]";
  return (
    <div className="mt-3 space-y-3 border-t border-[var(--admin-border)] pt-3 text-sm text-[var(--admin-text-primary)]">
      {p.instruction && <p className={row}><b>Anweisung:</b> {p.instruction}</p>}
      {p.passages?.map((x, i) => (
        <div key={i} className="rounded-lg bg-white/[0.03] p-3">
          <p className="font-semibold">{x.title}</p>
          <p className="mt-1 whitespace-pre-line text-xs text-[var(--admin-text-secondary)]">{x.text}</p>
        </div>
      ))}
      {skill === "hoeren" && (
        <div className={row}>
          <p><b>Audio:</b> {p.audio_hint ?? "—"} (nach dem Import im Hören-Tab der Lektion hochladen)</p>
          {p.transcript && <p className="mt-1 whitespace-pre-line"><b>Transkript:</b> {p.transcript}</p>}
        </div>
      )}
      {p.questions && (
        <ol className="space-y-2">
          {p.questions.map((q, i) => (
            <li key={i} className="rounded-lg bg-white/[0.03] p-3 text-xs">
              <p className="text-sm">
                <b>{i + 1}.</b> {q.question}
                <span className="ml-2 text-[var(--admin-text-muted)]">
                  {TYPE_LABEL[q.question_type] ?? q.question_type} · {q.points} P.{q.passage && skill === "lesen" ? ` · Text ${q.passage}` : ""}
                </span>
              </p>
              <QuestionKey q={q} />
              {q.explanation && <p className="mt-1 text-[var(--admin-text-muted)]">Erklärung: {q.explanation}</p>}
            </li>
          ))}
        </ol>
      )}
      {p.max_points !== undefined && <p className={row}>Summe: {p.max_points} Punkte → Ergebnis /100</p>}
      {p.prompt && <p className="whitespace-pre-line"><b>Aufgabe:</b> {p.prompt}</p>}
      {skill === "schreiben" && (
        <p className={row}>
          Textsorte: {p.task_type} · {p.min_words}–{p.max_words} Wörter{p.time_limit ? ` · ${p.time_limit} Min.` : ""}
          {p.audience ? ` · An: ${p.audience}` : ""}
          {p.support_phrases?.length ? ` · Redemittel: ${p.support_phrases.join(" / ")}` : ""}
        </p>
      )}
      {skill === "sprechen" && (
        <div className={row}>
          <p>
            {p.response_type === "dialog" ? "Dialog" : "Monolog"} · {p.min_duration}–{p.max_duration}s
            {p.preparation_time ? ` · Vorbereitung ${p.preparation_time}s` : ""}
            {p.topic ? ` · Thema: ${p.topic}` : ""}
          </p>
          {p.speech_goal && <p>Sprechziel: {p.speech_goal}</p>}
        </div>
      )}
      {p.key_pending ? <p className="text-xs text-[var(--admin-warning)]">{p.key_pending} Frage(n) ohne Lösung — nach dem Anhören festlegen.</p> : null}
      {p.rules?.map((r, i) => (
        <div key={i} className="rounded-lg bg-white/[0.03] p-3">
          <p className="font-semibold">Regel: {r.title}</p>
          {/* sanitized by the server's validation */}
          <div className="prose-editor mt-1 max-h-60 overflow-auto text-xs text-[var(--admin-text-secondary)]" dangerouslySetInnerHTML={{ __html: r.html }} />
        </div>
      ))}
      {p.exercises?.map((ex, i) => (
        <div key={i} className="rounded-lg bg-white/[0.03] p-3 text-xs">
          <p className="text-sm font-semibold">
            Übung: {ex.title} <span className="font-normal text-[var(--admin-text-muted)]">· {ex.questions.length} Fragen · {ex.max_points} P. · {ex.source === "book" ? "Buch" : "VIZU"}</span>
          </p>
          <ol className="mt-1 space-y-1">
            {ex.questions.map((q, n) => (
              <li key={n}>
                <b>{n + 1}.</b> {q.question} <span className="text-[var(--admin-text-muted)]">({TYPE_LABEL[q.question_type] ?? q.question_type})</span>
                <QuestionKey q={q} />
              </li>
            ))}
          </ol>
        </div>
      ))}
      {p.words && (
        <div className="rounded-lg bg-white/[0.03] p-3 text-xs">
          <p className="text-sm font-semibold">{p.words.length} Wörter{p.auto_practice ? ` · automatische Übung: ${p.auto_practice} Fragen` : ""}</p>
          <p className="mt-1 text-[var(--admin-text-secondary)]">
            {p.words.map((w) => `${w.article ? w.article + " " : ""}${w.word} — ${w.translation}`).join(" · ")}
          </p>
        </div>
      )}
      {p.rubric && (
        <p className={row}>
          Raster {p.rubric_is_default ? "(Standard des Niveaus)" : "(eigenes)"}: {p.rubric.map((c) => `${c.name} ${c.max}`).join(" · ")}
        </p>
      )}
    </div>
  );
}

/** One item of the validation report: status, target lesson, errors,
 * warnings and the normalised preview (incl. answer keys — admin only). */
export function ImportItemCard({ item }: { item: ImportItemReport }) {
  const [open, setOpen] = useState(false);
  const t = item.target;
  // Sprechen guiding questions are strings; Lesen/Hören questions objects
  const preview = item.preview;
  const speakingQuestions = (item.skill === "sprechen" || item.skill === "frage") && Array.isArray(preview?.questions)
    ? (preview?.questions as unknown as string[]) : null;
  const normalised = speakingQuestions && preview ? { ...preview, questions: undefined } : preview;
  return (
    <div
      className={`rounded-xl p-4 ring-1 ${item.valid ? "bg-white/[0.02] ring-[var(--admin-border)]" : "bg-[var(--admin-danger)]/[0.06] ring-[var(--admin-danger)]/40"}`}
      data-testid="import-item"
      data-valid={item.valid}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="flex flex-wrap items-center gap-2 text-sm font-semibold text-[var(--admin-text-primary)]">
            {item.valid ? <CheckCircle2 size={15} className="text-[var(--admin-accent)]" /> : <XCircle size={15} className="text-[var(--admin-danger)]" />}
            <span className="rounded bg-white/[0.06] px-1.5 py-0.5 text-[11px] font-bold">{item.level ?? "?"}</span>
            <span className="rounded bg-[var(--admin-primary)]/15 px-1.5 py-0.5 text-[11px] font-bold text-[var(--admin-primary)]">{skillLabel(item.skill)}</span>
            <span className="break-all">{item.title ?? "(ohne Titel)"}</span>
          </p>
          <p className="mt-1 text-xs text-[var(--admin-text-muted)]">
            #{item.index + 1} · {item.content_id ?? "keine content_id"}
            {t && (
              <>
                {" · "}Modul {t.module} · Lektion {t.lesson}
                {t.lesson_id ? (
                  <>
                    {" "}(
                    <Link href={`/admin/lessons/${t.lesson_id}`} className="text-[var(--admin-primary)] hover:underline">
                      {t.lesson_title}
                    </Link>
                    )
                  </>
                ) : t.create ? (
                  " (wird angelegt)"
                ) : null}
              </>
            )}
          </p>
        </div>
        {preview && (
          <button
            type="button"
            onClick={() => setOpen(!open)}
            className="inline-flex items-center gap-1 text-xs font-semibold text-[var(--admin-primary)]"
            aria-expanded={open}
            data-testid="import-item-toggle"
          >
            Vorschau <ChevronDown size={13} className={open ? "rotate-180 transition" : "transition"} />
          </button>
        )}
      </div>
      {item.skip && !item.errors.length && <p className="mt-2 text-xs text-[var(--admin-text-muted)]">Übersprungen: {item.skip}</p>}
      {item.errors.length > 0 && (
        <ul className="mt-2 space-y-0.5 text-xs text-[var(--admin-danger)]" data-testid="import-item-errors">
          {item.errors.map((e, i) => (
            <li key={i}>• {e}</li>
          ))}
        </ul>
      )}
      {item.warnings.length > 0 && (
        <ul className="mt-2 space-y-0.5 text-xs text-[var(--admin-warning)]">
          {item.warnings.map((w, i) => (
            <li key={i} className="flex gap-1">
              <AlertTriangle size={12} className="mt-0.5 shrink-0" /> {w}
            </li>
          ))}
        </ul>
      )}
      {open && normalised && (
        <>
          <Preview skill={item.skill} p={normalised} />
          {speakingQuestions && (
            <ol className="mt-2 list-decimal pl-5 text-xs text-[var(--admin-text-secondary)]">
              {speakingQuestions.map((q, i) => (
                <li key={i}>{q}</li>
              ))}
            </ol>
          )}
        </>
      )}
    </div>
  );
}
