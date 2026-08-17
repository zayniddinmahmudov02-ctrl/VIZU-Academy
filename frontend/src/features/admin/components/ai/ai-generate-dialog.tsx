"use client";

import { useState } from "react";
import { Sparkles } from "lucide-react";

import FormDialog from "@/components/admin/form-dialog";
import { AdminButton, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";

const LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"];

interface Props<TPreview> {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  hasCount?: boolean;
  generate: (input: { source_text: string; level: string; count: number }) => Promise<TPreview>;
  onApply: (preview: TPreview) => Promise<void>;
  renderPreview: (preview: TPreview) => React.ReactNode;
}

/** Shared "paste text -> Mit KI erstellen -> preview -> Übernehmen" shell
 * for every AI content-generation flow (Grammatik Quiz / Lesen / Hören /
 * Schreiben / Sprechen — see Feature 3). Only the generate call, the
 * preview rendering, and the apply step differ per skill; the source-
 * text input, level/count controls, and loading/error handling live
 * here once. Nothing here ever calls a create/publish endpoint itself —
 * that only happens inside the caller-supplied onApply, driven by the
 * admin's explicit "Übernehmen" click. */
export default function AiGenerateDialog<TPreview>({
  open,
  onOpenChange,
  title,
  hasCount = false,
  generate,
  onApply,
  renderPreview,
}: Props<TPreview>) {
  const [sourceText, setSourceText] = useState("");
  const [level, setLevel] = useState("A1");
  const [count, setCount] = useState(5);
  const [preview, setPreview] = useState<TPreview | null>(null);
  const [generating, setGenerating] = useState(false);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function reset() {
    setSourceText("");
    setPreview(null);
    setError(null);
  }

  async function handleGenerate() {
    if (!sourceText.trim()) return;
    setGenerating(true);
    setError(null);
    try {
      const result = await generate({ source_text: sourceText.trim(), level, count });
      setPreview(result);
    } catch {
      setError("Generierung fehlgeschlagen. Bitte erneut versuchen.");
    } finally {
      setGenerating(false);
    }
  }

  async function handleApply() {
    if (!preview) return;
    setApplying(true);
    try {
      await onApply(preview);
      onOpenChange(false);
      reset();
    } catch {
      setError("Übernehmen fehlgeschlagen. Bitte erneut versuchen.");
    } finally {
      setApplying(false);
    }
  }

  return (
    <FormDialog
      open={open}
      onOpenChange={(next) => {
        onOpenChange(next);
        if (!next) reset();
      }}
      title={title}
      description="Der KI-Entwurf wird nie automatisch veröffentlicht — erst nach Prüfung und Übernehmen."
      size="lg"
    >
      <div className="space-y-4">
        <div>
          <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">
            Text / Anweisungen
          </label>
          <AdminTextarea
            value={sourceText}
            onChange={(e) => setSourceText(e.target.value)}
            rows={5}
            placeholder="Thema, Ausgangstext oder Stichpunkte für die KI..."
          />
        </div>

        <div className="flex items-center gap-3">
          <div className="w-28">
            <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">Niveau</label>
            <AdminSelect value={level} onChange={(e) => setLevel(e.target.value)} className="h-9 text-sm">
              {LEVELS.map((l) => (
                <option key={l} value={l}>
                  {l}
                </option>
              ))}
            </AdminSelect>
          </div>
          {hasCount && (
            <div className="w-28">
              <label className="mb-1 block text-xs font-medium text-[var(--admin-text-secondary)]">Anzahl</label>
              <input
                type="number"
                min={1}
                max={20}
                value={count}
                onChange={(e) => setCount(Number(e.target.value))}
                className="h-9 w-full rounded-lg bg-[var(--admin-card)] px-3 text-sm text-[var(--admin-text-primary)] ring-1 ring-[var(--admin-border-strong)] outline-none focus:ring-2 focus:ring-[var(--admin-primary)]"
              />
            </div>
          )}
          <div className="flex-1" />
          <AdminButton size="sm" onClick={handleGenerate} disabled={!sourceText.trim() || generating}>
            <Sparkles size={14} />
            {generating ? "Wird erstellt..." : "Mit KI erstellen"}
          </AdminButton>
        </div>

        {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}

        {preview && (
          <div className="space-y-3 rounded-xl bg-white/[0.02] p-4 ring-1 ring-[var(--admin-border)]">
            {renderPreview(preview)}
          </div>
        )}
      </div>

      {preview && (
        <div className="mt-6 flex items-center justify-end gap-3">
          <AdminButton variant="secondary" size="sm" onClick={() => setPreview(null)} disabled={applying}>
            Verwerfen
          </AdminButton>
          <AdminButton size="sm" onClick={handleApply} disabled={applying}>
            {applying ? "Wird übernommen..." : "Übernehmen"}
          </AdminButton>
        </div>
      )}
    </FormDialog>
  );
}
