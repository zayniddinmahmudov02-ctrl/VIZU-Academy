"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Plus } from "lucide-react";

import {
  AdminButton,
  AdminInput,
  AdminLabel,
  AdminPageHeader,
  AdminSelect,
} from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FormDialog from "@/components/admin/form-dialog";
import { useCrudList, useCrudMutations } from "@/features/admin/hooks/use-crud";
import { mockExamLevelsApi, mockExamModelTestsApi } from "@/features/admin/services/mock-exam-service";
import { MODEL_TEST_STATUSES, type ModelTest } from "@/features/admin/types/mock-exam.types";

const EMPTY_FORM = { title: "", description: "", status: "DRAFT" as const, sort_order: 1 };

const STATUS_STYLE: Record<string, string> = {
  DRAFT: "bg-white/5 text-[var(--admin-text-muted)]",
  PUBLISHED: "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]",
  ARCHIVED: "bg-[var(--admin-danger)]/15 text-[var(--admin-danger)]",
};

export default function MockExamModelTestsPage() {
  const { providerId, levelId } = useParams<{ providerId: string; levelId: string }>();

  const { data: levels } = useCrudList("mock-exam-levels", mockExamLevelsApi, { provider_id: providerId });
  const level = levels?.find((l) => l.id === levelId);

  const { data: modelTests, isLoading } = useCrudList("mock-exam-model-tests", mockExamModelTestsApi, {
    level_id: levelId,
  });
  const { create, update, remove } = useCrudMutations("mock-exam-model-tests", mockExamModelTestsApi);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<ModelTest | null>(null);
  const [deleting, setDeleting] = useState<ModelTest | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  function openCreate() {
    setEditing(null);
    setForm(EMPTY_FORM);
    setError(null);
    setDialogOpen(true);
  }

  function openEdit(item: ModelTest) {
    setEditing(item);
    setForm({
      title: item.title,
      description: item.description ?? "",
      status: item.status as "DRAFT",
      sort_order: item.sort_order,
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
        await create.mutateAsync({ ...form, level_id: levelId });
      }
      setDialogOpen(false);
    } catch {
      setError("Speichern fehlgeschlagen.");
    }
  }

  const columns: DataTableColumn<ModelTest>[] = [
    {
      key: "title",
      header: "Modelltest",
      render: (item) => (
        <Link
          href={`/admin/mock-exams/${providerId}/${levelId}/${item.id}`}
          className="font-medium text-[var(--admin-text-primary)] hover:text-[var(--admin-primary)]"
        >
          {item.title}
        </Link>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (item) => (
        <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${STATUS_STYLE[item.status]}`}>
          {item.status}
        </span>
      ),
    },
    {
      key: "open",
      header: "",
      render: (item) => (
        <Link
          href={`/admin/mock-exams/${providerId}/${levelId}/${item.id}`}
          className="text-xs font-medium text-[var(--admin-primary)] hover:underline"
        >
          Test bearbeiten →
        </Link>
      ),
    },
  ];

  return (
    <div>
      <Link
        href={`/admin/mock-exams/${providerId}`}
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--admin-text-muted)] hover:text-[var(--admin-text-primary)]"
      >
        <ArrowLeft size={14} />
        Levels
      </Link>

      <AdminPageHeader
        title={level ? `${level.level} — Modelltests` : "Modelltests"}
        description="Beliebig viele Modelltests je Level (z. B. Modelltest 1–5)."
        action={
          <AdminButton onClick={openCreate}>
            <Plus size={16} />
            Neuer Modelltest
          </AdminButton>
        }
      />

      <DataTable
        columns={columns}
        data={modelTests}
        isLoading={isLoading}
        getRowId={(item) => item.id}
        onEdit={openEdit}
        onDelete={setDeleting}
        emptyMessage="Noch keine Modelltests angelegt."
      />

      <FormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={editing ? "Modelltest bearbeiten" : "Neuer Modelltest"}
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

          <div>
            <AdminLabel>Titel</AdminLabel>
            <AdminInput
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="Modelltest 1"
            />
          </div>

          <div>
            <AdminLabel>Beschreibung</AdminLabel>
            <AdminInput
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Optional"
            />
          </div>

          <div>
            <AdminLabel>Status</AdminLabel>
            <AdminSelect
              value={form.status}
              onChange={(e) => setForm({ ...form, status: e.target.value as "DRAFT" })}
            >
              {MODEL_TEST_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </AdminSelect>
          </div>

          <div>
            <AdminLabel>Reihenfolge</AdminLabel>
            <AdminInput
              type="number"
              value={form.sort_order}
              onChange={(e) => setForm({ ...form, sort_order: Number(e.target.value) })}
            />
          </div>
        </div>
      </FormDialog>

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(open) => !open && setDeleting(null)}
        title="Modelltest löschen"
        description={`"${deleting?.title}" wird dauerhaft gelöscht, inklusive aller Kompetenzen, Teile und Fragen.`}
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
