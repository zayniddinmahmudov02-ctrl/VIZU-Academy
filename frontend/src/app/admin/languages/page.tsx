"use client";

import { useState } from "react";
import { Plus } from "lucide-react";

import {
  AdminButton,
  AdminCheckbox,
  AdminInput,
  AdminLabel,
  AdminPageHeader,
} from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FormDialog from "@/components/admin/form-dialog";
import { useCrudList, useCrudMutations } from "@/features/admin/hooks/use-crud";
import { languagesApi } from "@/features/admin/services/languages-service";
import type { Language } from "@/features/admin/types/content.types";

const EMPTY_FORM = { code: "", name: "", flag: "", is_active: true };

export default function LanguagesPage() {
  const { data, isLoading } = useCrudList("languages", languagesApi);
  const { create, update, remove } = useCrudMutations("languages", languagesApi);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Language | null>(null);
  const [deleting, setDeleting] = useState<Language | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  function openCreate() {
    setEditing(null);
    setForm(EMPTY_FORM);
    setError(null);
    setDialogOpen(true);
  }

  function openEdit(item: Language) {
    setEditing(item);
    setForm({ code: item.code, name: item.name, flag: item.flag ?? "", is_active: item.is_active });
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
    } catch (err) {
      const message =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ??
        "Speichern fehlgeschlagen.";
      setError(message);
    }
  }

  const columns: DataTableColumn<Language>[] = [
    {
      key: "flag",
      header: "",
      className: "w-10",
      render: (item) => <span className="text-lg">{item.flag || "🌐"}</span>,
    },
    { key: "name", header: "Name", render: (item) => item.name },
    { key: "code", header: "Code", render: (item) => item.code },
    {
      key: "is_active",
      header: "Status",
      render: (item) => (
        <span
          className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
            item.is_active
              ? "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]"
              : "bg-white/5 text-[var(--admin-text-muted)]"
          }`}
        >
          {item.is_active ? "Aktiv" : "Inaktiv"}
        </span>
      ),
    },
  ];

  return (
    <div>
      <AdminPageHeader
        title="Languages"
        description="Sprachen, die auf der Plattform unterrichtet werden."
        action={
          <AdminButton onClick={openCreate}>
            <Plus size={16} />
            Neue Sprache
          </AdminButton>
        }
      />

      <DataTable
        columns={columns}
        data={data}
        isLoading={isLoading}
        getRowId={(item) => item.id}
        onEdit={openEdit}
        onDelete={setDeleting}
        emptyMessage="Noch keine Sprachen angelegt."
      />

      <FormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={editing ? "Sprache bearbeiten" : "Neue Sprache"}
        footer={
          <>
            <AdminButton variant="ghost" onClick={() => setDialogOpen(false)}>
              Abbrechen
            </AdminButton>
            <AdminButton
              onClick={handleSubmit}
              disabled={create.isPending || update.isPending || !form.code || !form.name}
            >
              {create.isPending || update.isPending ? "Wird gespeichert..." : "Speichern"}
            </AdminButton>
          </>
        }
      >
        <div className="space-y-4">
          {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}

          <div>
            <AdminLabel>Name</AdminLabel>
            <AdminInput
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Deutsch"
            />
          </div>

          <div>
            <AdminLabel>Code</AdminLabel>
            <AdminInput
              value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value })}
              placeholder="de"
            />
          </div>

          <div>
            <AdminLabel>Flagge (Emoji)</AdminLabel>
            <AdminInput
              value={form.flag}
              onChange={(e) => setForm({ ...form, flag: e.target.value })}
              placeholder="🇩🇪"
            />
          </div>

          <label className="flex cursor-pointer items-center gap-2.5">
            <AdminCheckbox
              checked={form.is_active}
              onCheckedChange={(checked) => setForm({ ...form, is_active: checked })}
            />
            <span className="text-sm text-[var(--admin-text-secondary)]">Aktiv</span>
          </label>
        </div>
      </FormDialog>

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(open) => !open && setDeleting(null)}
        title="Sprache löschen"
        description={`"${deleting?.name}" wird dauerhaft gelöscht. Alle zugehörigen Levels, Module und Lektionen werden ebenfalls entfernt.`}
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
