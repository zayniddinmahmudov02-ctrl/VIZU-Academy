"use client";

import { useMemo, useState } from "react";
import { Plus } from "lucide-react";

import {
  AdminButton,
  AdminCheckbox,
  AdminInput,
  AdminLabel,
  AdminPageHeader,
  AdminSelect,
} from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FormDialog from "@/components/admin/form-dialog";
import { useCrudList, useCrudMutations } from "@/features/admin/hooks/use-crud";
import { languagesApi } from "@/features/admin/services/languages-service";
import { levelsApi } from "@/features/admin/services/levels-service";
import type { Level } from "@/features/admin/types/content.types";

const EMPTY_FORM = {
  language_id: "",
  level: "",
  title: "",
  description: "",
  order_index: 1,
  is_active: true,
};

export default function LevelsPage() {
  const { data: languages } = useCrudList("languages", languagesApi);
  const { data, isLoading } = useCrudList("levels", levelsApi);
  const { create, update, remove } = useCrudMutations("levels", levelsApi);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Level | null>(null);
  const [deleting, setDeleting] = useState<Level | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  const languageMap = useMemo(
    () => new Map((languages ?? []).map((l) => [l.id, l.name])),
    [languages],
  );

  function openCreate() {
    setEditing(null);
    setForm({ ...EMPTY_FORM, language_id: languages?.[0]?.id ?? "" });
    setError(null);
    setDialogOpen(true);
  }

  function openEdit(item: Level) {
    setEditing(item);
    setForm({
      language_id: item.language_id,
      level: item.level,
      title: item.title,
      description: item.description ?? "",
      order_index: item.order_index,
      is_active: item.is_active,
    });
    setError(null);
    setDialogOpen(true);
  }

  async function handleSubmit() {
    setError(null);
    try {
      if (editing) {
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        const { language_id: _languageId, ...updateData } = form;
        await update.mutateAsync({ id: editing.id, data: updateData });
      } else {
        await create.mutateAsync(form);
      }
      setDialogOpen(false);
    } catch {
      setError("Speichern fehlgeschlagen.");
    }
  }

  const columns: DataTableColumn<Level>[] = [
    { key: "level", header: "Level", render: (item) => <span className="font-semibold">{item.level}</span> },
    { key: "title", header: "Titel", render: (item) => item.title },
    { key: "language", header: "Sprache", render: (item) => languageMap.get(item.language_id) ?? "—" },
    { key: "order", header: "Reihenfolge", render: (item) => item.order_index },
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
        title="Levels"
        description="Sprachniveaus (A1, A2, B1, ...) je Sprache."
        action={
          <AdminButton onClick={openCreate} disabled={!languages || languages.length === 0}>
            <Plus size={16} />
            Neues Level
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
        emptyMessage={
          languages && languages.length === 0
            ? "Lege zuerst eine Sprache an, bevor du Levels erstellst."
            : "Noch keine Levels angelegt."
        }
      />

      <FormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={editing ? "Level bearbeiten" : "Neues Level"}
        footer={
          <>
            <AdminButton variant="ghost" onClick={() => setDialogOpen(false)}>
              Abbrechen
            </AdminButton>
            <AdminButton
              onClick={handleSubmit}
              disabled={create.isPending || update.isPending || !form.level || !form.title}
            >
              {create.isPending || update.isPending ? "Wird gespeichert..." : "Speichern"}
            </AdminButton>
          </>
        }
      >
        <div className="space-y-4">
          {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}

          {!editing && (
            <div>
              <AdminLabel>Sprache</AdminLabel>
              <AdminSelect
                value={form.language_id}
                onChange={(e) => setForm({ ...form, language_id: e.target.value })}
              >
                {(languages ?? []).map((lang) => (
                  <option key={lang.id} value={lang.id}>
                    {lang.name}
                  </option>
                ))}
              </AdminSelect>
            </div>
          )}

          <div>
            <AdminLabel>Level (z. B. A1, B2)</AdminLabel>
            <AdminInput
              value={form.level}
              onChange={(e) => setForm({ ...form, level: e.target.value })}
              placeholder="A1"
            />
          </div>

          <div>
            <AdminLabel>Titel</AdminLabel>
            <AdminInput
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="Grundlagen Deutsch A1"
            />
          </div>

          <div>
            <AdminLabel>Beschreibung</AdminLabel>
            <AdminInput
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>

          <div>
            <AdminLabel>Reihenfolge</AdminLabel>
            <AdminInput
              type="number"
              value={form.order_index}
              onChange={(e) => setForm({ ...form, order_index: Number(e.target.value) })}
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
        title="Level löschen"
        description={`"${deleting?.title}" wird dauerhaft gelöscht, inklusive aller Module und Lektionen.`}
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
