"use client";

/* eslint-disable @next/next/no-img-element -- admin thumbnails come from the cacheable cover endpoint */

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, EyeOff, Pencil, Plus, Star, Tag, Trash2 } from "lucide-react";

import { AdminButton, AdminCard, AdminInput, AdminLabel, AdminPageHeader, AdminSelect } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import FormDialog from "@/components/admin/form-dialog";
import { mediaUrl } from "@/features/medien/services/medien-service";
import {
  createItem, deleteItem, getCategories, listItems, medienError, updateItem, uploadBookFile, uploadCover, type AdminItem,
} from "@/features/admin/services/medien-admin-service";

import { CategoryManager, ContentFields, contentFrom, contentInput, emptyContent, FILE_DE, FilePick, fileSize, MedienTabs, ProgressBar, StatusPill, type ContentValues } from "./shared";

const PAGE = 25;

/** Admin → Medien → Bibliothek: books (cover, PDF, text, category, level, FREE / PAID with prices, special offer, featured,
 * Published / Draft / Hidden), categories, and the usual edit / replace / hide / delete. */
export default function BooksAdmin() {
  const queryClient = useQueryClient();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [access, setAccess] = useState("");
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<AdminItem | "new" | null>(null);
  const [deleting, setDeleting] = useState<AdminItem | null>(null);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const books = useQuery({ queryKey: ["admin-medien-books", q, status, access, page], queryFn: () => listItems("BOOK", { q, status, access, page, page_size: PAGE }), placeholderData: (p) => p });
  const categories = useQuery({ queryKey: ["admin-medien-categories", "BOOK"], queryFn: () => getCategories("BOOK") });
  const refresh = () => void queryClient.invalidateQueries({ queryKey: ["admin-medien-books"] });
  const patch = useMutation({
    mutationFn: ({ item, data }: { item: AdminItem; data: Parameters<typeof updateItem>[2] }) => updateItem("BOOK", item.id, data),
    onSuccess: refresh, onError: (e) => setMessage({ ok: false, text: medienError(e) }),
  });
  const remove = useMutation({
    mutationFn: (item: AdminItem) => deleteItem("BOOK", item.id),
    onSuccess: () => { setDeleting(null); setMessage({ ok: true, text: "Buch gelöscht (Datei und Cover entfernt)." }); refresh(); },
    onError: (e) => { setDeleting(null); setMessage({ ok: false, text: medienError(e) }); },
  });
  const catName = (id?: string | null) => categories.data?.find((c) => c.id === id)?.name ?? "—";
  const total = books.data?.total ?? 0;

  return (
    <div data-testid="books-admin">
      <AdminPageHeader title="Medien · Bibliothek" description="Bücher hochladen und verwalten: Cover, PDF, Kategorie, Niveau, kostenlos oder kostenpflichtig, Sonderangebote." action={<AdminButton onClick={() => setEditing("new")} data-testid="book-new"><Plus size={16} /> Neues Buch</AdminButton>} />
      <MedienTabs />
      <AdminCard className="mb-5"><h2 className="mb-3 text-sm font-semibold text-[var(--admin-text-primary)]">Kategorien</h2><CategoryManager kind="BOOK" /></AdminCard>

      {message && <p role="status" className={`mb-4 rounded-xl px-4 py-2.5 text-sm ${message.ok ? "bg-[var(--admin-success)]/10 text-[var(--admin-success)]" : "bg-[var(--admin-danger)]/10 text-[var(--admin-danger)]"}`} data-testid="books-message">{message.text}</p>}

      <div className="mb-4 flex flex-wrap gap-2">
        <AdminInput className="w-64" placeholder="Titel suchen …" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} aria-label="Suchen" data-testid="books-search" />
        <AdminSelect className="w-44" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} aria-label="Status" data-testid="books-filter-status"><option value="">Alle Status</option><option value="PUBLISHED">Veröffentlicht</option><option value="DRAFT">Entwurf</option><option value="HIDDEN">Ausgeblendet</option></AdminSelect>
        <AdminSelect className="w-44" value={access} onChange={(e) => { setAccess(e.target.value); setPage(1); }} aria-label="Zugang"><option value="">Kostenlos & kostenpflichtig</option><option value="FREE">Kostenlos</option><option value="PAID">Kostenpflichtig</option></AdminSelect>
      </div>

      <AdminCard className="overflow-x-auto p-0">
        <table className="w-full min-w-[900px] text-left text-sm" data-testid="books-table">
          <thead><tr className="text-xs uppercase text-[var(--admin-text-muted)]"><th className="p-3">Buch</th><th>Kategorie</th><th>Niveau</th><th>Zugang</th><th>Status</th><th>Datei</th><th>Aufrufe</th><th className="pr-3 text-right">Aktionen</th></tr></thead>
          <tbody>
            {(books.data?.items ?? []).map((b) => (
              <tr key={b.id} className="border-t border-[var(--admin-border)] align-middle" data-testid="book-row" data-title={b.title}>
                <td className="p-3"><div className="flex items-center gap-3">
                  <span className="h-14 w-10 shrink-0 overflow-hidden rounded bg-[var(--admin-hover)]">{b.cover_url && <img src={mediaUrl(b.cover_url)} alt="" className="h-full w-full object-cover" loading="lazy" />}</span>
                  <span className="min-w-0"><span className="block truncate font-semibold text-[var(--admin-text-primary)]">{b.title}</span><span className="block truncate text-xs text-[var(--admin-text-muted)]">{b.author ?? "—"}{b.is_featured ? " · ★ empfohlen" : ""}{b.is_special_offer ? " · Sonderangebot" : ""}</span></span>
                </div></td>
                <td>{catName(b.category_id)}</td><td>{b.level ?? "—"}</td>
                <td>{b.access_type === "FREE" ? "Kostenlos" : `${new Intl.NumberFormat("de-DE").format(b.price ?? 0)} UZS`}</td>
                <td><StatusPill status={b.status} /></td>
                <td className={b.file_status === "ok" ? "" : "text-[var(--admin-warning)]"}>{FILE_DE[b.file_status]}{b.file_size ? ` · ${fileSize(b.file_size)}` : ""}</td>
                <td>{b.views ?? 0}</td>
                <td className="pr-3"><div className="flex justify-end gap-1">
                  <AdminButton size="sm" variant="secondary" onClick={() => setEditing(b)} title="Bearbeiten" aria-label={`${b.title} bearbeiten`} data-testid="book-edit"><Pencil size={13} /></AdminButton>
                  <AdminButton size="sm" variant="secondary" onClick={() => patch.mutate({ item: b, data: { status: b.status === "PUBLISHED" ? "HIDDEN" : "PUBLISHED" } })} title={b.status === "PUBLISHED" ? "Ausblenden" : "Veröffentlichen"} aria-label={b.status === "PUBLISHED" ? "Ausblenden" : "Veröffentlichen"} data-testid="book-toggle">{b.status === "PUBLISHED" ? <EyeOff size={13} /> : <Eye size={13} />}</AdminButton>
                  <AdminButton size="sm" variant="secondary" disabled={b.access_type !== "PAID"} onClick={() => patch.mutate({ item: b, data: { is_special_offer: !b.is_special_offer } })} title="Sonderangebot an/aus" aria-label="Sonderangebot an/aus" data-testid="book-offer"><Tag size={13} className={b.is_special_offer ? "text-[var(--admin-primary)]" : ""} /></AdminButton>
                  <AdminButton size="sm" variant="secondary" onClick={() => patch.mutate({ item: b, data: { is_featured: !b.is_featured } })} title="Empfohlen an/aus" aria-label="Empfohlen an/aus" data-testid="book-featured"><Star size={13} className={b.is_featured ? "fill-current text-[var(--admin-primary)]" : ""} /></AdminButton>
                  <AdminButton size="sm" variant="danger" onClick={() => setDeleting(b)} title="Löschen" aria-label={`${b.title} löschen`} data-testid="book-delete"><Trash2 size={13} /></AdminButton>
                </div></td>
              </tr>
            ))}
            {books.data && !books.data.items.length && <tr><td colSpan={8} className="p-8 text-center text-[var(--admin-text-muted)]">Keine Bücher.</td></tr>}
          </tbody>
        </table>
      </AdminCard>
      {total > PAGE && <div className="mt-3 flex items-center justify-center gap-3 text-sm"><AdminButton size="sm" variant="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>Zurück</AdminButton><span>{page} / {Math.ceil(total / PAGE)}</span><AdminButton size="sm" variant="secondary" disabled={page >= Math.ceil(total / PAGE)} onClick={() => setPage(page + 1)}>Weiter</AdminButton></div>}

      {editing && <BookDialog key={editing === "new" ? "new" : editing.id} initial={editing === "new" ? null : editing} categories={(categories.data ?? []).map((c) => ({ id: c.id, name: c.name }))} onClose={() => { setEditing(null); refresh(); }} />}
      <ConfirmDialog open={!!deleting} onOpenChange={(o) => !o && setDeleting(null)} title="Buch löschen" description={`„${deleting?.title ?? ""}“ wird mit Cover und PDF gelöscht. Lese-Fortschritte und Kaufanfragen dazu werden entfernt.`} isPending={remove.isPending} onConfirm={() => deleting && remove.mutate(deleting)} />
    </div>
  );
}

