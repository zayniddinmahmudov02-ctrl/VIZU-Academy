"use client";

import { Plus, RotateCcw, Trash2 } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminInput, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import type { RubricCriterion } from "@/features/admin/services/lesson-skills-admin-service";

// Mirrors backend services/lesson_skills/ai_evaluation.py (the server applies
// these when a task has no own rubric).
export const DEFAULT_WRITING_RUBRIC: RubricCriterion[] = [
  { key: "task", name: "Topshiriqni bajarish", max: 25 },
  { key: "grammar", name: "Grammatika", max: 25 },
  { key: "vocabulary", name: "Lug'at va mavzuga moslik", max: 20 },
  { key: "coherence", name: "Gaplar tuzilishi va mantiqiy bog'lanish", max: 15 },
  { key: "spelling", name: "Imlo va tinish belgilari", max: 15 },
];

export const DEFAULT_SPEAKING_RUBRIC: RubricCriterion[] = [
  { key: "content", name: "Savolga javob va mazmun", max: 25 },
  { key: "grammar", name: "Grammatika", max: 20 },
  { key: "vocabulary", name: "Lug'at", max: 20 },
  { key: "pronunciation", name: "Talaffuz", max: 20 },
  { key: "fluency", name: "Ravonlik va tushunarlilik", max: 15 },
];

export interface AiFormState {
  ai_evaluation_enabled: boolean;
  ai_instructions: string;
  feedback_language: string;
  max_attempts: number;
  /** null = the default A1 rubric */
  rubric: RubricCriterion[] | null;
}

export const EMPTY_AI_FORM: AiFormState = {
  ai_evaluation_enabled: true,
  ai_instructions: "",
  feedback_language: "uz",
  max_attempts: 3,
  rubric: null,
};

export function aiFormFrom(item: {
  ai_evaluation_enabled?: boolean;
  ai_instructions?: string | null;
  feedback_language?: string;
  max_attempts?: number;
  rubric?: RubricCriterion[] | null;
}): AiFormState {
  return {
    ai_evaluation_enabled: item.ai_evaluation_enabled ?? false,
    ai_instructions: item.ai_instructions ?? "",
    feedback_language: item.feedback_language ?? "uz",
    max_attempts: item.max_attempts ?? 3,
    rubric: item.rubric?.length ? item.rubric : null,
  };
}

export function aiPayload(state: AiFormState) {
  return {
    ai_evaluation_enabled: state.ai_evaluation_enabled,
    ai_instructions: state.ai_instructions.trim() || null,
    feedback_language: state.feedback_language,
    max_attempts: state.max_attempts,
    rubric: state.rubric,
  };
}

/** Same rules as backend validate_rubric. */
export function rubricProblem(rubric: RubricCriterion[] | null): string | null {
  if (!rubric) return null;
  if (rubric.length < 1 || rubric.length > 10) return "Bewertungsraster: 1–10 Kriterien.";
  const keys = new Set<string>();
  for (const c of rubric) {
    const key = c.key.trim().toLowerCase();
    if (!/^[a-z0-9_]{1,40}$/.test(key) || keys.has(key)) return `Kriterium-Schlüssel "${c.key}" ungültig oder doppelt (a–z, 0–9, _).`;
    if (!c.name.trim()) return "Jedes Kriterium braucht einen Namen.";
    if (!Number.isInteger(c.max) || c.max < 1 || c.max > 100) return `"${c.name}": max. 1–100 Punkte.`;
    keys.add(key);
  }
  return null;
}

const LANGUAGES = [
  { value: "uz", label: "Usbekisch (Beispiele auf Deutsch)" },
  { value: "de", label: "Deutsch" },
  { value: "ru", label: "Russisch" },
  { value: "en", label: "Englisch" },
];

const label = "mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]";

