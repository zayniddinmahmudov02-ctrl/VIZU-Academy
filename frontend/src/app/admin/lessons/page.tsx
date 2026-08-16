"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Plus, Settings2 } from "lucide-react";

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
import { lessonsApi } from "@/features/admin/services/lessons-service";
import { modulesApi } from "@/features/admin/services/modules-service";
import type { Lesson } from "@/features/admin/types/content.types";

const EMPTY_FORM = {
  module_id: "",
  number: 1,
  title: "",
  duration: 0,
  is_free: false,
};

export default function LessonsPage() {
  const { data: modules } = useCrudList("modules", modulesApi);
  const { data, isLoading } = useCrudList("lessons", lessonsApi);
  const { create, update, remove } = useCrudMutations("lessons", lessonsApi, [
    ["public-lessons-by-module"],
    ["public-courses-with-lesson-counts"],
    ["course-lessons-content-status"],
  ]);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Lesson | null>(null);
  const [deleting, setDeleting] = useState<Lesson | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  const moduleMap = useMemo(
    () => new Map((modules ?? []).map((m) => [m.id, m.title])),
    [modules],
  );

  function openCreate() {
    setEditing(null);
    setForm({ ...EMPTY_FORM, module_id: modules?.[0]?.id ?? "" });
    setError(null);
    setDialogOpen(true);
  }

  function openEdit(item: Lesson) {
    setEditing(item);
    setForm({
      module_id: item.module_id,
      number: item.number,
      title: item.title,
      duration: item.duration,
      is_free: item.is_free,
    });
    setError(null);
    setDialogOpen(true);
  }

  async function handleSubmit() {
    setError(null);
    try {
      if (editing) {
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        const { module_id: _moduleId, ...updateData } = form;
        await update.mutateAsync({ id: editing.id, data: updateData });
      } else {
        await create.mutateAsync(form);
      }
      setDialogOpen(false);
    } catch {
      setError("Speichern fehlgeschlagen.");
    }
  }

  const columns: DataTableColumn<Lesson>[] = [
    { key: "number", header: "#", className: "w-12", render: (item) => item.number },
    {
      key: "title",
      header: "Titel",
      render: (item) => (
        <Link
          href={`/admin/lessons/${item.id}`}
          className="font-medium text-[var(--admin-primary)] hover:underline"
        >
          {item.title}
        </Link>
      ),
    },
    { key: "module", header: "Modul", render: (item) => moduleMap.get(item.module_id) ?? "—" },
    { key: "duration", header: "Dauer (Min.)", render: (item) => item.duration },
    {
      key: "is_free",
      header: "Kostenlos",
      render: (item) =>
        item.is_free ? (
          <span className="rounded-full bg-[var(--admin-accent)]/15 px-2.5 py-1 text-xs font-semibold text-[var(--admin-accent)]">
            Ja
          </span>
        ) : (
          <span className="text-xs text-[var(--admin-text-muted)]">Nein</span>
        ),
    },
    {
      key: "manage",
      header: "",
      className: "w-10",
      render: (item) => (
        <Link
          href={`/admin/lessons/${item.id}`}
          aria-label="Inhalte verwalten"
          className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--admin-text-secondary)] transition hover:bg-white/5 hover:text-[var(--admin-primary)]"
        >
          <Settings2 size={15} />
        </Link>
      ),
    },
  ];

  return (
    <div>
      <AdminPageHeader
        title="Lessons"
        description="Lektionen innerhalb eines Moduls. Klicke auf eine Lektion, um Inhalte (Video, Vokabeln, Grammatik, ...) zu verwalten."
        action={
          <AdminButton onClick={openCreate} disabled={!modules || modules.length === 0}>
            <Plus size={16} />
            Neue Lektion
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
          modules && modules.length === 0
            ? "Lege zuerst ein Modul an, bevor du Lektionen erstellst."
            : "Noch keine Lektionen angelegt."
        }
      />

      <FormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={editing ? "Lektion bearbeiten" : "Neue Lektion"}
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
              <AdminLabel>Modul</AdminLabel>
              <AdminSelect
                value={form.module_id}
                onChange={(e) => setForm({ ...form, module_id: e.target.value })}
              >
                {(modules ?? []).map((module) => (
                  <option key={module.id} value={module.id}>
                    {module.title}
                  </option>
                ))}
              </AdminSelect>
            </div>
          )}

          <div>
            <AdminLabel>Lektionsnummer</AdminLabel>
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
              placeholder="Sich vorstellen"
            />
          </div>

          <div>
            <AdminLabel>Dauer (Minuten)</AdminLabel>
            <AdminInput
              type="number"
              value={form.duration}
              onChange={(e) => setForm({ ...form, duration: Number(e.target.value) })}
            />
          </div>

          <label className="flex cursor-pointer items-center gap-2.5">
            <AdminCheckbox
              checked={form.is_free}
              onCheckedChange={(checked) => setForm({ ...form, is_free: checked })}
            />
            <span className="text-sm text-[var(--admin-text-secondary)]">Kostenlos zugänglich</span>
          </label>
        </div>
      </FormDialog>

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(open) => !open && setDeleting(null)}
        title="Lektion löschen"
        description={`"${deleting?.title}" wird dauerhaft gelöscht, inklusive aller Inhalte (Video, Vokabeln, Übungen, ...).`}
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
