"use client";

import { useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Eye, EyeOff, FileText, Image as ImageIcon, Link2, Music, Pencil, Plus, RefreshCw, Trash2, Upload } from "lucide-react";

import { AdminButton, AdminInput, AdminLabel, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import FormDialog from "@/components/admin/form-dialog";
import {
  createLink,
  deleteResource,
  lmsAdminError,
  replaceResourceFile,
  resourcePreviewUrl,
  updateResource,
  uploadResource,
  type AdminResource,
} from "@/features/admin/services/lms-course-service";
import type { CompetencyKind, ResourceType } from "@/features/lms/types";

import { adminLmsKeys } from "./use-admin-lms";

type FileType = Exclude<ResourceType, "LINK">;
const ACCEPT: Record<FileType, string> = {
  AUDIO: ".mp3,.wav,.m4a,.ogg,audio/*",
  PDF: ".pdf,application/pdf",
  IMAGE: ".png,.jpg,.jpeg,.webp,.gif,image/*",
  DOCUMENT: ".docx,.pptx,.xlsx,.odt",
};
const TYPE_LABEL: Record<ResourceType, string> = { AUDIO: "Audio", PDF: "PDF", IMAGE: "Bild", DOCUMENT: "Dokument", LINK: "Link" };
const LIMITS = "Audio MP3/WAV/M4A/OGG bis 200 MB · PDF bis 50 MB · Bilder PNG/JPG/WebP/GIF bis 10 MB · Dokumente DOCX/PPTX/XLSX/ODT bis 30 MB";

function size(bytes: number | null) {
  if (!bytes) return "";
  return bytes >= 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

function TypeIcon({ type }: { type: ResourceType }) {
  const Icon = type === "AUDIO" ? Music : type === "IMAGE" ? ImageIcon : type === "LINK" ? Link2 : FileText;
  return <Icon size={16} />;
}

/** Learning resources of one competency (or, with competency = null, of the
 * whole lesson). New uploads are drafts; publishing asks for confirmation.
 * Type and size are checked by the server — its message is shown as is. */
export default function ResourceManager({ lessonId, competency, resources, canEdit }: {
  lessonId: string;
  competency: CompetencyKind | null;
  resources: AdminResource[];
  canEdit: boolean;
}) {
  const queryClient = useQueryClient();
  const refresh = () => queryClient.invalidateQueries({ queryKey: adminLmsKeys.lesson(lessonId) });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);
  const [form, setForm] = useState<{ type: FileType; title: string; description: string; duration: string; file: File | null }>({ type: "PDF", title: "", description: "", duration: "", file: null });
  const [link, setLink] = useState({ url: "", title: "" });
  const [publishing, setPublishing] = useState<AdminResource | null>(null);
  const [deleting, setDeleting] = useState<AdminResource | null>(null);
  const [editing, setEditing] = useState<AdminResource | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);
  const replaceInput = useRef<HTMLInputElement>(null);
  const [replaceTarget, setReplaceTarget] = useState<AdminResource | null>(null);
  const testScope = competency ?? "LESSON";

  async function run(action: () => Promise<unknown>, fallback?: string) {
    setBusy(true);
    setError(null);
    try {
      await action();
      await refresh();
      return true;
    } catch (err) {
      setError(lmsAdminError(err, fallback));
      return false;
    } finally {
      setBusy(false);
      setProgress(null);
    }
  }

  async function upload() {
    if (!form.file || !form.title.trim()) return;
    const ok = await run(
      () => uploadResource(lessonId, {
        file: form.file!, resource_type: form.type, title: form.title.trim(), competency,
        description: form.description.trim() || undefined, duration_seconds: form.duration ? Number(form.duration) : null,
      }, setProgress),
      "Upload fehlgeschlagen.",
    );
    if (ok) {
      setForm({ ...form, title: "", description: "", duration: "", file: null });
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  async function preview(r: AdminResource) {
    if (r.resource_type === "LINK" && r.external_url) {
      window.open(r.external_url, "_blank", "noopener,noreferrer");
      return;
    }
    try {
      const url = await resourcePreviewUrl(r.id);
      window.open(url, "_blank", "noopener");
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch (err) {
      setError(lmsAdminError(err, "Vorschau fehlgeschlagen."));
    }
  }

  return (
    <div className="space-y-4" data-testid="admin-resources" data-scope={testScope}>
      <h4 className="text-sm font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">Materialien {competency ? "dieser Kompetenz" : "der ganzen Lektion"}</h4>
      {error && <p className="rounded-xl bg-[var(--admin-danger)]/10 p-3 text-sm text-[var(--admin-danger)]" role="alert" data-testid="admin-resource-error">{error}</p>}

      {resources.length === 0 ? (
        <p className="text-sm text-[var(--admin-text-muted)]">Noch keine Materialien.</p>
      ) : (
        <ul className="space-y-2">
          {resources.map((r) => (
            <li key={r.id} className="flex flex-wrap items-center gap-3 rounded-xl bg-[var(--admin-hover)] p-3" data-testid="admin-resource" data-type={r.resource_type} data-published={r.is_published}>
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--admin-primary)]/10 text-[var(--admin-primary)]"><TypeIcon type={r.resource_type} /></span>
              <div className="min-w-0 flex-1">
                <p className="truncate font-semibold text-[var(--admin-text-primary)]">{r.title}</p>
                <p className="text-xs text-[var(--admin-text-muted)]">
                  {TYPE_LABEL[r.resource_type]}{r.size_bytes ? ` · ${size(r.size_bytes)}` : ""}{r.original_filename ? ` · ${r.original_filename}` : ""}{r.external_url ? ` · ${r.external_url}` : ""}
                </p>
              </div>
              {r.file_status === "missing" && <span className="rounded-full bg-[var(--admin-danger)]/10 px-2 py-0.5 text-xs font-semibold text-[var(--admin-danger)]">Datei fehlt</span>}
              <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${r.is_published ? "bg-emerald-500/10 text-emerald-500" : "bg-[var(--admin-card)] text-[var(--admin-text-muted)]"}`}>
                {r.is_published ? "sichtbar" : "Entwurf"}
              </span>
              <div className="flex gap-1">
                <AdminButton size="sm" variant="ghost" onClick={() => preview(r)} aria-label="Vorschau" title="Vorschau" data-testid="admin-resource-preview"><Eye size={14} /></AdminButton>
                {canEdit && (
                  <>
                    <AdminButton size="sm" variant="ghost" aria-label="Bearbeiten" title="Titel bearbeiten"
                                 onClick={() => { setEditing(r); setEditTitle(r.title); setEditDescription(r.description ?? ""); }}><Pencil size={14} /></AdminButton>
                    {r.resource_type !== "LINK" && (
                      <AdminButton size="sm" variant="ghost" aria-label="Datei ersetzen" title="Datei ersetzen" disabled={busy}
                                   onClick={() => { setReplaceTarget(r); replaceInput.current?.click(); }}><RefreshCw size={14} /></AdminButton>
                    )}
                    <AdminButton size="sm" variant="ghost" disabled={busy} data-testid="admin-resource-publish"
                                 aria-label={r.is_published ? "Verbergen" : "Veröffentlichen"} title={r.is_published ? "Verbergen" : "Veröffentlichen"}
                                 onClick={() => (r.is_published ? run(() => updateResource(r.id, { is_published: false })) : setPublishing(r))}>
                      {r.is_published ? <EyeOff size={14} /> : <Upload size={14} />}
                    </AdminButton>
                    <AdminButton size="sm" variant="ghost" aria-label="Löschen" title="Löschen" onClick={() => setDeleting(r)}><Trash2 size={14} /></AdminButton>
                  </>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      <input
        ref={replaceInput}
        type="file"
        className="hidden"
        accept={replaceTarget && replaceTarget.resource_type !== "LINK" ? ACCEPT[replaceTarget.resource_type] : undefined}
        onChange={(e) => {
          const file = e.target.files?.[0];
          e.target.value = "";
          if (file && replaceTarget) run(() => replaceResourceFile(replaceTarget.id, file, setProgress), "Datei konnte nicht ersetzt werden.");
        }}
      />

      {canEdit && (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="space-y-2 rounded-xl p-3 ring-1 ring-[var(--admin-border)]">
            <p className="text-sm font-semibold text-[var(--admin-text-primary)]">Datei hochladen (als Entwurf)</p>
            <div className="grid gap-2 sm:grid-cols-[9rem_1fr]">
              <AdminSelect value={form.type} aria-label="Dateityp" onChange={(e) => setForm({ ...form, type: e.target.value as FileType, file: null })} data-testid="admin-resource-type">
                <option value="PDF">PDF</option>
                <option value="AUDIO">Audio</option>
                <option value="IMAGE">Bild</option>
                <option value="DOCUMENT">Dokument</option>
              </AdminSelect>
              <AdminInput value={form.title} placeholder="Titel" aria-label="Titel" onChange={(e) => setForm({ ...form, title: e.target.value })} data-testid="admin-resource-title" />
            </div>
            <input ref={fileInput} type="file" accept={ACCEPT[form.type]} aria-label="Datei" data-testid="admin-resource-file"
                   onChange={(e) => setForm({ ...form, file: e.target.files?.[0] ?? null })}
                   className="block w-full text-sm text-[var(--admin-text-secondary)] file:mr-3 file:rounded-lg file:border-0 file:bg-[var(--admin-hover)] file:px-3 file:py-1.5 file:text-sm file:font-semibold" />
            {form.type === "AUDIO" && (
              <AdminInput type="number" min={1} value={form.duration} placeholder="Dauer in Sekunden (optional)" aria-label="Dauer" onChange={(e) => setForm({ ...form, duration: e.target.value })} />
            )}
            <AdminTextarea rows={2} value={form.description} placeholder="Beschreibung (optional)" onChange={(e) => setForm({ ...form, description: e.target.value })} />
            <p className="text-[11px] text-[var(--admin-text-muted)]">{LIMITS}</p>
            <div className="flex items-center gap-3">
              <AdminButton size="sm" disabled={busy || !form.file || !form.title.trim()} onClick={upload} data-testid="admin-resource-upload">
                <Upload size={14} /> {progress !== null ? `${progress}%` : "Hochladen"}
              </AdminButton>
            </div>
          </div>

          <div className="space-y-2 rounded-xl p-3 ring-1 ring-[var(--admin-border)]">
            <p className="text-sm font-semibold text-[var(--admin-text-primary)]">Externer Link (https)</p>
            <AdminInput value={link.title} placeholder="Titel" aria-label="Link-Titel" onChange={(e) => setLink({ ...link, title: e.target.value })} />
            <AdminInput value={link.url} placeholder="https://…" aria-label="URL" onChange={(e) => setLink({ ...link, url: e.target.value })} data-testid="admin-link-url" />
            <AdminButton size="sm" variant="secondary" disabled={busy || !link.url.trim() || !link.title.trim()} data-testid="admin-link-add"
                         onClick={async () => { if (await run(() => createLink(lessonId, { url: link.url.trim(), title: link.title.trim(), competency }), "Link konnte nicht angelegt werden.")) setLink({ url: "", title: "" }); }}>
              <Plus size={14} /> Link hinzufügen
            </AdminButton>
          </div>
        </div>
      )}

      <FormDialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)} title="Material bearbeiten" size="md"
        footer={<>
          <AdminButton variant="ghost" onClick={() => setEditing(null)}>Abbrechen</AdminButton>
          <AdminButton disabled={busy || !editTitle.trim()} onClick={async () => {
            if (editing && await run(() => updateResource(editing.id, { title: editTitle.trim(), description: editDescription.trim() || null }))) setEditing(null);
          }}>Speichern</AdminButton>
        </>}>
        <div className="space-y-3">
          <div><AdminLabel>Titel</AdminLabel><AdminInput value={editTitle} onChange={(e) => setEditTitle(e.target.value)} /></div>
          <div><AdminLabel>Beschreibung</AdminLabel><AdminTextarea rows={3} value={editDescription} onChange={(e) => setEditDescription(e.target.value)} /></div>
        </div>
      </FormDialog>

      <ConfirmDialog open={!!publishing} onOpenChange={(o) => !o && setPublishing(null)} title="Material veröffentlichen"
        description={`„${publishing?.title}“ wird für Schüler sichtbar, sobald Lektion und Kompetenz veröffentlicht sind.`}
        confirmLabel="Veröffentlichen" pendingLabel="Wird veröffentlicht..." variant="primary" isPending={busy}
        onConfirm={async () => { if (publishing && await run(() => updateResource(publishing.id, { is_published: true }))) setPublishing(null); }} />
      <ConfirmDialog open={!!deleting} onOpenChange={(o) => !o && setDeleting(null)} title="Material löschen"
        description={`„${deleting?.title}“ wird gelöscht. Die Datei wird nur entfernt, wenn sie von keinem anderen Eintrag verwendet wird.`}
        isPending={busy}
        onConfirm={async () => { if (deleting && await run(() => deleteResource(deleting.id), "Löschen fehlgeschlagen.")) setDeleting(null); }} />
    </div>
  );
}
