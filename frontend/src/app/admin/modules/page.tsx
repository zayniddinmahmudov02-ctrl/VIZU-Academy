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
import { levelsApi } from "@/features/admin/services/levels-service";
import { modulesApi } from "@/features/admin/services/modules-service";
import type { ModuleItem } from "@/features/admin/types/content.types";

const EMPTY_FORM = {
  course_id: "",
  number: 1,
  title: "",
  description: "",
  order_index: 1,
  is_active: true,
};

export default function ModulesPage() {
  const { data: levels } = useCrudList("levels", levelsApi);
  const { data, isLoading } = useCrudList("modules", modulesApi);
  const { create, update, remove } = useCrudMutations("modules", modulesApi);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<ModuleItem | null>(null);
  const [deleting, setDeleting] = useState<ModuleItem | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  const levelMap = useMemo(
    () => new Map((levels ?? []).map((l) => [l.id, `${l.level} — ${l.title}`])),
    [levels],
  );

  function openCreate() {
    setEditing(null);
    setForm({ ...EMPTY_FORM, course_id: levels?.[0]?.id ?? "" });
    setError(null);
    setDialogOpen(true);
  }

  function openEdit(item: ModuleItem) {
    setEditing(item);
    setForm({
      course_id: item.course_id,
      number: item.number,
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
        const { course_id: _courseId, ...updateData } = form;
        await update.mutateAsync({ id: editing.id, data: updateData });
      } else {
        await create.mutateAsync(form);
      }
      setDialogOpen(false);
    } catch {
      setError("Speichern fehlgeschlagen.");
    }
  }

  const columns: DataTableColumn<ModuleItem>[] = [
    { key: "number", header: "#", className: "w-12", render: (item) => item.number },
    { key: "title", header: "Titel", render: (item) => item.title },
    { key: "level", header: "Level", render: (item) => levelMap.get(item.course_id) ?? "—" },
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
        title="Modules"
        description="Module innerhalb eines Levels."
        action={
          <AdminButton onClick={openCreate} disabled={!levels || levels.length === 0}>
            <Plus size={16} />
            Neues Modul
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
          levels && levels.length === 0
            ? "Lege zuerst ein Level an, bevor du Module erstellst."
            : "Noch keine Module angelegt."
        }
      />

      <FormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={editing ? "Modul bearbeiten" : "Neues Modul"}
        footer={
          <>
            <AdminButton variant="ghost" onClick={() => setDialogOpen(false)}>
              Abbrechen
            </AdminButton>
            <AdminButton
              onClick={handleSubmit}
              disabled={create.isPending || update.isPending || !form.title}
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
              <AdminLabel>Level</AdminLabel>
              <AdminSelect
                value={form.course_id}
                onChange={(e) => setForm({ ...form, course_id: e.target.value })}
              >
                {(levels ?? []).map((level) => (
                  <option key={level.id} value={level.id}>
                    {level.level} — {level.title}
                  </option>
                ))}
              </AdminSelect>
            </div>
          )}

          <div>
            <AdminLabel>Modulnummer</AdminLabel>
            <AdminInput
              type="number"
              value={form.number}
              onChange={(e) => setForm({ ...form, number: Number(e.target.value) })}
            />
          </div>

          <div>
            <AdminLabel>Titel</AdminLabel>
            <AdminInput
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="Begrüßung und Vorstellung"
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
        title="Modul löschen"
        description={`"${deleting?.title}" wird dauerhaft gelöscht, inklusive aller Lektionen.`}
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
