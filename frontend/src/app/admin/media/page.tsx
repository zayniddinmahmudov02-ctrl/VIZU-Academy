"use client";

import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, Film, Image as ImageIcon, Music, Trash2, Upload } from "lucide-react";

import { AdminButton, AdminPageHeader, AdminSelect } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import { deleteMediaAsset, listMediaAssets, uploadMediaAsset } from "@/features/admin/lib/upload";
import type { MediaAsset } from "@/features/admin/types/content.types";

const FOLDERS = [
  { value: "", label: "Alle Ordner" },
  { value: "videos", label: "Videos" },
  { value: "audio", label: "Audio" },
  { value: "images", label: "Bilder" },
  { value: "documents", label: "Dokumente" },
  { value: "thumbnails", label: "Thumbnails" },
];

const MEDIA_ICONS: Record<string, typeof Film> = {
  video: Film,
  audio: Music,
  image: ImageIcon,
  document: FileText,
};

function formatBytes(bytes: number | null): string {
  if (!bytes) return "—";
  const mb = bytes / (1024 * 1024);
  return mb >= 1 ? `${mb.toFixed(1)} MB` : `${Math.round(bytes / 1024)} KB`;
}

export default function MediaLibraryPage() {
  const queryClient = useQueryClient();
  const [folder, setFolder] = useState("");
  const [deleting, setDeleting] = useState<MediaAsset | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadFolder, setUploadFolder] = useState<"videos" | "audio" | "images" | "documents" | "thumbnails">(
    "images",
  );

  const { data, isLoading } = useQuery({
    queryKey: ["media-library-all", folder],
    queryFn: () => listMediaAssets(folder || undefined),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadMediaAsset(file, uploadFolder),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["media-library-all"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteMediaAsset(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["media-library-all"] });
      setDeleting(null);
    },
  });

  return (
    <div>
      <AdminPageHeader
        title="Media Library"
        description="Zentrale Ablage für Videos, Audio, Bilder und Dokumente."
        action={
          <div className="flex items-center gap-2">
            <AdminSelect
              value={uploadFolder}
              onChange={(e) => setUploadFolder(e.target.value as typeof uploadFolder)}
              className="w-40"
            >
              <option value="images">Bilder</option>
              <option value="audio">Audio</option>
              <option value="videos">Videos</option>
              <option value="documents">Dokumente</option>
              <option value="thumbnails">Thumbnails</option>
            </AdminSelect>
            <AdminButton onClick={() => fileInputRef.current?.click()} disabled={uploadMutation.isPending}>
              <Upload size={15} />
              {uploadMutation.isPending ? "Wird hochgeladen..." : "Hochladen"}
            </AdminButton>
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) uploadMutation.mutate(file);
                e.target.value = "";
              }}
            />
          </div>
        }
      />

      <div className="mb-4 flex flex-wrap gap-2">
        {FOLDERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFolder(f.value)}
            className={`rounded-full px-3.5 py-1.5 text-xs font-semibold transition ${
              folder === f.value
                ? "bg-[var(--admin-primary)] text-white"
                : "bg-[var(--admin-card)] text-[var(--admin-text-secondary)] ring-1 ring-[var(--admin-border)] hover:text-[var(--admin-text-primary)]"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {isLoading && (
        <div className="flex justify-center py-16">
          <div className="h-8 w-8 animate-spin rounded-full border-[3px] border-white/10 border-t-[var(--admin-primary)]" />
        </div>
      )}

      {!isLoading && (!data || data.length === 0) && (
        <p className="rounded-2xl bg-[var(--admin-card)] p-10 text-center text-sm text-[var(--admin-text-muted)] ring-1 ring-[var(--admin-border)]">
          Keine Dateien gefunden.
        </p>
      )}

      {!isLoading && data && data.length > 0 && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {data.map((asset) => {
            const Icon = MEDIA_ICONS[asset.media_type] ?? FileText;
            return (
              <div
                key={asset.id}
                className="group relative overflow-hidden rounded-2xl bg-[var(--admin-card)] ring-1 ring-[var(--admin-border)]"
              >
                <div className="flex h-28 items-center justify-center bg-black/20">
                  {asset.media_type === "image" ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={asset.url} alt="" loading="lazy" className="h-full w-full object-cover" />
                  ) : (
                    <Icon size={28} className="text-[var(--admin-text-muted)]" />
                  )}
                </div>
                <div className="p-3">
                  <p className="truncate text-xs font-medium text-[var(--admin-text-primary)]" title={asset.filename}>
                    {asset.filename}
                  </p>
                  <p className="mt-0.5 text-[10px] text-[var(--admin-text-muted)]">
                    {formatBytes(asset.size_bytes)}
                  </p>
                </div>
                <button
                  onClick={() => setDeleting(asset)}
                  aria-label="Löschen"
                  className="absolute right-2 top-2 flex h-7 w-7 items-center justify-center rounded-lg bg-black/50 text-white opacity-0 transition group-hover:opacity-100 hover:bg-[var(--admin-danger)]"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            );
          })}
        </div>
      )}

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(open) => !open && setDeleting(null)}
        title="Datei löschen"
        description={`"${deleting?.filename}" wird dauerhaft aus der Medienbibliothek entfernt.`}
        isPending={deleteMutation.isPending}
        onConfirm={() => deleting && deleteMutation.mutate(deleting.id)}
      />
    </div>
  );
}
