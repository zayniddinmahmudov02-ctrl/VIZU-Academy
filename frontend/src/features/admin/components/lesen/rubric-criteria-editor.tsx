"use client";

import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";

import { AdminButton, AdminInput } from "@/components/admin/admin-ui";
import {
  createRubricCriterion,
  deleteRubricCriterion,
  updateRubricCriterion,
} from "@/features/admin/services/assessment-service";
import type { WritingRubricCriterion } from "@/features/admin/types/assessment.types";

interface Props {
  taskId: string;
  criteria: WritingRubricCriterion[];
  onChanged: () => void;
}

/** The universal rubric builder — used by both WritingPanel (Schreiben)
 * and SpeakingPanel (Sprechen), since a rubric criterion is just
 * (task_id, name, max_score) regardless of which skill's task it belongs
 * to. Never hardcodes criteria; whatever's added here is exactly what the
 * AI/teacher scores against. */
export default function RubricCriteriaEditor({ taskId, criteria, onChanged }: Props) {
  const [newName, setNewName] = useState("");
  const [newMax, setNewMax] = useState(5);

  async function handleAdd() {
    if (!newName.trim()) return;
    await createRubricCriterion(taskId, {
      name: newName.trim(),
      max_score: newMax,
      sort_order: criteria.length + 1,
    });
    setNewName("");
    setNewMax(5);
    onChanged();
  }

  const total = criteria.reduce((sum, c) => sum + c.max_score, 0);

  return (
    <div className="border-t border-[var(--admin-border)] pt-3">
      <div className="mb-2 flex items-center justify-between">
        <label className="text-xs font-medium text-[var(--admin-text-secondary)]">Bewertungsraster</label>
        <span className="text-[10px] text-[var(--admin-text-muted)]">Gesamt: {total} Pkt.</span>
      </div>

      <div className="space-y-1.5">
        {criteria.map((criterion) => (
          <div key={criterion.id} className="flex items-center gap-2">
            <AdminInput
              defaultValue={criterion.name}
              onBlur={(e) => {
                if (e.target.value !== criterion.name) {
                  updateRubricCriterion(criterion.id, { name: e.target.value }).then(onChanged);
                }
              }}
              className="h-8 flex-1 text-xs"
            />
            <AdminInput
              type="number"
              defaultValue={criterion.max_score}
              onBlur={(e) => {
                const value = Number(e.target.value);
                if (value !== criterion.max_score) {
                  updateRubricCriterion(criterion.id, { max_score: value }).then(onChanged);
                }
              }}
              className="h-8 w-20 text-xs"
            />
            <button
              onClick={() => deleteRubricCriterion(criterion.id).then(onChanged)}
              aria-label="Kriterium löschen"
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-[var(--admin-text-muted)] hover:bg-[var(--admin-danger)]/10 hover:text-[var(--admin-danger)]"
            >
              <Trash2 size={13} />
            </button>
          </div>
        ))}
      </div>

      <div className="mt-2 flex items-center gap-2">
        <AdminInput
          placeholder="z. B. Inhalt"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          className="h-8 flex-1 text-xs"
        />
        <AdminInput
          type="number"
          value={newMax}
          onChange={(e) => setNewMax(Number(e.target.value))}
          className="h-8 w-20 text-xs"
        />
        <AdminButton size="sm" variant="secondary" onClick={handleAdd}>
          <Plus size={13} />
        </AdminButton>
      </div>
    </div>
  );
}
