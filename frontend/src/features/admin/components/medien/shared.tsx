"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Eye, EyeOff, Pencil, Plus, Trash2 } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminInput, AdminLabel, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import {
  createCategory, deleteCategory, getCategories, medienError, updateCategory, type Access, type AdminItem, type ItemInput, type Status,
} from "@/features/admin/services/medien-admin-service";

export const fileSize = (bytes: number | null | undefined) => {
  if (!bytes) return "—";
  const mb = bytes / 1048576;
  return mb >= 1024 ? `${(mb / 1024).toFixed(2)} GB` : mb >= 1 ? `${mb.toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
};

export const STATUS_DE: Record<Status, string> = { DRAFT: "Entwurf", PUBLISHED: "Veröffentlicht", HIDDEN: "Ausgeblendet" };
export const STATUS_TONE: Record<Status, string> = {
  DRAFT: "bg-[var(--admin-hover)] text-[var(--admin-text-secondary)]", PUBLISHED: "bg-[var(--admin-success)]/15 text-[var(--admin-success)]", HIDDEN: "bg-[var(--admin-warning)]/15 text-[var(--admin-warning)]",
};
export const FILE_DE = { ok: "Datei vorhanden", missing: "Datei fehlt auf dem Server", none: "Keine Datei" } as const;

export function StatusPill({ status }: { status: Status }) {
  return <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${STATUS_TONE[status]}`} data-testid="status-pill" data-status={status}>{STATUS_DE[status]}</span>;
}

const TABS = [["/admin/medien", "Übersicht"], ["/admin/medien/bibliothek", "Bibliothek"], ["/admin/medien/musik", "Musik"], ["/admin/medien/filme", "Filme"]] as const;

export function MedienTabs() {
  const path = usePathname() ?? "";
  return (
    <nav className="mb-5 flex flex-wrap gap-2" aria-label="Medien" data-testid="medien-tabs">
      {TABS.map(([href, label]) => (
        <Link key={href} href={href} className={`rounded-full px-4 py-1.5 text-sm font-semibold transition ${path === href ? "bg-[var(--admin-primary)] text-white" : "bg-[var(--admin-card)] text-[var(--admin-text-secondary)] ring-1 ring-[var(--admin-border)] hover:bg-[var(--admin-hover)]"}`}>{label}</Link>
      ))}
    </nav>
  );
}

/** Categories of books / films: create, rename, hide (inactive) and delete when unused. The student catalog shows the
 * active ones; nothing about them is hard-coded in the frontend. */
