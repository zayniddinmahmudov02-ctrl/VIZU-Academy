"use client";

import { useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, FileText, Upload, X, XCircle } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminInput, AdminLabel, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FileUploadField from "@/components/admin/file-upload-field";
import FormDialog from "@/components/admin/form-dialog";
import { germanLevels } from "@/constants/levels";
import { useCrudList, useCrudMutations } from "@/features/admin/hooks/use-crud";
import { booksApi, uploadBookPdf } from "@/features/admin/services/books-service";
import type { Book } from "@/features/admin/types/content.types";
import { formatFileSize } from "@/lib/upload-format";

const PDF_TYPE_ERROR = "Nur PDF-Dateien sind erlaubt.";

function isPdfFile(file: File): boolean {
  return file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
}

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
 * The "Neues Buch"/"Buch bearbeiten" dialog picks up a PDF inline (see
 * handleSubmit) — since POST .../{book_id}/upload-pdf needs a real id,
 * Speichern still does book create/update first and the PDF upload
 * second, but both happen in one click from the admin's point of view;
 * a PDF is required to create a new book. The table's own per-row
 * "Hochladen"/"Ersetzen" action (POST .../upload-pdf directly) still
 * works unchanged as a quick way to replace an existing book's PDF
 * without opening the full edit dialog. Publishing is a plain
 * is_published toggle, same as every other publishable content type in
 * this admin — a book is never visible to students, and its PDF never
 * downloadable, until Published. */
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

  // The "Neues Buch"/"Buch bearbeiten" modal's own inline PDF field —
  // separate state from the table's per-row upload above, since both
  // can be open/in-flight independently. A newly picked file here is
  // only actually uploaded once Speichern succeeds (see handleSubmit):
  // book create/update always happens first, since upload-pdf requires
  // an existing book_id.
  const [modalPdfFile, setModalPdfFile] = useState<File | null>(null);
  const [modalPdfError, setModalPdfError] = useState<string | null>(null);
  const [modalPdfUploading, setModalPdfUploading] = useState(false);
  const modalPdfInputRef = useRef<HTMLInputElement>(null);

  const data = (all ?? [])
    .filter((b) => !levelFilter || b.level === levelFilter)
    .sort((a, b) => a.order_index - b.order_index);

  function openCreate() {
    setEditing(null);
    setForm(EMPTY_FORM);
    setError(null);
    setModalPdfFile(null);
    setModalPdfError(null);
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
    setModalPdfFile(null);
    setModalPdfError(null);
    setDialogOpen(true);
  }

  function pickModalPdf() {
    modalPdfInputRef.current?.click();
  }

  function handleModalPdfSelected(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (modalPdfInputRef.current) modalPdfInputRef.current.value = "";
    if (!file) return;
    if (!isPdfFile(file)) {
      setModalPdfError(PDF_TYPE_ERROR);
      return;
    }
    setModalPdfError(null);
    setModalPdfFile(file);
  }

  function clearModalPdf() {
    setModalPdfFile(null);
    setModalPdfError(null);
  }

  // 1. validation -> 2. book create/update -> 3. PDF upload (only once
  // the book row exists, since POST .../{book_id}/upload-pdf needs a
  // real id) -> 4. the PDF is linked to the book by that same call
  // (BookService.upload_pdf sets storage_key/original_filename) ->
  // 5. close + refresh only after both steps succeed. A PDF is required
  // for a brand-new book (there's no table row to fall back to yet);
  // editing an existing book that already has a PDF doesn't force a
  // new one, matching "don't force existing incomplete books to
  // suddenly require a PDF on every metadata edit."
  async function handleSubmit() {
    setError(null);

    if (!editing && !modalPdfFile) {
      setError("Bitte wähle eine PDF-Datei aus.");
      return;
    }

    try {
      let book: Book;
      if (editing) {
        book = await update.mutateAsync({ id: editing.id, data: form });
      } else {
        book = await create.mutateAsync(form);
      }

      if (modalPdfFile) {
        setModalPdfUploading(true);
        try {
          await uploadBookPdf(book.id, modalPdfFile);
        } catch {
          // The book row itself is already saved at this point — point
          // `editing` at it so a retry from here updates instead of
          // creating a second, duplicate book, and keep the dialog open
          // with the same picked file so the admin can just retry.
          setEditing(book);
          setError("Buch gespeichert, aber PDF-Upload fehlgeschlagen. Bitte erneut versuchen.");
          await queryClient.invalidateQueries({ queryKey: ["books"] });
          return;
        } finally {
          setModalPdfUploading(false);
        }
      }

      await queryClient.invalidateQueries({ queryKey: ["books"] });
      setModalPdfFile(null);
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
          <img src={item.cover_url} alt="" loading="lazy" className="h-12 w-9 rounded object-cover" />
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
              disabled={
                create.isPending ||
                update.isPending ||
                modalPdfUploading ||
                !form.title ||
                !form.level ||
                (!editing && !modalPdfFile)
              }
            >
              {modalPdfUploading
                ? "PDF wird hochgeladen..."
                : create.isPending || update.isPending
                  ? "Wird gespeichert..."
                  : "Speichern"}
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

          <div>
            <AdminLabel>PDF-Datei{!editing && " *"}</AdminLabel>
            <input
              ref={modalPdfInputRef}
              type="file"
              accept="application/pdf,.pdf"
              className="hidden"
              onChange={handleModalPdfSelected}
            />

            {modalPdfFile ? (
              <div className="flex items-center gap-2 rounded-lg bg-[var(--admin-card)] px-3.5 py-2.5 ring-1 ring-[var(--admin-border-strong)]">
                <FileText size={15} className="shrink-0 text-[var(--admin-text-muted)]" />
                <span className="flex-1 truncate text-sm text-[var(--admin-text-secondary)]" title={modalPdfFile.name}>
                  {modalPdfFile.name}
                </span>
                <span className="shrink-0 text-xs text-[var(--admin-text-muted)]">
                  {formatFileSize(modalPdfFile.size)}
                </span>
                <button
                  type="button"
                  onClick={clearModalPdf}
                  aria-label="PDF entfernen"
                  className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-[var(--admin-text-muted)] hover:bg-[var(--admin-hover)] hover:text-[var(--admin-danger)]"
                >
                  <X size={14} />
                </button>
              </div>
            ) : editing?.storage_key ? (
              <div className="flex items-center gap-2 rounded-lg bg-[var(--admin-card)] px-3.5 py-2.5 ring-1 ring-[var(--admin-border-strong)]">
                <CheckCircle2 size={15} className="shrink-0 text-[var(--admin-accent)]" />
                <span className="flex-1 truncate text-sm text-[var(--admin-text-secondary)]">
                  Aktuelle Datei: {editing.original_filename ?? "PDF"}
                </span>
                <AdminButton type="button" variant="ghost" size="sm" onClick={pickModalPdf}>
                  <Upload size={13} />
                  Ersetzen
                </AdminButton>
              </div>
            ) : (
              <AdminButton type="button" variant="secondary" size="sm" onClick={pickModalPdf}>
                <Upload size={14} />
                PDF auswählen
              </AdminButton>
            )}

            {modalPdfError && <p className="mt-1.5 text-xs text-[var(--admin-danger)]">{modalPdfError}</p>}
          </div>

          <label className="flex cursor-pointer items-center gap-2.5">
            <AdminCheckbox
              checked={form.is_published}
              onCheckedChange={(checked) => setForm({ ...form, is_published: checked })}
            />
            <span className="text-sm text-[var(--admin-text-secondary)]">Veröffentlicht</span>
          </label>
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