export default function AiTaskFields({ value, onChange, defaultRubric, level }: {
  value: AiFormState;
  onChange: (next: AiFormState) => void;
  defaultRubric: RubricCriterion[];
  /** CEFR level of the lesson whose default rubric is shown */
  level?: string | null;
}) {
  const rubric = value.rubric ?? defaultRubric;
  const total = rubric.reduce((sum, c) => sum + (Number(c.max) || 0), 0);

  function setRubric(next: RubricCriterion[]) {
    onChange({ ...value, rubric: next });
  }

  function patchCriterion(index: number, change: Partial<RubricCriterion>) {
    setRubric(rubric.map((c, i) => (i === index ? { ...c, ...change } : c)));
  }

  return (
    <div className="space-y-4 rounded-xl bg-white/[0.03] p-4 ring-1 ring-[var(--admin-border)]" data-testid="ai-settings">
      <label className="flex cursor-pointer items-center gap-2.5">
        <AdminCheckbox checked={value.ai_evaluation_enabled} onCheckedChange={(checked) => onChange({ ...value, ai_evaluation_enabled: checked })} />
        <span className="text-sm font-semibold text-[var(--admin-text-primary)]">KI-Bewertung aktiv</span>
      </label>
      <p className="-mt-2 text-xs text-[var(--admin-text-muted)]">
        {value.ai_evaluation_enabled
          ? "Abgaben werden automatisch nach dem Raster bewertet (Gemini). Lehrkräfte/Admins können jede Bewertung korrigieren."
          : "Ohne KI: die Lehrkraft bewertet im Teacher Panel."}
      </p>

      {value.ai_evaluation_enabled && (
        <>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className={label}>Feedback-Sprache</label>
              <AdminSelect value={value.feedback_language} onChange={(e) => onChange({ ...value, feedback_language: e.target.value })}>
                {LANGUAGES.map((l) => (
                  <option key={l.value} value={l.value}>{l.label}</option>
                ))}
              </AdminSelect>
            </div>
            <div>
              <label className={label}>Max. Versuche</label>
              <AdminInput type="number" min={1} max={20} value={value.max_attempts} onChange={(e) => onChange({ ...value, max_attempts: Number(e.target.value) })} />
            </div>
          </div>

          <div>
            <label className={label}>Zusätzliche Anweisungen für die KI (nur serverseitig, Schüler sehen sie nicht)</label>
            <AdminTextarea
              rows={3}
              value={value.ai_instructions}
              onChange={(e) => onChange({ ...value, ai_instructions: e.target.value })}
              placeholder="z. B. Der Schüler soll sich mit Name, Herkunft und Wohnort vorstellen."
            />
          </div>

          <div>
            <div className="mb-1.5 flex flex-wrap items-center justify-between gap-2">
              <span className="text-sm font-medium text-[var(--admin-text-primary)]">
                Bewertungsraster {value.rubric ? "(eigenes)" : `(Standard ${level ?? "A1"})`} · {total} Punkte → Ergebnis /100
              </span>
              {value.rubric && (
                <button type="button" onClick={() => onChange({ ...value, rubric: null })} className="inline-flex items-center gap-1 text-xs font-semibold text-[var(--admin-primary)] hover:underline">
                  <RotateCcw size={12} /> Standard verwenden
                </button>
              )}
            </div>
            <div className="space-y-2">
              {rubric.map((c, i) => (
                <div key={i} className="flex items-center gap-2" data-testid="rubric-row">
                  <AdminInput className="w-32" value={c.key} onChange={(e) => patchCriterion(i, { key: e.target.value })} aria-label="Schlüssel" />
                  <AdminInput value={c.name} onChange={(e) => patchCriterion(i, { name: e.target.value })} aria-label="Name" />
                  <AdminInput className="w-20" type="number" min={1} max={100} value={c.max} onChange={(e) => patchCriterion(i, { max: Number(e.target.value) })} aria-label="Max. Punkte" />
                  <AdminButton size="sm" variant="ghost" disabled={rubric.length <= 1} onClick={() => setRubric(rubric.filter((_, j) => j !== i))} aria-label="Kriterium entfernen">
                    <Trash2 size={13} />
                  </AdminButton>
                </div>
              ))}
            </div>
            {rubric.length < 10 && (
              <button
                type="button"
                onClick={() => setRubric([...rubric, { key: `criterion_${rubric.length + 1}`, name: "", max: 10 }])}
                className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-[var(--admin-primary)] hover:underline"
              >
                <Plus size={12} /> Kriterium
              </button>
            )}
          </div>
        </>
      )}
    </div>
  );
}
