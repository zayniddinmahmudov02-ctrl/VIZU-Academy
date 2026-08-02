"use client";

import { useMemo, useState } from "react";
import { Plus } from "lucide-react";

import {
  AdminButton,
  AdminCard,
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
import { examProvidersApi, examsApi } from "@/features/admin/services/exam-service";
import type { Exam } from "@/features/admin/types/content.types";

const EMPTY_FORM = { provider_id: "", level: "", title: "", duration: 180, is_active: true };

export default function MockExamsPage() {
  const { data: providers } = useCrudList("exam-providers", examProvidersApi);
  const providerMutations = useCrudMutations("exam-providers", examProvidersApi);

  const { data, isLoading } = useCrudList("exams", examsApi);
  const { create, update, remove } = useCrudMutations("exams", examsApi);

  const providerMap = useMemo(
    () => new Map((providers ?? []).map((p) => [p.id, p.name])),
    [providers],
  );

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Exam | null>(null);
  const [deleting, setDeleting] = useState<Exam | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  const [newProviderName, setNewProviderName] = useState("");
  const [newProviderCode, setNewProviderCode] = useState("");

  function openCreate() {
    setEditing(null);
    setForm({ ...EMPTY_FORM, provider_id: providers?.[0]?.id ?? "" });
    setError(null);
    setDialogOpen(true);
  }

  function openEdit(item: Exam) {
    setEditing(item);
    setForm({
      provider_id: item.provider_id,
      level: item.level,
      title: item.title,
      duration: item.duration,
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
        const { provider_id: _providerId, level: _level, ...updateData } = form;
        await update.mutateAsync({ id: editing.id, data: updateData });
      } else {
        await create.mutateAsync(form);
      }
      setDialogOpen(false);
    } catch {
      setError("Speichern fehlgeschlagen.");
    }
  }

  async function handleAddProvider() {
    if (!newProviderName.trim() || !newProviderCode.trim()) return;
    await providerMutations.create.mutateAsync({
      name: newProviderName.trim(),
      code: newProviderCode.trim(),
    });
    setNewProviderName("");
    setNewProviderCode("");
  }

  const columns: DataTableColumn<Exam>[] = [
    { key: "title", header: "Titel", render: (item) => item.title },
    { key: "level", header: "Level", render: (item) => item.level },
    { key: "provider", header: "Anbieter", render: (item) => providerMap.get(item.provider_id) ?? "—" },
    { key: "duration", header: "Dauer (Min.)", render: (item) => item.duration },
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
        title="Mock Exams"
        description="Prüfungssimulationen je Anbieter und Level."
        action={
          <AdminButton onClick={openCreate} disabled={!providers || providers.length === 0}>
            <Plus size={16} />
            Neue Prüfung
          </AdminButton>
        }
      />

      <AdminCard className="mb-6">
        <h3 className="mb-3 text-sm font-semibold text-[var(--admin-text-primary)]">Prüfungsanbieter</h3>
        <div className="mb-3 flex flex-wrap gap-2">
          {(providers ?? []).map((p) => (
            <span
              key={p.id}
              className="rounded-full bg-white/5 px-3 py-1.5 text-xs font-medium text-[var(--admin-text-secondary)]"
            >
              {p.name} <span className="text-[var(--admin-text-muted)]">({p.code})</span>
            </span>
          ))}
          {(!providers || providers.length === 0) && (
            <p className="text-xs text-[var(--admin-text-muted)]">Noch keine Anbieter angelegt.</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <AdminInput
            value={newProviderName}
            onChange={(e) => setNewProviderName(e.target.value)}
            placeholder="Name (z. B. Goethe-Institut)"
            className="h-9 flex-1 text-sm"
          />
          <AdminInput
            value={newProviderCode}
            onChange={(e) => setNewProviderCode(e.target.value)}
            placeholder="Code (z. B. GOETHE)"
            className="h-9 w-40 text-sm"
          />
          <AdminButton type="button" variant="secondary" size="sm" onClick={handleAddProvider}>
            <Plus size={14} />
          </AdminButton>
        </div>
      </AdminCard>

      <DataTable
        columns={columns}
        data={data}
        isLoading={isLoading}
        getRowId={(item) => item.id}
        onEdit={openEdit}
        onDelete={setDeleting}
        emptyMessage={
          providers && providers.length === 0
            ? "Lege zuerst einen Prüfungsanbieter an."
            : "Noch keine Prüfungen angelegt."
        }
      />

      <FormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={editing ? "Prüfung bearbeiten" : "Neue Prüfung"}
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

          {!editing && (
            <div>
              <AdminLabel>Anbieter</AdminLabel>
              <AdminSelect
                value={form.provider_id}
                onChange={(e) => setForm({ ...form, provider_id: e.target.value })}
              >
                {(providers ?? []).map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </AdminSelect>
            </div>
          )}

          <div>
            <AdminLabel>Titel</AdminLabel>
            <AdminInput
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="B1 Modellprüfung 1"
            />
          </div>

          <div>
            <AdminLabel>Level</AdminLabel>
            <AdminInput
              value={form.level}
              onChange={(e) => setForm({ ...form, level: e.target.value })}
              placeholder="B1"
              disabled={!!editing}
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
        title="Prüfung löschen"
        description={`"${deleting?.title}" wird dauerhaft gelöscht.`}
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
