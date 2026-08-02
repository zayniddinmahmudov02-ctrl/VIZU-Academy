"use client";

import { useState } from "react";
import Link from "next/link";
import { Award, BarChart3, ClipboardList, Layers3, Plus } from "lucide-react";

import {
  AdminButton,
  AdminCard,
  AdminCheckbox,
  AdminInput,
  AdminLabel,
  AdminPageHeader,
} from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FormDialog from "@/components/admin/form-dialog";
import { useCrudList, useCrudMutations } from "@/features/admin/hooks/use-crud";
import { useQuery } from "@tanstack/react-query";
import { getDashboardSummary } from "@/features/admin/services/mock-exam-service";
import { mockExamProvidersApi } from "@/features/admin/services/mock-exam-service";
import type { CertificationProvider } from "@/features/admin/types/mock-exam.types";

const EMPTY_FORM = {
  name: "",
  code: "",
  description: "",
  color: "#5b5bf8",
  is_active: true,
  sort_order: 1,
  logo_url: null as string | null,
};

function SummaryCard({ label, value, icon: Icon }: { label: string; value: number; icon: typeof Award }) {
  return (
    <AdminCard className="flex items-center gap-4">
      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[var(--admin-primary)]/15 text-[var(--admin-primary)]">
        <Icon size={20} />
      </div>
      <div>
        <p className="text-2xl font-bold text-[var(--admin-text-primary)]">{value}</p>
        <p className="text-xs text-[var(--admin-text-muted)]">{label}</p>
      </div>
    </AdminCard>
  );
}

export default function MockExamCertificatesPage() {
  const { data: providers, isLoading } = useCrudList("mock-exam-providers", mockExamProvidersApi);
  const { create, update, remove } = useCrudMutations("mock-exam-providers", mockExamProvidersApi);
  const { data: summary } = useQuery({ queryKey: ["mock-exam-dashboard-summary"], queryFn: getDashboardSummary });

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<CertificationProvider | null>(null);
  const [deleting, setDeleting] = useState<CertificationProvider | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  function openCreate() {
    setEditing(null);
    setForm(EMPTY_FORM);
    setError(null);
    setDialogOpen(true);
  }

  function openEdit(item: CertificationProvider) {
    setEditing(item);
    setForm({
      name: item.name,
      code: item.code,
      description: item.description ?? "",
      color: item.color ?? "#5b5bf8",
      is_active: item.is_active,
      sort_order: item.sort_order,
      logo_url: item.logo_url,
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
        await create.mutateAsync(form);
      }
      setDialogOpen(false);
    } catch {
      setError("Speichern fehlgeschlagen. Prüfe, ob der Code bereits vergeben ist.");
    }
  }

  const columns: DataTableColumn<CertificationProvider>[] = [
    {
      key: "name",
      header: "Zertifikat",
      render: (item) => (
        <Link
          href={`/admin/mock-exams/${item.id}`}
          className="flex items-center gap-2.5 font-medium text-[var(--admin-text-primary)] hover:text-[var(--admin-primary)]"
        >
          <span
            className="h-2.5 w-2.5 shrink-0 rounded-full"
            style={{ backgroundColor: item.color ?? "#5b5bf8" }}
          />
          {item.name}
        </Link>
      ),
    },
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
    {
      key: "open",
      header: "",
      render: (item) => (
        <Link
          href={`/admin/mock-exams/${item.id}`}
          className="text-xs font-medium text-[var(--admin-primary)] hover:underline"
        >
          Levels öffnen →
        </Link>
      ),
    },
  ];

  return (
    <div>
      <AdminPageHeader
        title="Mock Test Management"
        description="Zertifikate → Levels → Modelltests → Kompetenzen → Teile → Fragen."
        action={
          <div className="flex items-center gap-2">
            <Link href="/admin/mock-exams/question-bank">
              <AdminButton variant="secondary">
                <Layers3 size={16} />
                Question Bank
              </AdminButton>
            </Link>
            <Link href="/admin/mock-exams/results">
              <AdminButton variant="secondary">
                <ClipboardList size={16} />
                Ergebnisse
              </AdminButton>
            </Link>
            <Link href="/admin/mock-exams/analytics">
              <AdminButton variant="secondary">
                <BarChart3 size={16} />
                Analytics
              </AdminButton>
            </Link>
            <AdminButton onClick={openCreate}>
              <Plus size={16} />
              Neues Zertifikat
            </AdminButton>
          </div>
        }
      />

      {summary && (
        <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <SummaryCard label="Zertifikate" value={summary.certificates} icon={Award} />
          <SummaryCard label="Levels" value={summary.levels} icon={Layers3} />
          <SummaryCard label="Modelltests" value={summary.model_tests} icon={ClipboardList} />
          <SummaryCard label="Fragen" value={summary.questions} icon={BarChart3} />
        </div>
      )}

      <DataTable
        columns={columns}
        data={providers}
        isLoading={isLoading}
        getRowId={(item) => item.id}
        onEdit={openEdit}
        onDelete={setDeleting}
        emptyMessage="Noch keine Zertifikate angelegt (z. B. Goethe-Institut, TELC, ÖSD)."
      />

      <FormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={editing ? "Zertifikat bearbeiten" : "Neues Zertifikat"}
        footer={
          <>
            <AdminButton variant="ghost" onClick={() => setDialogOpen(false)}>
              Abbrechen
            </AdminButton>
            <AdminButton
              onClick={handleSubmit}
              disabled={create.isPending || update.isPending || !form.name || !form.code}
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
              placeholder="Goethe-Institut"
            />
          </div>

          <div>
            <AdminLabel>Code</AdminLabel>
            <AdminInput
              value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })}
              placeholder="GOETHE"
            />
          </div>

          <div>
            <AdminLabel>Beschreibung</AdminLabel>
            <AdminInput
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Offizielle deutsche Sprachprüfung"
            />
          </div>

          <div className="flex items-center gap-3">
            <div className="flex-1">
              <AdminLabel>Farbe</AdminLabel>
              <input
                type="color"
                value={form.color}
                onChange={(e) => setForm({ ...form, color: e.target.value })}
                className="h-10 w-full rounded-lg bg-[var(--admin-card)] ring-1 ring-[var(--admin-border-strong)]"
              />
            </div>
            <div className="flex-1">
              <AdminLabel>Reihenfolge</AdminLabel>
              <AdminInput
                type="number"
                value={form.sort_order}
                onChange={(e) => setForm({ ...form, sort_order: Number(e.target.value) })}
              />
            </div>
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
        title="Zertifikat löschen"
        description={`"${deleting?.name}" wird dauerhaft gelöscht, inklusive aller Levels, Modelltests, Kompetenzen, Teile und Fragen.`}
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
