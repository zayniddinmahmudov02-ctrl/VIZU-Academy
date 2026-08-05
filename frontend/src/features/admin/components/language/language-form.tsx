"use client";

import { useRef, useState } from "react";
import { Loader2, Upload } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminInput, AdminLabel, AdminTextarea } from "@/components/admin/admin-ui";
import { uploadFlagSvg } from "@/features/admin/services/language-management-service";
import type { LanguageCreate } from "@/features/admin/types/language.types";

export interface LanguageFormValues {
  code: string;
  locale: string;
  name: string;
  native_name: string;
  english_name: string;
  flag_file: string;
  primary_color: string;
  description: string;
  is_default: boolean;
  is_active: boolean;
  sort_order: number;
}

export const EMPTY_LANGUAGE_FORM: LanguageFormValues = {
  code: "",
  locale: "",
  name: "",
  native_name: "",
  english_name: "",
  flag_file: "",
  primary_color: "#5b5bf8",
  description: "",
  is_default: false,
  is_active: true,
  sort_order: 1,
};

export function toLanguageCreatePayload(form: LanguageFormValues): LanguageCreate {
  return {
    code: form.code.trim().toLowerCase(),
    locale: form.locale.trim(),
    name: form.name.trim(),
    native_name: form.native_name.trim() || null,
    english_name: form.english_name.trim() || null,
    flag_file: form.flag_file || null,
    primary_color: form.primary_color || null,
    description: form.description.trim() || null,
    is_default: form.is_default,
    is_active: form.is_active,
    sort_order: form.sort_order,
  };
}

export default function LanguageForm({
  form,
  onChange,
}: {
  form: LanguageFormValues;
  onChange: (form: LanguageFormValues) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  async function handleFlagSelected(file: File) {
    setUploading(true);
    setUploadError(null);
    try {
      const filename = await uploadFlagSvg(file, form.code || "flag");
      onChange({ ...form, flag_file: filename });
    } catch {
      setUploadError("Upload fehlgeschlagen. Nur SVG-Dateien bis 500KB sind erlaubt.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <AdminLabel>Name *</AdminLabel>
          <AdminInput
            value={form.name}
            onChange={(e) => onChange({ ...form, name: e.target.value })}
            placeholder="Deutsch"
          />
        </div>
        <div>
          <AdminLabel>Code *</AdminLabel>
          <AdminInput
            value={form.code}
            onChange={(e) => onChange({ ...form, code: e.target.value })}
            placeholder="de"
            maxLength={10}
          />
        </div>
        <div>
          <AdminLabel>Locale (BCP-47) *</AdminLabel>
          <AdminInput
            value={form.locale}
            onChange={(e) => onChange({ ...form, locale: e.target.value })}
            placeholder="de-DE"
            maxLength={20}
          />
        </div>
        <div>
          <AdminLabel>Reihenfolge</AdminLabel>
          <AdminInput
            type="number"
            value={form.sort_order}
            onChange={(e) => onChange({ ...form, sort_order: Number(e.target.value) })}
          />
        </div>
        <div>
          <AdminLabel>Eigenbezeichnung (native name)</AdminLabel>
          <AdminInput
            value={form.native_name}
            onChange={(e) => onChange({ ...form, native_name: e.target.value })}
            placeholder="Deutsch"
          />
        </div>
        <div>
          <AdminLabel>Englische Bezeichnung</AdminLabel>
          <AdminInput
            value={form.english_name}
            onChange={(e) => onChange({ ...form, english_name: e.target.value })}
            placeholder="German"
          />
        </div>
      </div>

      <div>
        <AdminLabel>Beschreibung</AdminLabel>
        <AdminTextarea
          value={form.description}
          onChange={(e) => onChange({ ...form, description: e.target.value })}
          rows={3}
          placeholder="Optionale Beschreibung dieser Sprache..."
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <AdminLabel>Flagge (SVG)</AdminLabel>
          {form.flag_file ? (
            <div className="flex items-center gap-3 rounded-lg bg-white/[0.02] px-3 py-2 ring-1 ring-[var(--admin-border)]">
              <img src={`/flags/${form.flag_file}`} alt="" className="h-5 w-8 rounded object-cover" />
              <span className="flex-1 truncate text-sm text-[var(--admin-text-secondary)]">{form.flag_file}</span>
              <button
                type="button"
                onClick={() => onChange({ ...form, flag_file: "" })}
                className="text-xs text-[var(--admin-danger)] hover:underline"
              >
                Entfernen
              </button>
            </div>
          ) : (
            <AdminButton
              type="button"
              variant="secondary"
              size="sm"
              disabled={uploading}
              onClick={() => inputRef.current?.click()}
            >
              {uploading ? <Loader2 size={14} className="animate-spin" /> : <Upload size={14} />}
              {uploading ? "Wird hochgeladen..." : "SVG auswählen"}
            </AdminButton>
          )}
          <input
            ref={inputRef}
            type="file"
            accept=".svg,image/svg+xml"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFlagSelected(file);
              e.target.value = "";
            }}
          />
          {uploadError && <p className="mt-1 text-xs text-[var(--admin-danger)]">{uploadError}</p>}
        </div>

        <div>
          <AdminLabel>Farbe</AdminLabel>
          <input
            type="color"
            value={form.primary_color}
            onChange={(e) => onChange({ ...form, primary_color: e.target.value })}
            className="h-10 w-full rounded-lg bg-[var(--admin-card)] ring-1 ring-[var(--admin-border-strong)]"
          />
        </div>
      </div>

      <div className="flex items-center gap-6">
        <label className="flex cursor-pointer items-center gap-2.5">
          <AdminCheckbox
            checked={form.is_active}
            onCheckedChange={(checked) => onChange({ ...form, is_active: checked })}
          />
          <span className="text-sm text-[var(--admin-text-secondary)]">Aktiv</span>
        </label>
        <label className="flex cursor-pointer items-center gap-2.5">
          <AdminCheckbox
            checked={form.is_default}
            onCheckedChange={(checked) => onChange({ ...form, is_default: checked })}
          />
          <span className="text-sm text-[var(--admin-text-secondary)]">Standardsprache</span>
        </label>
      </div>
    </div>
  );
}
