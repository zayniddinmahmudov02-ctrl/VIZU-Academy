"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft, ArrowRight, CheckCircle2, ChevronLeft, ChevronRight, Flag, Loader2, RotateCcw, Save, Send } from "lucide-react";

import { AdminButton, AdminInput, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import { apiErrorMessage, getListeningAudioBlobUrl } from "@/features/admin/services/lesson-skills-admin-service";
import {
  getLoesungTask, publishLoesungTask, saveLoesungQuestion, taskHref,
  type KeyQuestion, type LoesungDetail, type LoesungKind, type SaveKeyInput,
} from "@/features/admin/services/loesung-service";

import { AudioBadge, KeyStatusBadge, PublishBadge } from "./loesung-badges";

const card = "rounded-2xl bg-[var(--admin-card)] p-4 ring-1 ring-[var(--admin-border)] sm:p-5";
const GAP_RE = /\[\[([A-Za-z0-9_-]{1,20})\]\]/g;

type Gap = { accepted: string; options: string[] };
type Draft = {
  options: { id: string; text: string; is_correct: boolean }[];
  gaps: Record<string, Gap>;
  pairs: Record<string, string>;
  accepted: string;
  explanation: string;
  note: string;
};

function toDraft(q: KeyQuestion): Draft {
  const cfg = (q.config ?? {}) as Record<string, unknown>;
  const gaps: Record<string, Gap> = {};
  if (q.question_type === "GAP_FILL") {
    const raw = (cfg.gaps ?? {}) as Record<string, unknown>;
    for (const m of String(cfg.text ?? "").matchAll(GAP_RE)) {
      const g = raw[m[1]];
      const obj: { accepted?: string[]; options?: string[] } = Array.isArray(g) ? { accepted: g as string[] } : ((g ?? {}) as { accepted?: string[]; options?: string[] });
      gaps[m[1]] = { accepted: (obj.accepted ?? []).join(" | "), options: obj.options ?? [] };
    }
  }
  return {
    options: q.options.map((o) => ({ ...o })),
    gaps,
    pairs: { ...((cfg.pairs ?? {}) as Record<string, string>) },
    accepted: ((cfg.accepted ?? []) as string[]).join(" | "),
    explanation: q.explanation ?? "",
    note: q.note ?? "",
  };
}

function split(v: string): string[] {
  return v.split("|").map((s) => s.trim()).filter(Boolean);
}

function toPayload(q: KeyQuestion, d: Draft): SaveKeyInput {
  const cfg = (q.config ?? {}) as Record<string, unknown>;
  const out: SaveKeyInput = { explanation: d.explanation.trim() || null, note: d.note.trim() || null };
  if (q.question_type === "MULTIPLE_CHOICE" || q.question_type === "TRUE_FALSE") out.options = d.options;
  else if (q.question_type === "GAP_FILL") {
    out.config = {
      text: cfg.text, case_sensitive: Boolean(cfg.case_sensitive),
      gaps: Object.fromEntries(Object.entries(d.gaps).map(([id, g]) => [id, { accepted: split(g.accepted), ...(g.options.length ? { options: g.options } : {}) }])),
    };
  } else if (q.question_type === "MATCHING") out.config = { items: cfg.items, targets: cfg.targets, pairs: d.pairs };
  else if (q.question_type === "SHORT_ANSWER") out.config = { accepted: split(d.accepted), case_sensitive: Boolean(cfg.case_sensitive), max_length: cfg.max_length ?? 100 };
  return out;
}

/** One Lesen / Hören Aufgabe: text or audio, every question with its answer
 * key, per-question save + manual verification, validation report and the
 * publish button (server decides; saving never publishes). */
export default function LoesungEditorClient({ kind, id }: { kind: LoesungKind; id: string }) {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({ queryKey: ["loesung", "task", kind, id], queryFn: () => getLoesungTask(kind, id) });
  const [index, setIndex] = useState(0);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  function update(next: LoesungDetail) {
    queryClient.setQueryData(["loesung", "task", kind, id], next);
    queryClient.invalidateQueries({ queryKey: ["loesung", "overview"] });
  }

  async function publish() {
    setBusy(true);
    setMsg(null);
    try {
      update(await publishLoesungTask(kind, id));
      setMsg({ ok: true, text: "Veröffentlicht (über die bestehende Veröffentlichung der Aufgabe)." });
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: { problems?: { message: string }[] } } } })?.response?.data?.detail;
      setMsg({ ok: false, text: detail?.problems ? detail.problems.map((p) => p.message).join(" · ") : apiErrorMessage(err, "Veröffentlichen fehlgeschlagen.") });
    } finally {
      setBusy(false);
    }
  }

  if (isLoading) return <p className="py-10 text-center text-sm text-[var(--admin-text-muted)]">Lädt …</p>;
  if (error || !data) return <p className="text-sm text-[var(--admin-danger)]">{apiErrorMessage(error, "Aufgabe konnte nicht geladen werden.")}</p>;

  const q = data.questions[Math.min(index, Math.max(0, data.questions.length - 1))];
  const isLast = index >= data.questions.length - 1;

  return (
    <div className="space-y-5" data-testid="loesung-editor">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <Link href="/admin/lms/loesung" className="inline-flex items-center gap-1 text-[var(--admin-text-secondary)] hover:text-[var(--admin-primary)]">
          <ArrowLeft size={15} /> Lösung
        </Link>
        <span className="ml-auto flex flex-wrap gap-2">
          {data.previous && <Link href={taskHref(data.previous.kind, data.previous.id)}><AdminButton size="sm" variant="ghost"><ChevronLeft size={14} /> Vorherige Aufgabe</AdminButton></Link>}
          {data.next && <Link href={taskHref(data.next.kind, data.next.id)}><AdminButton size="sm" variant="ghost">Nächste Aufgabe <ChevronRight size={14} /></AdminButton></Link>}
          {data.next_incomplete && (
            <Link href={taskHref(data.next_incomplete.kind, data.next_incomplete.id)} data-testid="loesung-next-incomplete">
              <AdminButton size="sm" variant="secondary"><ArrowRight size={14} /> Nächste offene Aufgabe</AdminButton>
            </Link>
          )}
        </span>
      </div>

      <header className={card}>
        <p className="text-xs text-[var(--admin-text-muted)]">
          {data.level} · Lektion {data.lesson_number}: {data.lesson_title} · {kind === "hoeren" ? "Hören" : "Lesen"}
        </p>
        <h1 className="text-xl font-bold text-[var(--admin-text-primary)]">{data.title}</h1>
        <div className="mt-2 flex flex-wrap gap-1.5">
          <KeyStatusBadge status={data.key_status} />
          {kind === "hoeren" && <AudioBadge audio={data.audio} />}
          <PublishBadge published={data.is_published} ready={data.ready_to_publish} />
          <span className="text-xs text-[var(--admin-text-secondary)]">{data.questions.length} Fragen · {data.with_key} mit Lösung · {data.verified} geprüft</span>
        </div>
        {data.import?.note && (
          <p className="mt-3 rounded-xl bg-[var(--admin-warning)]/10 p-3 text-sm text-[var(--admin-warning)]" data-testid="loesung-import-note">
            <AlertTriangle size={14} className="mr-1 inline" />Hinweis aus dem Import{data.import.book_page ? ` (Buch S. ${data.import.book_page})` : ""}: {data.import.note}
          </p>
        )}
      </header>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
        <section className={`${card} space-y-3 lg:sticky lg:top-4 lg:max-h-[85vh] lg:overflow-auto`}>
          {data.instruction && <p className="text-sm font-semibold text-[var(--admin-text-primary)]">{data.instruction}</p>}
          {kind === "hoeren" ? <AudioBlock detail={data} /> : (
            <div className="prose-editor text-sm text-[var(--admin-text-primary)]" data-testid="loesung-text"
                 dangerouslySetInnerHTML={{ __html: (data.content ?? "").replace(/<\s*(script|style|iframe)[\s\S]*?<\/\s*\1\s*>/gi, "") }} />
          )}
          {kind === "hoeren" && data.transcript && (
            <details className="text-sm"><summary className="cursor-pointer text-[var(--admin-text-secondary)]">Transkript</summary>
              <p className="mt-2 whitespace-pre-line text-[var(--admin-text-secondary)]">{data.transcript}</p></details>
          )}
        </section>

        <section className="space-y-4">
          <div className="flex flex-wrap gap-1.5" data-testid="loesung-question-strip">
            {data.questions.map((x, i) => (
              <button key={x.id} onClick={() => setIndex(i)} aria-label={`Frage ${x.number}`}
                      className={`h-8 min-w-8 rounded-lg px-2 text-xs font-bold ring-1 ${i === index ? "ring-2 ring-[var(--admin-primary)]" : "ring-[var(--admin-border)]"} ${
                        !x.has_key ? "bg-[var(--admin-danger)]/15 text-[var(--admin-danger)]" : x.needs_review ? "bg-[var(--admin-warning)]/20 text-[var(--admin-warning)]"
                          : x.verified ? "bg-[var(--admin-success)]/15 text-[var(--admin-success)]" : "bg-[var(--admin-hover)] text-[var(--admin-text-secondary)]"}`}>
                {x.number}
              </button>
            ))}
          </div>
          {q ? (
            // keyed by the saved state: after a save the server-normalised question replaces the draft
            <QuestionEditor key={`${q.id}:${JSON.stringify([q.options, q.config, q.explanation, q.note, q.verified, q.needs_review])}`} kind={kind} taskId={id} question={q} isLast={isLast} onSaved={update}
                            onPrev={index > 0 ? () => setIndex(index - 1) : undefined} onNext={!isLast ? () => setIndex(index + 1) : undefined} />
          ) : <p className={card}>Diese Aufgabe hat keine Fragen.</p>}

          <div className={`${card} space-y-3`} data-testid="loesung-validation">
            <h2 className="text-sm font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">Prüfbericht</h2>
            {data.validation.ready ? (
              <p className="text-sm text-[var(--admin-success)]"><CheckCircle2 size={14} className="mr-1 inline" />Alle Anforderungen erfüllt.</p>
            ) : (
              <ul className="max-h-48 space-y-1 overflow-auto text-sm text-[var(--admin-text-secondary)]">
                {data.validation.problems.map((p, i) => (
                  <li key={i}>
                    {p.question ? <button className="font-semibold text-[var(--admin-primary)] hover:underline" onClick={() => setIndex(p.question! - 1)}>{p.message}</button> : p.message}
                  </li>
                ))}
              </ul>
            )}
            {!data.is_published && (
              <AdminButton onClick={publish} disabled={busy || !data.validation.ready} data-testid="loesung-publish">
                {busy ? <Loader2 size={15} className="animate-spin" /> : <Send size={15} />} Veröffentlichen
              </AdminButton>
            )}
            {msg && <p role="status" className={`text-sm ${msg.ok ? "text-[var(--admin-success)]" : "text-[var(--admin-danger)]"}`}>{msg.text}</p>}
          </div>
        </section>
      </div>
    </div>
  );
}

