"use client";

import { Plus, Trash2 } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminInput, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import type { AdminQuestion, AdminQuestionConfig, AdminQuestionType } from "@/features/admin/services/lesson-skills-admin-service";

export const CONFIG_QUESTION_TYPES: AdminQuestionType[] = ["MATCHING", "GAP_FILL", "SHORT_ANSWER"];
const GAP_PATTERN = /\[\[([A-Za-z0-9_-]{1,20})\]\]/g;
const LETTERS = "ABCDEFGHIJKLMNO";

export function gapIds(text: string): string[] {
  return [...text.matchAll(GAP_PATTERN)].map((m) => m[1]);
}

export function blankConfig(type: AdminQuestionType): AdminQuestionConfig | null {
  if (type === "MATCHING") {
    return {
      items: [{ id: "1", text: "" }, { id: "2", text: "" }],
      targets: [{ id: "A", text: "" }, { id: "B", text: "" }, { id: "C", text: "" }],
      pairs: { "1": "A", "2": "B" },
    };
  }
  if (type === "GAP_FILL") return { text: "Ich [[1]] Anna.", gaps: { "1": { accepted: [""] } }, case_sensitive: false };
  if (type === "SHORT_ANSWER") return { accepted: [""], case_sensitive: false, max_length: 100 };
  return null;
}

const clean = (values: string[] | undefined) => (values ?? []).map((v) => v.trim()).filter(Boolean);

/** Trims the free-typed lists before saving (they are edited raw so that a
 * separator can be typed). */
export function cleanConfig(q: AdminQuestion): AdminQuestionConfig | null {
  const c = q.config;
  if (!c) return null;
  if (q.question_type === "GAP_FILL") {
    const gaps: NonNullable<AdminQuestionConfig["gaps"]> = {};
    for (const id of gapIds(c.text ?? "")) {
      const g = c.gaps?.[id] ?? { accepted: [] };
      const options = clean(g.options);
      gaps[id] = options.length ? { accepted: clean(g.accepted), options } : { accepted: clean(g.accepted) };
    }
    return { text: c.text ?? "", gaps, case_sensitive: !!c.case_sensitive };
  }
  if (q.question_type === "SHORT_ANSWER") return { accepted: clean(c.accepted), case_sensitive: !!c.case_sensitive, max_length: c.max_length ?? 100 };
  return {
    items: (c.items ?? []).map((i) => ({ ...i, text: i.text.trim() })),
    targets: (c.targets ?? []).map((x) => ({ ...x, text: x.text.trim() })),
    pairs: c.pairs ?? {},
  };
}

/** Mirrors app/services/lesson_skills/question_types.validate_config. */
export function configProblem(q: AdminQuestion): string | null {
  const c = cleanConfig(q);
  if (!c) return "Konfiguration fehlt.";
  if (q.question_type === "MATCHING") {
    const items = c.items ?? [];
    const targets = c.targets ?? [];
    if (items.length < 2 || items.length > 12) return "Zuordnung: 2–12 Aussagen.";
    if (targets.length < items.length || targets.length > 15) return "Zuordnung: mindestens so viele Antworten wie Aussagen (max. 15).";
    if ([...items, ...targets].some((e) => !e.text)) return "Zuordnung: leerer Eintrag.";
    if (items.some((i) => !targets.some((x) => x.id === c.pairs?.[i.id]))) return "Zuordnung: jeder Aussage eine richtige Antwort zuordnen.";
    return null;
  }
  if (q.question_type === "GAP_FILL") {
    const ids = gapIds(c.text ?? "");
    if (!ids.length) return "Lückentext: mindestens eine Lücke [[1]] im Text.";
    if (new Set(ids).size !== ids.length) return "Lückentext: Lücken-Nummern müssen eindeutig sein.";
    for (const id of ids) {
      const g = c.gaps?.[id];
      if (!g?.accepted.length) return `Lückentext: Lücke [[${id}]] braucht eine richtige Antwort.`;
      if (g.options && g.options.length < 2) return `Lückentext: Lücke [[${id}]] braucht 2+ Auswahloptionen.`;
      const norm = (s: string) => s.trim().toLocaleLowerCase("de");
      if (g.options && !g.accepted.some((a) => g.options!.some((o) => norm(o) === norm(a)))) {
        return `Lückentext: die Antwort von [[${id}]] steht nicht in den Optionen.`;
      }
    }
    return null;
  }
  if (!c.accepted?.length) return "Kurzantwort: mindestens eine akzeptierte Antwort.";
  return null;
}

