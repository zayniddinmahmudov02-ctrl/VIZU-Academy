"use client";

import { useRef, useState } from "react";
import { Image as ImageIcon, Upload, X } from "lucide-react";

import { AdminButton, AdminInput } from "@/components/admin/admin-ui";
import { resolveMediaUrl } from "@/lib/media";
import { uploadImage } from "@/features/admin/services/assessment-service";
import type { AssessmentTask, SpeakingConfig } from "@/features/admin/types/assessment.types";

import RubricCriteriaEditor from "./rubric-criteria-editor";

interface Props {
  task: AssessmentTask;
  onConfigChange: (config: Partial<SpeakingConfig> & { image_url?: string | null }) => void;
  onChanged: () => void;
}

/** The Sprechen task builder panel: image attachment, Vorbereitungszeit /
 * Sprechzeit, and the same universal rubric builder Schreiben uses
 * (RubricCriteriaEditor doesn't care which skill's task it's attached
 * to). Speaking tasks are always created with evaluation_mode=TEACHER_ONLY
 * server-side — there's no AI audio evaluation in this phase, so no mode
 * selector is shown here (unlike WritingPanel). */
export default function SpeakingPanel({ task, onConfigChange, onChanged }: Props) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <div className="space-y-4 rounded-xl bg-white/[0.02] p-4 ring-1 ring-[var(--admin-border)]">
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

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1 block text-[10px] font-medium uppercase text-[var(--admin-text-muted)]">
            Vorbereitungszeit (Sek.)
          </label>
          <AdminInput
            type="number"
            defaultValue={task.prep_seconds ?? ""}
            onBlur={(e) => onConfigChange({ prep_seconds: e.target.value ? Number(e.target.value) : null })}
            className="h-8 text-xs"
          />
        </div>
        <div>
          <label className="mb-1 block text-[10px] font-medium uppercase text-[var(--admin-text-muted)]">
            Sprechzeit (Sek.)
          </label>
          <AdminInput
            type="number"
            defaultValue={task.speak_seconds ?? ""}
            onBlur={(e) => onConfigChange({ speak_seconds: e.target.value ? Number(e.target.value) : null })}
            className="h-8 text-xs"
          />
        </div>
      </div>

      <RubricCriteriaEditor taskId={task.id} criteria={task.rubric_criteria ?? []} onChanged={onChanged} />
    </div>
  );
}
