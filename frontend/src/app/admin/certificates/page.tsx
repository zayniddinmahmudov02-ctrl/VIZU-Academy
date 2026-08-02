"use client";

import { useState } from "react";
import { Plus } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminInput, AdminLabel, AdminPageHeader } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FormDialog from "@/components/admin/form-dialog";
import { useCrudList, useCrudMutations } from "@/features/admin/hooks/use-crud";
import { certificatesApi } from "@/features/admin/services/certificates-service";
import type { Certificate } from "@/features/admin/types/certificate.types";

const EMPTY_FORM = {
  user_id: "",
  course_id: "",
  level: "",
  score: 0,
  lesen_score: 0,
  hoeren_score: 0,
  schreiben_score: 0,
  sprechen_score: 0,
  is_valid: true,
};

export default function CertificatesPage() {
  const { data, isLoading } = useCrudList("certificates", certificatesApi);
  const { create, remove } = useCrudMutations("certificates", certificatesApi);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState<Certificate | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  function openCreate() {
    setForm(EMPTY_FORM);
    setError(null);
    setDialogOpen(true);
  }

  async function handleSubmit() {
    setError(null);
    try {
      await create.mutateAsync(form);
      setDialogOpen(false);
    } catch {
      setError("Zertifikat konnte nicht ausgestellt werden. Prüfe, ob Nutzer- und Kurs-ID korrekt sind.");
    }
  }

  const columns: DataTableColumn<Certificate>[] = [
    { key: "number", header: "Nummer", render: (item) => item.certificate_number },
    { key: "level", header: "Level", render: (item) => item.level },
    { key: "score", header: "Punktzahl", render: (item) => `${item.score}%` },
    {
      key: "is_valid",
      header: "Status",
      render: (item) => (
        <span
          className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
            item.is_valid
              ? "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]"
              : "bg-[var(--admin-danger)]/15 text-[var(--admin-danger)]"
          }`}
        >
          {item.is_valid ? "Gültig" : "Widerrufen"}
        </span>
      ),
    },
    {
      key: "issued_at",
      header: "Ausgestellt",
      render: (item) => new Date(item.issued_at).toLocaleDateString("de-DE"),
    },
  ];

  return (
    <div>
      <AdminPageHeader
        title="Certificates"
        description="Ausgestellte Zertifikate verwalten und widerrufen."
        action={
          <AdminButton onClick={openCreate}>
            <Plus size={16} />
            Zertifikat ausstellen
          </AdminButton>
        }
      />

      <DataTable
        columns={columns}
        data={data}
        isLoading={isLoading}
        getRowId={(item) => item.id}
        onDelete={setDeleting}
        emptyMessage="Noch keine Zertifikate ausgestellt."
      />

      <FormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title="Zertifikat manuell ausstellen"
        description="Zertifikatsnummer und Verifizierungscode werden automatisch generiert."
        size="lg"
        footer={
          <>
            <AdminButton variant="ghost" onClick={() => setDialogOpen(false)}>
              Abbrechen
            </AdminButton>
            <AdminButton
              onClick={handleSubmit}
              disabled={create.isPending || !form.user_id || !form.course_id || !form.level}
            >
              {create.isPending ? "Wird ausgestellt..." : "Ausstellen"}
            </AdminButton>
          </>
        }
      >
        <div className="space-y-4">
          {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <AdminLabel>Nutzer-ID</AdminLabel>
              <AdminInput
                value={form.user_id}
                onChange={(e) => setForm({ ...form, user_id: e.target.value })}
                placeholder="UUID des Nutzers"
              />
            </div>
            <div>
              <AdminLabel>Kurs-ID</AdminLabel>
              <AdminInput
                value={form.course_id}
                onChange={(e) => setForm({ ...form, course_id: e.target.value })}
                placeholder="UUID des Kurses"
              />
            </div>
          </div>

          <div>
            <AdminLabel>Level</AdminLabel>
            <AdminInput
              value={form.level}
              onChange={(e) => setForm({ ...form, level: e.target.value })}
              placeholder="B1"
            />
          </div>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div>
              <AdminLabel>Gesamt %</AdminLabel>
              <AdminInput
                type="number"
                value={form.score}
                onChange={(e) => setForm({ ...form, score: Number(e.target.value) })}
              />
            </div>
            <div>
              <AdminLabel>Lesen</AdminLabel>
              <AdminInput
                type="number"
                value={form.lesen_score}
                onChange={(e) => setForm({ ...form, lesen_score: Number(e.target.value) })}
              />
            </div>
            <div>
              <AdminLabel>Hören</AdminLabel>
              <AdminInput
                type="number"
                value={form.hoeren_score}
                onChange={(e) => setForm({ ...form, hoeren_score: Number(e.target.value) })}
              />
            </div>
            <div>
              <AdminLabel>Schreiben</AdminLabel>
              <AdminInput
                type="number"
                value={form.schreiben_score}
                onChange={(e) => setForm({ ...form, schreiben_score: Number(e.target.value) })}
              />
            </div>
          </div>

          <label className="flex cursor-pointer items-center gap-2.5">
            <AdminCheckbox
              checked={form.is_valid}
              onCheckedChange={(checked) => setForm({ ...form, is_valid: checked })}
            />
            <span className="text-sm text-[var(--admin-text-secondary)]">Gültig</span>
          </label>
        </div>
      </FormDialog>

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(open) => !open && setDeleting(null)}
        title="Zertifikat widerrufen"
        description={`Zertifikat "${deleting?.certificate_number}" wird dauerhaft gelöscht.`}
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
