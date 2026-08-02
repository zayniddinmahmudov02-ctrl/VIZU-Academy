"use client";

import { useRef, useState } from "react";
import { Loader2, Upload, X } from "lucide-react";

import { AdminButton } from "@/components/admin/admin-ui";
import { uploadMediaAsset } from "@/features/admin/lib/upload";

interface Props {
  value: string | null;
  onChange: (url: string | null) => void;
  folder: "images" | "audio" | "documents";
  label: string;
  accept: string;
}

export default function MediaUploadButton({ value, onChange, folder, label, accept }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(file: File) {
    setUploading(true);
    setError(null);
    try {
      const asset = await uploadMediaAsset(file, folder);
      onChange(asset.url);
    } catch {
      setError("Upload fehlgeschlagen.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">{label}</label>
      {value ? (
        <div className="flex items-center gap-2 rounded-lg bg-white/[0.02] px-3 py-2 ring-1 ring-[var(--admin-border)]">
          <a
            href={value}
            target="_blank"
            rel="noreferrer"
            className="flex-1 truncate text-sm text-[var(--admin-primary)] hover:underline"
          >
            {value.split("/").pop()}
          </a>
          <button
            type="button"
            onClick={() => onChange(null)}
            aria-label="Entfernen"
            className="flex h-6 w-6 items-center justify-center rounded-md text-[var(--admin-text-muted)] hover:bg-[var(--admin-danger)]/10 hover:text-[var(--admin-danger)]"
          >
            <X size={13} />
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
          {uploading ? "Wird hochgeladen..." : "Datei auswählen"}
        </AdminButton>
      )}
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
          e.target.value = "";
        }}
      />
      {error && <p className="mt-1 text-xs text-[var(--admin-danger)]">{error}</p>}
    </div>
  );
}