export function CategoryManager({ kind }: { kind: "BOOK" | "FILM" }) {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [edit, setEdit] = useState<{ id: string; name: string } | null>(null);
  const [del, setDel] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { data } = useQuery({ queryKey: ["admin-medien-categories", kind], queryFn: () => getCategories(kind) });
  const refresh = () => { setError(null); void queryClient.invalidateQueries({ queryKey: ["admin-medien-categories", kind] }); };
  const fail = (e: unknown) => setError(medienError(e));
  const add = useMutation({ mutationFn: () => createCategory(kind, name.trim()), onSuccess: () => { setName(""); refresh(); }, onError: fail });
  const upd = useMutation({ mutationFn: (v: { id: string; data: { name?: string; is_active?: boolean } }) => updateCategory(v.id, v.data), onSuccess: () => { setEdit(null); refresh(); }, onError: fail });
  const rm = useMutation({ mutationFn: (id: string) => deleteCategory(id), onSuccess: () => { setDel(null); refresh(); }, onError: (e) => { setDel(null); fail(e); } });

  return (
    <div data-testid="category-manager">
      <div className="flex flex-wrap gap-2">
        {(data ?? []).map((c) => (
          <span key={c.id} className={`inline-flex items-center gap-1 rounded-full py-1 pl-3 pr-1 text-sm ring-1 ring-[var(--admin-border)] ${c.is_active ? "bg-[var(--admin-card)]" : "bg-[var(--admin-hover)] opacity-70"}`} data-testid="category-chip" data-name={c.name}>
            {edit?.id === c.id ? (
              <form className="flex items-center gap-1" onSubmit={(e) => { e.preventDefault(); if (edit.name.trim()) upd.mutate({ id: c.id, data: { name: edit.name.trim() } }); }}>
                <AdminInput className="h-7 w-36 px-2 text-xs" value={edit.name} autoFocus onChange={(e) => setEdit({ id: c.id, name: e.target.value })} aria-label="Kategoriename" data-testid="category-edit-input" />
                <button className="rounded-full p-1 text-[var(--admin-success)]" aria-label="Speichern" data-testid="category-edit-save"><Check size={14} /></button>
              </form>
            ) : (
              <><span className="font-medium text-[var(--admin-text-primary)]">{c.name}</span><span className="text-xs text-[var(--admin-text-muted)]">{c.item_count}</span></>
            )}
            <button className="rounded-full p-1 text-[var(--admin-text-muted)] hover:text-[var(--admin-primary)]" aria-label={`${c.name} umbenennen`} onClick={() => setEdit({ id: c.id, name: c.name })} data-testid="category-rename"><Pencil size={12} /></button>
            <button className="rounded-full p-1 text-[var(--admin-text-muted)] hover:text-[var(--admin-primary)]" aria-label={c.is_active ? `${c.name} ausblenden` : `${c.name} einblenden`} onClick={() => upd.mutate({ id: c.id, data: { is_active: !c.is_active } })} data-testid="category-toggle">{c.is_active ? <Eye size={12} /> : <EyeOff size={12} />}</button>
            <button className="rounded-full p-1 text-[var(--admin-text-muted)] hover:text-[var(--admin-danger)]" aria-label={`${c.name} löschen`} onClick={() => setDel(c.id)} data-testid="category-delete"><Trash2 size={12} /></button>
          </span>
        ))}
      </div>
      <form className="mt-3 flex max-w-md gap-2" onSubmit={(e) => { e.preventDefault(); if (name.trim()) add.mutate(); }}>
        <AdminInput value={name} onChange={(e) => setName(e.target.value)} placeholder="Neue Kategorie" maxLength={120} aria-label="Neue Kategorie" data-testid="category-new-input" />
        <AdminButton disabled={!name.trim() || add.isPending} data-testid="category-add"><Plus size={15} /> Hinzufügen</AdminButton>
      </form>
      {error && <p role="alert" className="mt-2 text-sm text-[var(--admin-danger)]" data-testid="category-error">{error}</p>}
      <ConfirmDialog open={!!del} onOpenChange={(o) => !o && setDel(null)} title="Kategorie löschen" description="Die Kategorie wird gelöscht. Das geht nur, wenn kein Inhalt sie mehr verwendet." isPending={rm.isPending} onConfirm={() => del && rm.mutate(del)} />
    </div>
  );
}

export interface ContentValues {
  title: string; description: string; language: string; level: string; access_type: Access; price: string; old_price: string;
  is_special_offer: boolean; is_featured: boolean; status: Status;
}

export const emptyContent = (): ContentValues => ({ title: "", description: "", language: "de", level: "", access_type: "FREE", price: "", old_price: "", is_special_offer: false, is_featured: false, status: "DRAFT" });

export const contentFrom = (i: AdminItem): ContentValues => ({
  title: i.title, description: i.description ?? "", language: i.language, level: i.level ?? "", access_type: i.access_type, price: i.price ? String(i.price) : "",
  old_price: i.old_price ? String(i.old_price) : "", is_special_offer: i.is_special_offer, is_featured: i.is_featured, status: i.status,
});

export const contentInput = (v: ContentValues): ItemInput => ({
  title: v.title.trim(), description: v.description.trim() || null, language: v.language.trim() || "de", level: v.level || null, access_type: v.access_type,
  ...(v.access_type === "PAID" ? { price: v.price ? Number(v.price) : null, old_price: v.old_price ? Number(v.old_price) : null } : {}),
  is_special_offer: v.access_type === "PAID" && v.is_special_offer, is_featured: v.is_featured, status: v.status,
});

function Field({ label, children, className }: { label: string; children: React.ReactNode; className?: string }) {
  return <div className={className}><AdminLabel>{label}</AdminLabel>{children}</div>;
}