function AudioBlock({ detail }: { detail: LoesungDetail }) {
  const [url, setUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState<string | null>(null);
  const playable = detail.audio === "ok";
  useEffect(() => {
    if (!playable) return;
    let created: string | null = null;
    getListeningAudioBlobUrl(detail.id).then((u) => { created = u; setUrl(u); }).catch(() => setFailed("Audio konnte nicht geladen werden."));
    return () => { if (created) URL.revokeObjectURL(created); };
  }, [detail.id, playable]);
  if (!playable) {
    return (
      <p className="rounded-xl bg-[var(--admin-danger)]/10 p-3 text-sm text-[var(--admin-danger)]" data-testid="loesung-audio-missing">
        <AlertTriangle size={14} className="mr-1 inline" />
        {detail.audio === "file_missing" ? "Die Audiodatei fehlt auf dem Server." : detail.audio === "external" ? "Nur ein externer Audio-Link ist hinterlegt." : "Für diese Aufgabe ist kein Audio hochgeladen."}
        {" "}Audio unter Media Management hochladen.
      </p>
    );
  }
  return (
    <div className="space-y-1" data-testid="loesung-audio">
      {url ? <audio src={url} controls className="w-full" onError={() => setFailed("Die Audiodatei lässt sich nicht abspielen.")} /> : !failed && <Loader2 size={16} className="animate-spin" />}
      <p className="text-xs text-[var(--admin-text-muted)]">{detail.audio_name}{detail.audio_duration ? ` · ${Math.round(detail.audio_duration / 60)} min` : ""}</p>
      {failed && <p className="text-sm text-[var(--admin-danger)]">{failed}</p>}
    </div>
  );
}

function QuestionEditor({ kind, taskId, question: q, isLast, onSaved, onPrev, onNext }: {
  kind: LoesungKind; taskId: string; question: KeyQuestion; isLast: boolean; onSaved: (d: LoesungDetail) => void; onPrev?: () => void; onNext?: () => void;
}) {
  const initial = useMemo(() => toDraft(q), [q]);
  const [d, setD] = useState<Draft>(initial);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const dirty = JSON.stringify(d) !== JSON.stringify(initial);
  const cfg = (q.config ?? {}) as Record<string, unknown>;

  async function save(review?: SaveKeyInput["review"], thenNext = false) {
    setBusy(true);
    setMsg(null);
    try {
      const payload = toPayload(q, d);
      // a note-only save of a question without a key must not run the key validation
      if (!q.has_key && !dirtyKey()) { delete payload.options; delete payload.config; }
      const next = await saveLoesungQuestion(kind, taskId, q.id, { ...payload, ...(review ? { review } : {}) });
      onSaved(next);
      setMsg({ ok: true, text: review === "verified" ? "Gespeichert und bestätigt." : review === "needs_review" ? "Als „prüfen“ markiert." : "Gespeichert." });
      if (thenNext && onNext) onNext();
    } catch (err) {
      setMsg({ ok: false, text: apiErrorMessage(err, "Speichern fehlgeschlagen.") });
    } finally {
      setBusy(false);
    }
  }
  function dirtyKey() {
    return JSON.stringify([d.options, d.gaps, d.pairs, d.accepted]) !== JSON.stringify([initial.options, initial.gaps, initial.pairs, initial.accepted]);
  }

  return (
    <div className={`${card} space-y-4`} data-testid="loesung-question" data-qtype={q.question_type}>
      <div className="flex flex-wrap items-start gap-2">
        <p className="mr-auto text-sm font-semibold text-[var(--admin-text-primary)]">Frage {q.number}: {q.question}</p>
        {!q.has_key ? <Tag cls="bad">Lösung fehlt</Tag> : q.verified ? <Tag cls="ok">Geprüft</Tag> : q.verification_outdated ? <Tag cls="warn">Nach Prüfung geändert</Tag> : <Tag cls="muted">Nicht geprüft</Tag>}
        {q.needs_review && <Tag cls="warn">Prüfen</Tag>}
      </div>
      {q.key_problem && q.has_key === false && <p className="text-xs text-[var(--admin-danger)]">{q.key_problem}</p>}

      {(q.question_type === "MULTIPLE_CHOICE" || q.question_type === "TRUE_FALSE") && (
        <div className="space-y-2">
          {d.options.map((o, i) => (
            <label key={o.id} className={`flex items-center gap-2 rounded-xl p-2 ring-1 ${o.is_correct ? "bg-[var(--admin-success)]/10 ring-[var(--admin-success)]" : "ring-[var(--admin-border)]"}`}>
              <input type="radio" name={`q-${q.id}`} checked={o.is_correct} onChange={() => setD({ ...d, options: d.options.map((x) => ({ ...x, is_correct: x.id === o.id })) })}
                     aria-label={`Option ${String.fromCharCode(65 + i)} ist richtig`} />
              <span className="w-5 text-xs font-bold text-[var(--admin-text-muted)]">{String.fromCharCode(65 + i)}</span>
              <AdminInput value={o.text} maxLength={500} onChange={(e) => setD({ ...d, options: d.options.map((x) => (x.id === o.id ? { ...x, text: e.target.value } : x)) })} />
            </label>
          ))}
        </div>
      )}

      {q.question_type === "GAP_FILL" && (
        <div className="space-y-3">
          <p className="whitespace-pre-line rounded-xl bg-[var(--admin-hover)] p-3 text-sm text-[var(--admin-text-primary)]">{String(cfg.text ?? "")}</p>
          {Object.entries(d.gaps).map(([gid, g]) => (
            <div key={gid} className="flex flex-wrap items-center gap-2">
              <span className="w-14 text-xs font-bold text-[var(--admin-text-muted)]">[[{gid}]]</span>
              {g.options.length > 0 ? (
                <AdminSelect className="w-56" value={split(g.accepted)[0] ?? ""} onChange={(e) => setD({ ...d, gaps: { ...d.gaps, [gid]: { ...g, accepted: e.target.value } } })} aria-label={`Lücke ${gid}`}>
                  <option value="">— Lösung wählen —</option>
                  {g.options.map((o) => <option key={o} value={o}>{o}</option>)}
                </AdminSelect>
              ) : (
                <AdminInput className="max-w-sm flex-1" placeholder="Richtige Antwort (Varianten mit | trennen)" value={g.accepted} aria-label={`Lücke ${gid}`}
                            onChange={(e) => setD({ ...d, gaps: { ...d.gaps, [gid]: { ...g, accepted: e.target.value } } })} />
              )}
            </div>
          ))}
        </div>
      )}

      {q.question_type === "MATCHING" && (
        <div className="space-y-2">
          {((cfg.items ?? []) as { id: string; text: string }[]).map((it) => (
            <div key={it.id} className="flex flex-wrap items-center gap-2 text-sm">
              <span className="min-w-0 flex-1 text-[var(--admin-text-primary)]">{it.id}. {it.text}</span>
              <AdminSelect className="w-64" value={d.pairs[it.id] ?? ""} onChange={(e) => setD({ ...d, pairs: { ...d.pairs, [it.id]: e.target.value } })} aria-label={`Zuordnung ${it.id}`}>
                <option value="">— wählen —</option>
                {((cfg.targets ?? []) as { id: string; text: string }[]).map((t) => <option key={t.id} value={t.id}>{t.id}) {t.text}</option>)}
              </AdminSelect>
            </div>
          ))}
        </div>
      )}

      {q.question_type === "SHORT_ANSWER" && (
        <AdminInput placeholder="Akzeptierte Antworten (mit | trennen)" value={d.accepted} onChange={(e) => setD({ ...d, accepted: e.target.value })} />
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="text-xs text-[var(--admin-text-muted)]">Erklärung (für Lernende nach der Abgabe)
          <AdminTextarea rows={2} maxLength={2000} value={d.explanation} onChange={(e) => setD({ ...d, explanation: e.target.value })} />
        </label>
        <label className="text-xs text-[var(--admin-text-muted)]">Prüfnotiz / Quelle (nur Admin)
          <AdminTextarea rows={2} maxLength={2000} value={d.note} onChange={(e) => setD({ ...d, note: e.target.value })} data-testid="loesung-note" />
        </label>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <AdminButton size="sm" variant="secondary" disabled={busy || !dirty} onClick={() => save()} data-testid="loesung-save"><Save size={14} /> Speichern</AdminButton>
        <AdminButton size="sm" disabled={busy} onClick={() => save("verified", true)} data-testid="loesung-verify">
          <CheckCircle2 size={14} /> {isLast ? "Speichern & bestätigen" : "Bestätigen & weiter"}
        </AdminButton>
        <AdminButton size="sm" variant="ghost" disabled={busy} onClick={() => save("needs_review")} data-testid="loesung-flag"><Flag size={14} /> Als „prüfen“ markieren</AdminButton>
        {(q.verified || q.needs_review) && (
          <AdminButton size="sm" variant="ghost" disabled={busy} onClick={() => save("unverified")}><RotateCcw size={14} /> Status zurücksetzen</AdminButton>
        )}
        <span className="ml-auto flex gap-1">
          <AdminButton size="sm" variant="ghost" disabled={!onPrev} onClick={onPrev} aria-label="Vorherige Frage"><ChevronLeft size={14} /></AdminButton>
          <AdminButton size="sm" variant="ghost" disabled={!onNext} onClick={onNext} aria-label="Nächste Frage"><ChevronRight size={14} /></AdminButton>
        </span>
      </div>
      {dirty && <p className="text-xs text-[var(--admin-warning)]">Ungespeicherte Änderungen.</p>}
      {msg && <p role="status" className={`text-sm ${msg.ok ? "text-[var(--admin-success)]" : "text-[var(--admin-danger)]"}`} data-testid="loesung-question-msg">{msg.text}</p>}
    </div>
  );
}

function Tag({ cls, children }: { cls: "ok" | "warn" | "bad" | "muted"; children: React.ReactNode }) {
  const tone = { ok: "bg-[var(--admin-success)]/15 text-[var(--admin-success)]", warn: "bg-[var(--admin-warning)]/15 text-[var(--admin-warning)]",
                 bad: "bg-[var(--admin-danger)]/15 text-[var(--admin-danger)]", muted: "bg-[var(--admin-hover)] text-[var(--admin-text-secondary)]" }[cls];
  return <span className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${tone}`}>{children}</span>;
}
