"use client";

import { useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, FileText, Upload, XCircle } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminInput, AdminLabel, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FileUploadField from "@/components/admin/file-upload-field";
import FormDialog from "@/components/admin/form-dialog";
import { germanLevels } from "@/constants/levels";
import { useCrudList, useCrudMutations } from "@/features/admin/hooks/use-crud";
import { booksApi, uploadBookPdf } from "@/features/admin/services/books-service";
import type { Book } from "@/features/admin/types/content.types";

const EMPTY_FORM = {
  title: "",
  author: "",
  description: "",
  level: germanLevels[0].code as string,
  cover_url: "",
  order_index: 1,
  is_published: false,
};

/** Admin "Bücher" manager — PDF books tagged by CEFR level, shown at the
 * top of the matching level's student lesson list (see book-row.tsx).
 * Upload -> preview -> save -> publish, per spec: metadata is created
 * first (Speichern), then the PDF itself is uploaded via a dedicated
 * per-row action once the book exists (POST .../upload-pdf) — mirrors
 * VideoManager's two-step create-then-upload shape. Publishing is a
 * plain is_published toggle, same as every other publishable content
 * type in this admin — a book is never visible to students, and its
 * PDF never downloadable, until Published. */
export default function BookManager() {
  const queryClient = useQueryClient();
  const { data: all, isLoading } = useCrudList("books", booksApi);
  const { create, update, remove } = useCrudMutations("books", booksApi, [["public-books"]]);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Book | null>(null);
  const [deleting, setDeleting] = useState<Book | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);
  const [levelFilter, setLevelFilter] = useState<string>("");

  const [uploadingId, setUploadingId] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pendingUploadBookId = useRef<string | null>(null);

  const data = (all ?? [])
    .filter((b) => !levelFilter || b.level === levelFilter)
    .sort((a, b) => a.order_index - b.order_index);

  function openCreate() {
    setEditing(null);
    setForm(EMPTY_FORM);
    setError(null);
    setDialogOpen(true);
  }

  function openEdit(item: Book) {
    setEditing(item);
    setForm({
      title: item.title,
      author: item.author ?? "",
      description: item.description ?? "",
      level: item.level,
      cover_url: item.cover_url ?? "",
      order_index: item.order_index,
      is_published: item.is_published,
    });
    setError(null);
    setDialogOpen(true);
  }

  async function handleSubmit() {
    setError(null);
    try {
      if (editing) {
        await update.mutateAsync({ id: editing.id, data: form });
      } else {
        await create.mutateAsync(form);
      }
      setDialogOpen(false);
    } catch {
      setError("Speichern fehlgeschlagen.");
    }
  }

  function triggerPdfUpload(bookId: string) {
    pendingUploadBookId.current = bookId;
    fileInputRef.current?.click();
  }

  async function handlePdfFileSelected(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    const bookId = pendingUploadBookId.current;
    if (!file || !bookId) return;
    setUploadError(null);
    setUploadingId(bookId);
    try {
      await uploadBookPdf(bookId, file);
      await queryClient.invalidateQueries({ queryKey: ["books"] });
    } catch {
      setUploadError("PDF-Upload fehlgeschlagen.");
    } finally {
      setUploadingId(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  const columns: DataTableColumn<Book>[] = [
    {
      key: "cover",
      header: "",
      className: "w-14",
      render: (item) =>
        item.cover_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={item.cover_url} alt="" className="h-12 w-9 rounded object-cover" />
        ) : (
          <div className="flex h-12 w-9 items-center justify-center rounded bg-white/5 text-[var(--admin-text-muted)]">
            <FileText size={16} />
          </div>
        ),
    },
    {
      key: "title",
      header: "Titel",
      render: (item) => (
        <div>
          <p className="font-medium">{item.title}</p>
          {item.author && <p className="text-xs text-[var(--admin-text-muted)]">{item.author}</p>}
        </div>
      ),
    },
    { key: "level", header: "Level", render: (item) => item.level },
    {
      key: "pdf",
      header: "PDF",
      render: (item) => (
        <div className="flex items-center gap-2">
          {item.storage_key ? (
            <span className="inline-flex items-center gap-1 text-xs text-[var(--admin-accent)]">
              <CheckCircle2 size={13} />
              Hochgeladen
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-xs text-[var(--admin-text-muted)]">
              <XCircle size={13} />
              Kein PDF
            </span>
          )}
          <AdminButton
            type="button"
            variant="ghost"
            size="sm"
            disabled={uploadingId === item.id}
            onClick={() => triggerPdfUpload(item.id)}
          >
            <Upload size={13} />
            {uploadingId === item.id ? "..." : item.storage_key ? "Ersetzen" : "Hochladen"}
          </AdminButton>
        </div>
      ),
    },
    {
      key: "is_published",
      header: "Status",
      render: (item) => (
        <span
          className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
            item.is_published
              ? "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]"
              : "bg-white/5 text-[var(--admin-text-muted)]"
          }`}
        >
          {item.is_published ? "Veröffentlicht" : "Entwurf"}
        </span>
      ),
    },
    { key: "order_index", header: "Reihenfolge", render: (item) => item.order_index },
  ];

  return (
    <div>
      <input ref={fileInputRef} type="file" accept="application/pdf" className="hidden" onChange={handlePdfFileSelected} />

      <div className="mb-4 flex flex-wrap items-center justify-between gap-2.5">
        <div className="w-40">
          <AdminSelect value={levelFilter} onChange={(e) => setLevelFilter(e.target.value)} className="h-9 text-sm">
            <option value="">Alle Level</option>
            {germanLevels.map((l) => (
              <option key={l.code} value={l.code}>
                {l.code}
              </option>
            ))}
          </AdminSelect>
        </div>
        <AdminButton onClick={openCreate}>Neues Buch</AdminButton>
      </div>

      {uploadError && <p className="mb-3 text-sm text-[var(--admin-danger)]">{uploadError}</p>}

      <DataTable
        columns={columns}
        data={data}
        isLoading={isLoading}
        getRowId={(item) => item.id}
        onEdit={openEdit}
        onDelete={setDeleting}
        emptyMessage="Noch keine Bücher angelegt."
      />

      <FormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={editing ? "Buch bearbeiten" : "Neues Buch"}
        size="lg"
        footer={
          <>
            <AdminButton variant="ghost" onClick={() => setDialogOpen(false)}>
              Abbrechen
            </AdminButton>
            <AdminButton
              onClick={handleSubmit}
              disabled={create.isPending || update.isPending || !form.title || !form.level}
            >
              {create.isPending || update.isPending ? "Wird gespeichert..." : "Speichern"}
            </AdminButton>
          </>
        }
      >
        <div className="space-y-4">
          {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <AdminLabel>Titel</AdminLabel>
              <AdminInput value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
            </div>
            <div>
              <AdminLabel>Muallif (Autor)</AdminLabel>
              <AdminInput value={form.author} onChange={(e) => setForm({ ...form, author: e.target.value })} />
            </div>
          </div>

          <div>
            <AdminLabel>Tavsif (Beschreibung)</AdminLabel>
            <AdminTextarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={3}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <AdminLabel>Level</AdminLabel>
              <AdminSelect value={form.level} onChange={(e) => setForm({ ...form, level: e.target.value })}>
                {germanLevels.map((l) => (
                  <option key={l.code} value={l.code}>
                    {l.code}
                  </option>
                ))}
              </AdminSelect>
            </div>
            <div>
              <AdminLabel>Reihenfolge</AdminLabel>
              <AdminInput
                type="number"
                value={form.order_index}
                onChange={(e) => setForm({ ...form, order_index: Number(e.target.value) })}
              />
            </div>
          </div>

          <div>
            <FileUploadField
              label="Cover (optional)"
              folder="images"
              accept="image/*"
              value={form.cover_url || null}
              onChange={(url) => setForm({ ...form, cover_url: url })}
            />
          </div>

          <label className="flex cursor-pointer items-center gap-2.5">
            <AdminCheckbox
              checked={form.is_published}
              onCheckedChange={(checked) => setForm({ ...form, is_published: checked })}
            />
            <span className="text-sm text-[var(--admin-text-secondary)]">Veröffentlicht</span>
          </label>

          {!editing && (
            <p className="text-xs text-[var(--admin-text-muted)]">
              Nach dem Speichern kann die PDF-Datei über die Tabelle hochgeladen werden.
            </p>
          )}
        </div>
      </FormDialog>

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(open) => !open && setDeleting(null)}
        title="Buch löschen"
        description={`"${deleting?.title}" wird dauerhaft gelöscht, inklusive der PDF-Datei.`}
        isPending={remove.isPending}
        onConfirm={async () => {
          if (!deleting) return;
          await remove.mutateAsync(deleting.id);
          setDeleting(null);
        }}
      />
    </div>
  );
}
