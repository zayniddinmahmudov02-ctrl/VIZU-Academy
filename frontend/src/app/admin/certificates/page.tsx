"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Plus } from "lucide-react";

import {
  AdminButton,
  AdminCheckbox,
  AdminInput,
  AdminLabel,
  AdminPageHeader,
  AdminSelect,
} from "@/components/admin/admin-ui";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FormDialog from "@/components/admin/form-dialog";
import Avatar from "@/components/ui/avatar";
import { useCrudMutations } from "@/features/admin/hooks/use-crud";
import { certificatesApi, listCertificateHolders } from "@/features/admin/services/certificates-service";
import type { CertificateHolder, CertificateSource } from "@/features/admin/types/certificate.types";

const PAGE_SIZE = 50;

const SOURCE_OPTIONS: { value: CertificateSource; label: string }[] = [
  { value: "COURSE", label: "Kursabschluss" },
  { value: "VORBEREITUNG", label: "Vorbereitung" },
  { value: "VIZU_MOCK", label: "VIZU-MOCK" },
];

const EMPTY_FORM = {
  user_id: "",
  course_id: "",
  source: "COURSE" as CertificateSource,
  level: "",
  score: 0,
  lesen_score: 0,
  hoeren_score: 0,
  schreiben_score: 0,
  sprechen_score: 0,
  is_valid: true,
};

function displayName(holder: CertificateHolder): string {
  return [holder.first_name, holder.last_name].filter(Boolean).join(" ") || holder.username || holder.email || "—";
}

export default function CertificatesPage() {
  const [page, setPage] = useState(1);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["admin-certificate-holders", page],
    queryFn: () => listCertificateHolders({ page, page_size: PAGE_SIZE }),
  });

  const { create } = useCrudMutations("certificates", certificatesApi);

  async function handleSubmit() {
    setError(null);
    try {
      await create.mutateAsync({
        ...form,
        course_id: form.source === "COURSE" ? form.course_id : null,
      });
      setDialogOpen(false);
      setForm(EMPTY_FORM);
    } catch {
      setError("Zertifikat konnte nicht ausgestellt werden. Prüfe, ob Nutzer- und Kurs-ID korrekt sind.");
    }
  }

  const columns: DataTableColumn<CertificateHolder>[] = [
    {
      key: "avatar",
      header: "",
      className: "w-12",
      render: (holder) => <Avatar src={holder.profile_image ?? undefined} name={displayName(holder)} size={32} />,
    },
    {
      key: "user",
      header: "Nutzer",
      render: (holder) => (
        <Link
          href={`/admin/certificates/${holder.user_id}`}
          className="font-medium text-[var(--admin-text-primary)] hover:text-[var(--admin-primary)]"
        >
          {displayName(holder)}
        </Link>
      ),
    },
    { key: "count", header: "Zertifikate gesamt", render: (holder) => holder.certificate_count },
    {
      key: "last",
      header: "Letztes Zertifikat",
      render: (holder) =>
        holder.last_certificate_at ? new Date(holder.last_certificate_at).toLocaleDateString("de-DE") : "—",
    },
    {
      key: "open",
      header: "",
      render: (holder) => (
        <Link
          href={`/admin/certificates/${holder.user_id}`}
          className="text-xs font-medium text-[var(--admin-primary)] hover:underline"
        >
          Profil öffnen →
        </Link>
      ),
    },
  ];

  return (
    <div>
      <AdminPageHeader
        title="Certificate"
        description="Nutzer mit Zertifikaten, sortiert nach Anzahl."
        action={
          <AdminButton onClick={() => setDialogOpen(true)}>
            <Plus size={16} />
            Zertifikat ausstellen
          </AdminButton>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items}
        isLoading={isLoading}
        getRowId={(holder) => holder.user_id}
        emptyMessage="Noch keine Zertifikate ausgestellt."
      />

      {data && data.total_pages > 1 && (
        <div className="mt-4 flex items-center justify-between text-sm text-[var(--admin-text-secondary)]">
          <span>
            Seite {data.page} von {data.total_pages} ({data.total} Nutzer mit Zertifikaten)
          </span>
          <div className="flex gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--admin-card)] ring-1 ring-[var(--admin-border-strong)] disabled:opacity-40"
            >
              <ChevronLeft size={14} />
            </button>
            <button
              disabled={page >= data.total_pages}
              onClick={() => setPage((p) => p + 1)}
              className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--admin-card)] ring-1 ring-[var(--admin-border-strong)] disabled:opacity-40"
            >
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      )}

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
              disabled={
                create.isPending ||
                !form.user_id ||
                !form.level ||
                (form.source === "COURSE" && !form.course_id)
              }
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
              <AdminLabel>Quelle</AdminLabel>
              <AdminSelect
                value={form.source}
                onChange={(e) => setForm({ ...form, source: e.target.value as CertificateSource })}
              >
                {SOURCE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </AdminSelect>
            </div>
          </div>

          {form.source === "COURSE" && (
            <div>
              <AdminLabel>Kurs-ID</AdminLabel>
              <AdminInput
                value={form.course_id}
                onChange={(e) => setForm({ ...form, course_id: e.target.value })}
                placeholder="UUID des Kurses"
              />
            </div>
          )}

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
    </div>
  );
}
