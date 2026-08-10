"use client";

import { Trash2 } from "lucide-react";

import { AdminCheckbox, AdminInput } from "@/components/admin/admin-ui";
import type { TaskQuestion } from "../../types/assessment.types";

interface Props {
  gaps: TaskQuestion[];
  onUpdate: (id: string, data: Partial<TaskQuestion>) => void;
  onRemove: (id: string) => void;
}

/** Below the CLOZE_TEXT rich-text editor: one row per Lücke (TaskQuestion),
 * ordered by sort_order — the same order the gap markers appear in the
 * content. Alternative answers are stored as a JSON array string
 * (alternative_answers) but edited here as a plain comma-separated list. */
export default function GapList({ gaps, onUpdate, onRemove }: Props) {
  const sorted = [...gaps].sort((a, b) => a.sort_order - b.sort_order);

  if (sorted.length === 0) {
    return (
      <p className="text-xs text-[var(--admin-text-muted)]">
        Noch keine Lücken. Klicke im Editor auf &quot;Lücke einfügen&quot;.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {sorted.map((gap, index) => (
        <div key={gap.id} className="rounded-lg bg-white/[0.02] p-3 ring-1 ring-[var(--admin-border)]">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs font-semibold text-[var(--admin-primary)]">Lücke {index + 1}</span>
            <button
              onClick={() => onRemove(gap.id)}
              aria-label="Lücke löschen"
              className="flex h-6 w-6 items-center justify-center rounded-md text-[var(--admin-text-muted)] hover:bg-[var(--admin-danger)]/10 hover:text-[var(--admin-danger)]"
            >
              <Trash2 size={12} />
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <div className="sm:col-span-2">
              <label className="mb-1 block text-[10px] font-medium uppercase text-[var(--admin-text-muted)]">
                Correct
              </label>
              <AdminInput
                defaultValue={gap.correct_text_answer ?? ""}
                onBlur={(e) => {
                  if (e.target.value !== (gap.correct_text_answer ?? "")) {
                    onUpdate(gap.id, { correct_text_answer: e.target.value });
                  }
                }}
                placeholder="Deutschland"
                className="h-8 text-sm"
              />
            </div>
            <div className="sm:col-span-2">
              <label className="mb-1 block text-[10px] font-medium uppercase text-[var(--admin-text-muted)]">
                Alternative (Komma-getrennt)
              </label>
              <AdminInput
                defaultValue={parseAlternatives(gap.alternative_answers).join(", ")}
                onBlur={(e) => {
                  const next = serializeAlternatives(e.target.value);
                  if (next !== (gap.alternative_answers ?? "")) {
                    onUpdate(gap.id, { alternative_answers: next });
                  }
                }}
                placeholder="Germany"
                className="h-8 text-sm"
              />
            </div>
            <div>
              <label className="mb-1 block text-[10px] font-medium uppercase text-[var(--admin-text-muted)]">
                Punkte
              </label>
              <AdminInput
                type="number"
                defaultValue={gap.points}
                onBlur={(e) => {
                  const value = Number(e.target.value);
                  if (value !== gap.points) onUpdate(gap.id, { points: value });
                }}
                className="h-8 text-sm"
              />
            </div>
            <label className="flex cursor-pointer items-center gap-2 pt-4">
              <AdminCheckbox
                checked={gap.case_sensitive}
                onCheckedChange={(checked) => onUpdate(gap.id, { case_sensitive: checked })}
              />
              <span className="text-xs text-[var(--admin-text-secondary)]">Case sensitive</span>
            </label>
          </div>
        </div>
      ))}
    </div>
  );
}

function parseAlternatives(raw: string | null): string[] {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function serializeAlternatives(commaSeparated: string): string {
  const list = commaSeparated
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  return JSON.stringify(list);
}