interface Props {
  question: AdminQuestion;
  onChange: (config: AdminQuestionConfig) => void;
}

export default function ConfigQuestionEditor({ question, onChange }: Props) {
  const c = question.config ?? blankConfig(question.question_type) ?? {};
  const set = (change: Partial<AdminQuestionConfig>) => onChange({ ...c, ...change });

  if (question.question_type === "MATCHING") {
    const items = c.items ?? [];
    const targets = c.targets ?? [];
    const pairs = c.pairs ?? {};
    const relabel = (list: { id: string; text: string }[]) => list.map((x, i) => ({ ...x, id: LETTERS[i] }));
    return (
      <div className="grid gap-4 md:grid-cols-2" data-testid="matching-editor">
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-[var(--admin-text-muted)]">Aussagen → richtige Antwort</p>
          {items.map((item, i) => (
            <div key={i} className="flex items-center gap-2">
              <span className="w-5 text-xs font-bold text-[var(--admin-text-muted)]">{item.id}.</span>
              <AdminInput
                value={item.text}
                placeholder={`Aussage ${item.id}`}
                onChange={(e) => set({ items: items.map((x, j) => (j === i ? { ...x, text: e.target.value } : x)) })}
              />
              <div className="w-20 shrink-0">
                <AdminSelect
                  value={pairs[item.id] ?? ""}
                  onChange={(e) => set({ pairs: { ...pairs, [item.id]: e.target.value } })}
                  aria-label={`Richtige Antwort für ${item.id}`}
                >
                  <option value="">—</option>
                  {targets.map((x) => (
                    <option key={x.id} value={x.id}>
                      {x.id}
                    </option>
                  ))}
                </AdminSelect>
              </div>
              {items.length > 2 && (
                <AdminButton
                  variant="ghost"
                  size="sm"
                  aria-label="Aussage entfernen"
                  onClick={() => {
                    const next = items.filter((_, j) => j !== i).map((x, j) => ({ ...x, id: String(j + 1) }));
                    const nextPairs: Record<string, string> = {};
                    items.filter((_, j) => j !== i).forEach((x, j) => {
                      if (pairs[x.id]) nextPairs[String(j + 1)] = pairs[x.id];
                    });
                    set({ items: next, pairs: nextPairs });
                  }}
                >
                  <Trash2 size={13} />
                </AdminButton>
              )}
            </div>
          ))}
          {items.length < 12 && (
            <button
              type="button"
              className="text-xs font-semibold text-[var(--admin-primary)] hover:underline"
              onClick={() => set({ items: [...items, { id: String(items.length + 1), text: "" }] })}
            >
              + Aussage
            </button>
          )}
        </div>
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-[var(--admin-text-muted)]">Antworten (auch Distraktoren)</p>
          {targets.map((x, i) => (
            <div key={i} className="flex items-center gap-2">
              <span className="w-5 text-xs font-bold text-[var(--admin-text-muted)]">{x.id})</span>
              <AdminInput
                value={x.text}
                placeholder={`Antwort ${x.id}`}
                onChange={(e) => set({ targets: targets.map((y, j) => (j === i ? { ...y, text: e.target.value } : y)) })}
              />
              {targets.length > items.length && (
                <AdminButton
                  variant="ghost"
                  size="sm"
                  aria-label="Antwort entfernen"
                  onClick={() => {
                    const removed = x.id;
                    const next = relabel(targets.filter((_, j) => j !== i));
                    const map = new Map(targets.filter((_, j) => j !== i).map((y, j) => [y.id, LETTERS[j]]));
                    const nextPairs = Object.fromEntries(
                      Object.entries(pairs).map(([k, v]) => [k, v === removed ? "" : (map.get(v) ?? "")]),
                    );
                    set({ targets: next, pairs: nextPairs });
                  }}
                >
                  <Trash2 size={13} />
                </AdminButton>
              )}
            </div>
          ))}
          {targets.length < 15 && (
            <button
              type="button"
              className="text-xs font-semibold text-[var(--admin-primary)] hover:underline"
              onClick={() => set({ targets: [...targets, { id: LETTERS[targets.length], text: "" }] })}
            >
              + Antwort
            </button>
          )}
        </div>
      </div>
    );
  }

  if (question.question_type === "GAP_FILL") {
    const text = c.text ?? "";
    const ids = gapIds(text);
    const gaps = c.gaps ?? {};
    const nextId = () => {
      let n = 1;
      while (ids.includes(String(n))) n += 1;
      return String(n);
    };
    return (
      <div className="space-y-3" data-testid="gap-editor">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-xs text-[var(--admin-text-muted)]">Lücken im Text als [[1]], [[2]] … markieren.</p>
          <AdminButton
            variant="secondary"
            size="sm"
            onClick={() => {
              const id = nextId();
              set({ text: `${text}${text.endsWith(" ") || !text ? "" : " "}[[${id}]]`, gaps: { ...gaps, [id]: { accepted: [""] } } });
            }}
          >
            <Plus size={13} /> Lücke einfügen
          </AdminButton>
        </div>
        <AdminTextarea rows={3} value={text} onChange={(e) => set({ text: e.target.value })} placeholder="Ich [[1]] Anna und komme aus [[2]]." />
        {ids.map((id) => {
          const g = gaps[id] ?? { accepted: [] };
          return (
            <div key={id} className="grid gap-2 sm:grid-cols-[3rem_1fr_1fr] sm:items-center">
              <span className="text-xs font-bold text-[var(--admin-text-muted)]">[[{id}]]</span>
              <AdminInput
                value={g.accepted.join("|")}
                onChange={(e) => set({ gaps: { ...gaps, [id]: { ...g, accepted: e.target.value.split("|") } } })}
                placeholder="Richtige Antwort(en), getrennt mit |"
                aria-label={`Antworten Lücke ${id}`}
              />
              <AdminInput
                value={(g.options ?? []).join("|")}
                onChange={(e) => {
                  const options = e.target.value ? e.target.value.split("|") : undefined;
                  set({ gaps: { ...gaps, [id]: options ? { ...g, options } : { accepted: g.accepted } } });
                }}
                placeholder="Optional: Auswahl a|b|c (sonst freie Eingabe)"
                aria-label={`Auswahl Lücke ${id}`}
              />
            </div>
          );
        })}
        <label className="flex items-center gap-2 text-xs text-[var(--admin-text-secondary)]">
          <AdminCheckbox checked={!!c.case_sensitive} onCheckedChange={(v) => set({ case_sensitive: v })} aria-label="Groß-/Kleinschreibung beachten" />
          Groß-/Kleinschreibung beachten
        </label>
      </div>
    );
  }

  return (
    <div className="space-y-2" data-testid="short-editor">
      <AdminTextarea
        rows={3}
        value={(c.accepted ?? []).join("\n")}
        onChange={(e) => set({ accepted: e.target.value.split("\n") })}
        placeholder={"Alle akzeptierten Antworten, eine pro Zeile\nz. B. 3\ndrei\nGleis 3"}
        aria-label="Akzeptierte Antworten"
      />
      <p className="text-xs text-[var(--admin-text-muted)]">
        Nur für Antworten, die sich eindeutig prüfen lassen. Leerzeichen, Satzzeichen am Ende und (optional) Groß-/Kleinschreibung werden ignoriert.
      </p>
      <div className="flex flex-wrap items-center gap-4">
        <label className="flex items-center gap-2 text-xs text-[var(--admin-text-secondary)]">
          <AdminCheckbox checked={!!c.case_sensitive} onCheckedChange={(v) => set({ case_sensitive: v })} aria-label="Groß-/Kleinschreibung beachten" />
          Groß-/Kleinschreibung beachten
        </label>
        <label className="flex items-center gap-1.5 text-xs text-[var(--admin-text-secondary)]">
          Max. Zeichen
          <AdminInput
            type="number"
            min={1}
            max={300}
            className="h-9 w-20"
            value={c.max_length ?? 100}
            onChange={(e) => set({ max_length: Number(e.target.value) })}
          />
        </label>
      </div>
    </div>
  );
}
