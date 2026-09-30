"use client";

import { Plus, Trash2 } from "lucide-react";

import { AdminButton, AdminInput } from "@/components/admin/admin-ui";
import type { VizuMockWritingRubricCriterion } from "@/features/admin/types/vizu-mock-admin.types";

interface Props {
  criteria: VizuMockWritingRubricCriterion[];
  onChange: (criteria: VizuMockWritingRubricCriterion[]) => void;
}

/** Add/remove/edit rows for a Schreiben Aufgabe's scoring rubric — no
 * existing rubric-criteria UI exists anywhere in the codebase to reuse
 * (the Assessment Engine's own rubric CRUD was built but never wired to
 * a route or UI), so this is new. */
export default function RubricCriteriaEditor({ criteria, onChange }: Props) {
  const total = criteria.reduce((sum, c) => sum + (Number(c.max_score) || 0), 0);

  function update(index: number, patch: Partial<VizuMockWritingRubricCriterion>) {
    const next = criteria.map((c, i) => (i === index ? { ...c, ...patch } : c));
    onChange(next);
  }

  function remove(index: number) {
    onChange(criteria.filter((_, i) => i !== index));
  }

  function add() {
    onChange([
      ...criteria,
      { id: null, name: "", max_score: 4, order_index: criteria.length + 1 },
    ]);
  }

  return (
    <div className="space-y-2">
      {criteria.map((c, i) => (
        <div key={c.id ?? `new-${i}`} className="flex items-center gap-2">
          <AdminInput
            value={c.name}
            onChange={(e) => update(i, { name: e.target.value })}
            placeholder="Kriterium (z. B. Grammatik)"
            className="flex-1"
          />
          <AdminInput
            type="number"
            min={0}
            value={c.max_score}
            onChange={(e) => update(i, { max_score: Number(e.target.value) })}
            className="w-20"
          />
          <button
            type="button"
            onClick={() => remove(i)}
            aria-label="Kriterium entfernen"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-[var(--admin-text-secondary)] transition hover:bg-[var(--admin-danger)]/10 hover:text-[var(--admin-danger)]"
          >
            <Trash2 size={14} />
          </button>
        </div>
      ))}

      <div className="flex items-center justify-between pt-1">
        <AdminButton type="button" variant="ghost" size="sm" onClick={add}>
          <Plus size={13} />
          Kriterium hinzufügen
        </AdminButton>
        <span
          className={
            total === 20
              ? "text-xs font-semibold text-[var(--admin-success,#22c55e)]"
              : "text-xs font-semibold text-[var(--admin-warning,#f59e0b)]"
          }
        >
          Gesamt: {total}/20
        </span>
      </div>
    </div>
  );
}
