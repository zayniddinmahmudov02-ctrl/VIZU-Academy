"use client";

import { useRef, useState } from "react";
import { Image as ImageIcon, Plus, Trash2, Upload, X } from "lucide-react";

import { AdminButton, AdminInput, AdminSelect } from "@/components/admin/admin-ui";
import { resolveMediaUrl } from "@/lib/media";
import {
  createRubricCriterion,
  deleteRubricCriterion,
  updateRubricCriterion,
  uploadImage,
} from "@/features/admin/services/assessment-service";
import {
  EVALUATION_MODE_LABELS,
  EVALUATION_MODES,
  type AssessmentTask,
  type WritingConfig,
} from "@/features/admin/types/assessment.types";

interface Props {
  task: AssessmentTask;
  onConfigChange: (config: Partial<WritingConfig>) => void;
  onChanged: () => void;
}

/** The Schreiben task builder panel: image attachment, word/time limits,
 * evaluation mode, and the admin-defined scoring rubric — everything a
 * WRITING task needs beyond its rich-text prompt (rendered by the caller
 * via the same LesenRichTextEditor every other task type already uses for
 * `content`, so "Sie haben einen Freund..." is just a normal rich-text
 * field, not a special case). Never hardcodes a rubric — whatever
 * criteria the admin adds here is exactly what the AI/teacher scores
 * against. */
export default function WritingPanel({ task, onConfigChange, onChanged }: Props) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newCriterionName, setNewCriterionName] = useState("");
  const [newCriterionMax, setNewCriterionMax] = useState(5);

  async function handleImageSelected(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const url = await uploadImage(file);
      onConfigChange({ image_url: url });
    } catch {
      setError("Bild konnte nicht hochgeladen werden.");
    } finally {
      setUploading(false);
    }
  }

  async function handleAddCriterion() {
    if (!newCriterionName.trim()) return;
    await createRubricCriterion(task.id, {
      name: newCriterionName.trim(),
      max_score: newCriterionMax,
      sort_order: (task.rubric_criteria?.length ?? 0) + 1,
    });
    setNewCriterionName("");
    setNewCriterionMax(5);
    onChanged();
  }

  const totalRubricScore = (task.rubric_criteria ?? []).reduce((sum, c) => sum + c.max_score, 0);

  return (
    <div className="space-y-4 rounded-xl bg-white/[0.02] p-4 ring-1 ring-[var(--admin-border)]">
      {/* Image (Text / Image / Text+Image content) */}
      <div>
        <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">
          Bild (optional)
        </label>
        <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleImageSelected} />
        {task.image_url ? (
          <div className="flex items-center gap-3">
            <img
              src={resolveMediaUrl(task.image_url) ?? undefined}
              alt=""
              className="h-20 w-20 rounded-lg object-cover ring-1 ring-[var(--admin-border)]"
            />
            <AdminButton size="sm" variant="ghost" onClick={() => onConfigChange({ image_url: null })}>
              <X size={13} />
              Entfernen
            </AdminButton>
          </div>
        ) : (
          <AdminButton size="sm" variant="secondary" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
            {uploading ? <Upload size={13} /> : <ImageIcon size={13} />}
            {uploading ? "Wird hochgeladen..." : "Bild hochladen"}
          </AdminButton>
        )}
        {error && <p className="mt-1 text-xs text-[var(--admin-danger)]">{error}</p>}
      </div>

      {/* Word / time limits + evaluation mode */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div>
          <label className="mb-1 block text-[10px] font-medium uppercase text-[var(--admin-text-muted)]">
            Min. Wörter
          </label>
          <AdminInput
            type="number"
            defaultValue={task.min_words ?? ""}
            onBlur={(e) => onConfigChange({ min_words: e.target.value ? Number(e.target.value) : null })}
            className="h-8 text-xs"
          />
        </div>
        <div>
          <label className="mb-1 block text-[10px] font-medium uppercase text-[var(--admin-text-muted)]">
            Max. Wörter
          </label>
          <AdminInput
            type="number"
            defaultValue={task.max_words ?? ""}
            onBlur={(e) => onConfigChange({ max_words: e.target.value ? Number(e.target.value) : null })}
            className="h-8 text-xs"
          />
        </div>
        <div>
          <label className="mb-1 block text-[10px] font-medium uppercase text-[var(--admin-text-muted)]">
            Zeitlimit (Min.)
          </label>
          <AdminInput
            type="number"
            defaultValue={task.time_limit_minutes ?? ""}
            onBlur={(e) => onConfigChange({ time_limit_minutes: e.target.value ? Number(e.target.value) : null })}
            className="h-8 text-xs"
          />
        </div>
        <div>
          <label className="mb-1 block text-[10px] font-medium uppercase text-[var(--admin-text-muted)]">
            Bewertung
          </label>
          <AdminSelect
            value={task.evaluation_mode}
            onChange={(e) => onConfigChange({ evaluation_mode: e.target.value as WritingConfig["evaluation_mode"] })}
            className="h-8 text-xs"
          >
            {EVALUATION_MODES.map((mode) => (
              <option key={mode} value={mode}>
                {EVALUATION_MODE_LABELS[mode]}
              </option>
            ))}
          </AdminSelect>
        </div>
      </div>

      {/* Rubric */}
      <div className="border-t border-[var(--admin-border)] pt-3">
        <div className="mb-2 flex items-center justify-between">
          <label className="text-xs font-medium text-[var(--admin-text-secondary)]">Bewertungsraster</label>
          <span className="text-[10px] text-[var(--admin-text-muted)]">Gesamt: {totalRubricScore} Pkt.</span>
        </div>

        <div className="space-y-1.5">
          {(task.rubric_criteria ?? []).map((criterion) => (
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
            value={newCriterionName}
            onChange={(e) => setNewCriterionName(e.target.value)}
            className="h-8 flex-1 text-xs"
          />
          <AdminInput
            type="number"
            value={newCriterionMax}
            onChange={(e) => setNewCriterionMax(Number(e.target.value))}
            className="h-8 w-20 text-xs"
          />
          <AdminButton size="sm" variant="secondary" onClick={handleAddCriterion}>
            <Plus size={13} />
          </AdminButton>
        </div>
      </div>
    </div>
  );
}
