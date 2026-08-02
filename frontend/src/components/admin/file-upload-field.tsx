"use client";

import { useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { FolderOpen, Loader2, Upload, X } from "lucide-react";

import { listMediaAssets, uploadMediaAsset } from "@/features/admin/lib/upload";
import type { MediaAsset } from "@/features/admin/types/content.types";

import { AdminButton } from "./admin-ui";
import FormDialog from "./form-dialog";

interface Props {
  value: string | null;
  onChange: (url: string) => void;
  folder: "videos" | "audio" | "images" | "documents" | "thumbnails";
  accept?: string;
  label?: string;
}

export default function FileUploadField({ value, onChange, folder, accept, label }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [browseOpen, setBrowseOpen] = useState(false);

  async function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);
    setUploading(true);

    try {
      const asset = await uploadMediaAsset(file, folder);
      onChange(asset.url);
    } catch {
      setError("Upload fehlgeschlagen. Bitte erneut versuchen.");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div>
      {label && (
        <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
          {label}
        </label>
      )}

      {value ? (
        <div className="flex items-center gap-2 rounded-lg bg-[var(--admin-card)] px-3.5 py-2.5 ring-1 ring-[var(--admin-border-strong)]">
          <span className="flex-1 truncate text-sm text-[var(--admin-text-secondary)]" title={value}>
            {value}
          </span>
          <button
            type="button"
            onClick={() => onChange("")}
            aria-label="Entfernen"
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-[var(--admin-text-muted)] hover:bg-white/5 hover:text-[var(--admin-danger)]"
          >
            <X size={14} />
          </button>
        </div>
      ) : (
        <div className="flex items-center gap-2">
          <AdminButton
            type="button"
            variant="secondary"
            size="sm"
            disabled={uploading}
            onClick={() => inputRef.current?.click()}
          >
            {uploading ? <Loader2 size={14} className="animate-spin" /> : <Upload size={14} />}
            {uploading ? "Wird hochgeladen..." : "Neu hochladen"}
          </AdminButton>
          <AdminButton
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setBrowseOpen(true)}
          >
            <FolderOpen size={14} />
            Vorhandene auswählen
          </AdminButton>
          <input
            ref={inputRef}
            type="file"
            accept={accept}
            className="hidden"
            onChange={handleFileSelect}
          />
        </div>
      )}

      {error && <p className="mt-1.5 text-xs text-[var(--admin-danger)]">{error}</p>}

      <MediaBrowseDialog
        open={browseOpen}
        onOpenChange={setBrowseOpen}
        folder={folder}
        onSelect={(url) => {
          onChange(url);
          setBrowseOpen(false);
        }}
      />
    </div>
  );
}

function MediaBrowseDialog({
  open,
  onOpenChange,
  folder,
  onSelect,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  folder: string;
  onSelect: (url: string) => void;
}) {
  const { data, isLoading } = useQuery({
    queryKey: ["media-library", folder],
    queryFn: () => listMediaAssets(folder),
    enabled: open,
  });

  return (
    <FormDialog
      open={open}
      onOpenChange={onOpenChange}
      title="Vorhandene Datei auswählen"
      size="lg"
    >
      {isLoading && (
        <div className="flex justify-center py-10">
          <Loader2 size={22} className="animate-spin text-[var(--admin-primary)]" />
        </div>
      )}

      {!isLoading && (!data || data.length === 0) && (
        <p className="py-10 text-center text-sm text-[var(--admin-text-muted)]">
          Keine Dateien in diesem Ordner gefunden.
        </p>
      )}

      {!isLoading && data && data.length > 0 && (
        <div className="grid max-h-[50vh] grid-cols-2 gap-3 overflow-y-auto sm:grid-cols-3">
          {data.map((asset: MediaAsset) => (
            <button
              key={asset.id}
              type="button"
              onClick={() => onSelect(asset.url)}
              className="flex flex-col items-start gap-1 rounded-lg bg-white/[0.02] p-3 text-left ring-1 ring-[var(--admin-border)] transition hover:ring-[var(--admin-primary)]"
            >
              <span className="w-full truncate text-xs font-medium text-[var(--admin-text-primary)]">
                {asset.filename}
              </span>
              <span className="text-[10px] uppercase tracking-wide text-[var(--admin-text-muted)]">
                {asset.media_type}
              </span>
            </button>
          ))}
        </div>
      )}
    </FormDialog>
  );
}