function BookDialog({ initial, categories, onClose }: { initial: AdminItem | null; categories: { id: string; name: string }[]; onClose: () => void }) {
  const [item, setItem] = useState<AdminItem | null>(initial);
  const [values, setValues] = useState<ContentValues>(initial ? contentFrom(initial) : emptyContent());
  const [author, setAuthor] = useState(initial?.author ?? "");
  const [category, setCategory] = useState(initial?.category_id ?? "");
  const [year, setYear] = useState(initial?.year ? String(initial.year) : "");
  const [cover, setCover] = useState<File | null>(null);
  const [pdf, setPdf] = useState<File | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [percent, setPercent] = useState(0);
  const [note, setNote] = useState<{ ok: boolean; text: string } | null>(null);

  async function save() {
    setNote(null);
    setBusy("Speichern …");
    try {
      const data = { ...contentInput(values), author: author.trim() || null, category_id: category || null, year: year ? Number(year) : null };
      let saved = item ? await updateItem("BOOK", item.id, data) : await createItem("BOOK", data);
      setItem(saved);
      if (cover) { setBusy("Cover wird hochgeladen …"); setPercent(0); saved = await uploadCover("BOOK", saved.id, cover, setPercent); setCover(null); }
      if (pdf) { setBusy("PDF wird hochgeladen …"); setPercent(0); saved = await uploadBookFile(saved.id, pdf, setPercent); setPdf(null); }
      setItem(saved);
      setNote({ ok: true, text: "Gespeichert." });
    } catch (err) {
      setNote({ ok: false, text: medienError(err) });
    } finally {
      setBusy(null);
    }
  }

  return (
    <FormDialog open onOpenChange={(o) => { if (!o && !busy) onClose(); }} title={item ? "Buch bearbeiten" : "Neues Buch"} size="lg"
                footer={<><AdminButton variant="ghost" onClick={onClose} disabled={!!busy} data-testid="book-close">Schließen</AdminButton><AdminButton onClick={save} disabled={!!busy || !values.title.trim()} data-testid="book-save">{busy ?? "Speichern"}</AdminButton></>}>
      <div className="space-y-4" data-testid="book-dialog">
        <ContentFields value={values} onChange={setValues} />
        <div className="grid gap-3 sm:grid-cols-3">
          <div><AdminLabel>Autor</AdminLabel><AdminInput value={author} onChange={(e) => setAuthor(e.target.value)} maxLength={255} data-testid="f-author" /></div>
          <div><AdminLabel>Kategorie</AdminLabel><AdminSelect value={category} onChange={(e) => setCategory(e.target.value)} data-testid="f-category"><option value="">—</option>{categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</AdminSelect></div>
          <div><AdminLabel>Erscheinungsjahr</AdminLabel><AdminInput type="number" value={year} onChange={(e) => setYear(e.target.value)} data-testid="f-year" /></div>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <FilePick label={item?.has_cover ? "Cover ersetzen" : "Cover (JPG, PNG, WebP)"} accept="image/jpeg,image/png,image/webp" file={cover} onFile={setCover} testId="book-cover-file" />
          <FilePick label={item?.file_status === "ok" ? "PDF ersetzen" : "Buchdatei (PDF)"} accept="application/pdf" file={pdf} onFile={setPdf} testId="book-pdf-file" hint={item ? `Aktuell: ${FILE_DE[item.file_status]}${item.file_size ? ` · ${fileSize(item.file_size)}` : ""}` : "max. 300 MB"} />
        </div>
        {busy && busy.includes("hochgeladen") && <ProgressBar percent={percent} />}
        {note && <p role="status" className={`text-sm ${note.ok ? "text-[var(--admin-success)]" : "text-[var(--admin-danger)]"}`} data-testid="book-note">{note.text}</p>}
      </div>
    </FormDialog>
  );
}