/** The fields every Medienwelt content has: text, language, level, FREE / PAID with prices, special offer, featured, status. */
export function ContentFields({ value, onChange, withDescription = true }: { value: ContentValues; onChange: (v: ContentValues) => void; withDescription?: boolean }) {
  const set = <K extends keyof ContentValues>(k: K, v: ContentValues[K]) => onChange({ ...value, [k]: v });
  const paid = value.access_type === "PAID";
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <Field label="Titel *" className="sm:col-span-2"><AdminInput value={value.title} onChange={(e) => set("title", e.target.value)} maxLength={255} data-testid="f-title" /></Field>
      {withDescription && <Field label="Beschreibung" className="sm:col-span-2"><AdminTextarea rows={3} value={value.description} onChange={(e) => set("description", e.target.value)} data-testid="f-description" /></Field>}
      <Field label="Sprache"><AdminInput value={value.language} onChange={(e) => set("language", e.target.value)} maxLength={10} placeholder="de" data-testid="f-language" /></Field>
      <Field label="Niveau"><AdminSelect value={value.level} onChange={(e) => set("level", e.target.value)} data-testid="f-level"><option value="">—</option>{["A1", "A2", "B1", "B2", "C1"].map((l) => <option key={l} value={l}>{l}</option>)}</AdminSelect></Field>
      <Field label="Zugang"><AdminSelect value={value.access_type} onChange={(e) => set("access_type", e.target.value as Access)} data-testid="f-access"><option value="FREE">Kostenlos (FREE)</option><option value="PAID">Kostenpflichtig (PAID)</option></AdminSelect></Field>
      <Field label="Status"><AdminSelect value={value.status} onChange={(e) => set("status", e.target.value as Status)} data-testid="f-status">{(Object.keys(STATUS_DE) as Status[]).map((s) => <option key={s} value={s}>{STATUS_DE[s]}</option>)}</AdminSelect></Field>
      {paid && (
        <>
          <Field label="Preis (UZS) *"><AdminInput type="number" min={1} value={value.price} onChange={(e) => set("price", e.target.value)} data-testid="f-price" /></Field>
          <Field label="Alter Preis (durchgestrichen)"><AdminInput type="number" min={1} value={value.old_price} onChange={(e) => set("old_price", e.target.value)} data-testid="f-old-price" /></Field>
          <label className="flex items-center gap-2 text-sm text-[var(--admin-text-primary)]"><AdminCheckbox checked={value.is_special_offer} onCheckedChange={(c) => set("is_special_offer", c)} aria-label="Sonderangebot" /> Sonderangebot (Student-Seite „Spezielles Angebot“)</label>
        </>
      )}
      <label className="flex items-center gap-2 text-sm text-[var(--admin-text-primary)]"><AdminCheckbox checked={value.is_featured} onCheckedChange={(c) => set("is_featured", c)} aria-label="Empfohlen" /> Empfohlen</label>
    </div>
  );
}

export function FilePick({ label, accept, onFile, file, testId, hint }: { label: string; accept: string; onFile: (f: File | null) => void; file: File | null; testId: string; hint?: string }) {
  return (
    <Field label={label}>
      <input type="file" accept={accept} onChange={(e) => onFile(e.target.files?.[0] ?? null)} data-testid={testId}
             className="block w-full text-sm text-[var(--admin-text-secondary)] file:mr-3 file:rounded-lg file:border-0 file:bg-[var(--admin-hover)] file:px-3 file:py-2 file:text-sm file:font-semibold file:text-[var(--admin-text-primary)]" />
      {file && <p className="mt-1 text-xs text-[var(--admin-text-muted)]">{file.name} · {fileSize(file.size)}</p>}
      {hint && <p className="mt-1 text-xs text-[var(--admin-text-muted)]">{hint}</p>}
    </Field>
  );
}

export function ProgressBar({ percent, testId = "upload-progress" }: { percent: number; testId?: string }) {
  return (
    <div className="h-1.5 overflow-hidden rounded-full bg-[var(--admin-border)]" data-testid={testId} data-percent={percent}>
      <div className="h-full bg-[var(--admin-primary)] transition-all" style={{ width: `${percent}%` }} />
    </div>
  );
}
