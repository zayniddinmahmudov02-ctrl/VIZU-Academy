"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Plus } from "lucide-react";

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
import { mockExamLevelsApi, mockExamProvidersApi } from "@/features/admin/services/mock-exam-service";
import type { MockExamLevel } from "@/features/admin/types/mock-exam.types";

const EMPTY_FORM = { level: "", title: "", description: "", sort_order: 1, is_active: true };

export default function MockExamLevelsPage() {
  const { providerId } = useParams<{ providerId: string }>();

  const { data: providers } = useCrudList("mock-exam-providers", mockExamProvidersApi);
  const provider = providers?.find((p) => p.id === providerId);

  const { data: levels, isLoading } = useCrudList("mock-exam-levels", mockExamLevelsApi, {
    provider_id: providerId,
  });
  const { create, update, remove } = useCrudMutations("mock-exam-levels", mockExamLevelsApi);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<MockExamLevel | null>(null);
  const [deleting, setDeleting] = useState<MockExamLevel | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  function openCreate() {
    setEditing(null);
    setForm(EMPTY_FORM);
    setError(null);
    setDialogOpen(true);
  }

  function openEdit(item: MockExamLevel) {
    setEditing(item);
    setForm({
      level: item.level,
      title: item.title ?? "",
      description: item.description ?? "",
      sort_order: item.sort_order,
      is_active: item.is_active,
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
        await create.mutateAsync({ ...form, provider_id: providerId });
      }
      setDialogOpen(false);
    } catch {
      setError("Speichern fehlgeschlagen.");
    }
  }

  const columns: DataTableColumn<MockExamLevel>[] = [
    { key: "level", header: "Level", render: (item) => item.level },
    { key: "title", header: "Titel", render: (item) => item.title ?? "—" },
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
    {
      key: "open",
      header: "",
      render: (item) => (
        <Link
          href={`/admin/mock-exams/${providerId}/${item.id}`}
          className="text-xs font-medium text-[var(--admin-primary)] hover:underline"
        >
          Modelltests öffnen →
        </Link>
      ),
    },
  ];

  return (
    <div>
      <Link
        href="/admin/mock-exams"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--admin-text-muted)] hover:text-[var(--admin-text-primary)]"
      >
        <ArrowLeft size={14} />
        Zertifikate
      </Link>

      <AdminPageHeader
        title={provider ? `${provider.name} — Levels` : "Levels"}
        description="A1–C2 Niveaustufen mit beliebig vielen Modelltests."
        action={
          <AdminButton onClick={openCreate}>
            <Plus size={16} />
            Neues Level
          </AdminButton>
        }
      />

      <DataTable
        columns={columns}
        data={levels}
        isLoading={isLoading}
        getRowId={(item) => item.id}
        onEdit={openEdit}
        onDelete={setDeleting}
        emptyMessage="Noch keine Levels angelegt (z. B. A1, A2, B1, B2, C1, C2)."
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
              disabled={create.isPending || update.isPending || !form.level}
            >
              {create.isPending || update.isPending ? "Wird gespeichert..." : "Speichern"}
            </AdminButton>
          </>
        }
      >
        <div className="space-y-4">
          {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}

          <div>
            <AdminLabel>Level</AdminLabel>
            <AdminInput
              value={form.level}
              onChange={(e) => setForm({ ...form, level: e.target.value.toUpperCase() })}
              placeholder="B2"
            />
          </div>

          <div>
            <AdminLabel>Titel (optional)</AdminLabel>
            <AdminInput
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="B2 Mittelstufe"
            />
          </div>

          <div>
            <AdminLabel>Reihenfolge</AdminLabel>
            <AdminInput
              type="number"
              value={form.sort_order}
              onChange={(e) => setForm({ ...form, sort_order: Number(e.target.value) })}
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
        description={`"${deleting?.level}" wird dauerhaft gelöscht, inklusive aller Modelltests.`}
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
