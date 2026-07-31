"use client";

import { useState } from "react";
import { isAxiosError } from "axios";
import { FileText, Pencil, Ban } from "lucide-react";

import { API_URL } from "@/constants/api";
import AdminModal from "./admin-modal";
import DataTable, { type DataTableColumn } from "./data-table";
import { Badge } from "./badges";
import type { AdminCertificateItem, UpdateCertificateInput } from "../types/certificate";

interface Props {
  certificates: AdminCertificateItem[];
  loading: boolean;
  onUpdate: (certificateId: string, data: UpdateCertificateInput) => Promise<void>;
  onRevoke: (certificateId: string) => void;
}

function formatDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export default function CertificatesTable({ certificates, loading, onUpdate, onRevoke }: Props) {
  const [editTarget, setEditTarget] = useState<AdminCertificateItem | null>(null);
  const [lesenScore, setLesenScore] = useState("0");
  const [hoerenScore, setHoerenScore] = useState("0");
  const [schreibenScore, setSchreibenScore] = useState("0");
  const [sprechenScore, setSprechenScore] = useState("0");
  const [isValid, setIsValid] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function openEdit(certificate: AdminCertificateItem) {
    setEditTarget(certificate);
    setLesenScore(String(certificate.lesenScore));
    setHoerenScore(String(certificate.hoerenScore));
    setSchreibenScore(String(certificate.schreibenScore));
    setSprechenScore(String(certificate.sprechenScore));
    setIsValid(certificate.isValid);
    setError(null);
  }

  function closeEdit(open: boolean) {
    if (!open) {
      setEditTarget(null);
      setError(null);
    }
  }

  async function handleSave() {
    if (!editTarget) return;
    setSaving(true);
    setError(null);

    const lesen = Number(lesenScore);
    const hoeren = Number(hoerenScore);
    const schreiben = Number(schreibenScore);
    const sprechen = Number(sprechenScore);

    try {
      await onUpdate(editTarget.id, {
        lesenScore: lesen,
        hoerenScore: hoeren,
        schreibenScore: schreiben,
        sprechenScore: sprechen,
        score: lesen + hoeren + schreiben + sprechen,
        isValid,
      });
      setEditTarget(null);
    } catch (err) {
      const message = isAxiosError<{ message?: string }>(err)
        ? err.response?.data?.message
        : undefined;
      setError(message ?? "Failed to update certificate.");
    } finally {
      setSaving(false);
    }
  }

  function handleRevoke(certificate: AdminCertificateItem) {
    if (!window.confirm(`Revoke certificate ${certificate.certificateNumber}? This marks it invalid.`)) return;
    onRevoke(certificate.id);
  }

  const columns: DataTableColumn<AdminCertificateItem>[] = [
    {
      key: "certificate_number",
      label: "Certificate #",
      render: (certificate) => (
        <div>
          <p className="font-medium text-white">{certificate.certificateNumber}</p>
          <p className="font-mono text-xs text-[var(--admin-text-muted)]">{certificate.verificationCode}</p>
        </div>
      ),
    },
    {
      key: "holder",
      label: "Holder",
      render: (certificate) => (
        <span className="font-mono text-xs text-[var(--admin-text-secondary)]">{certificate.userId}</span>
      ),
    },
    {
      key: "course_level",
      label: "Course / Level",
      render: (certificate) => (
        <div>
          <p className="font-mono text-xs text-[var(--admin-text-secondary)]">{certificate.courseId}</p>
          <Badge label={certificate.level} tone="primary" />
        </div>
      ),
    },
    {
      key: "score",
      label: "Score",
      render: (certificate) => (
        <span className="text-[var(--admin-text-secondary)]">{certificate.score}</span>
      ),
    },
    {
      key: "issued_at",
      label: "Issued",
      render: (certificate) => (
        <span className="text-[var(--admin-text-secondary)]">{formatDate(certificate.issuedAt)}</span>
      ),
    },
    {
      key: "status",
      label: "Status",
      render: (certificate) => (
        <Badge label={certificate.isValid ? "Valid" : "Revoked"} tone={certificate.isValid ? "success" : "danger"} />
      ),
    },
    {
      key: "actions",
      label: "Actions",
      render: (certificate) => (
        <div className="flex items-center gap-2">
          {certificate.pdfUrl && (
            <a
              href={`${API_URL}/api/v1/certificates/download/${certificate.id}`}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="View certificate PDF"
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--admin-border)] text-[var(--admin-text-secondary)] transition-colors hover:bg-white/5 hover:text-white"
            >
              <FileText size={14} />
            </a>
          )}

          <button
            type="button"
            onClick={() => openEdit(certificate)}
            aria-label="Edit certificate"
            className="rounded-lg border border-[var(--admin-border)] p-1.5 text-[var(--admin-text-secondary)] transition-colors hover:bg-white/5 hover:text-white"
          >
            <Pencil size={14} />
          </button>

          <button
            type="button"
            onClick={() => handleRevoke(certificate)}
            disabled={!certificate.isValid}
            aria-label="Revoke certificate"
            className="rounded-lg border border-[var(--admin-border)] p-1.5 text-[var(--admin-text-secondary)] transition-colors hover:border-[var(--admin-danger)]/40 hover:text-[var(--admin-danger)] disabled:opacity-40"
          >
            <Ban size={14} />
          </button>
        </div>
      ),
    },
  ];

  return (
    <>
      <DataTable
        columns={columns}
        rows={certificates}
        getRowKey={(certificate) => certificate.id}
        loading={loading}
        emptyLabel="No certificates issued yet."
        minWidth="900px"
      />

      <AdminModal open={editTarget !== null} onOpenChange={closeEdit} title="Edit Certificate">
        <div className="space-y-3">
          {editTarget && (
            <p className="text-xs text-[var(--admin-text-muted)]">
              {editTarget.certificateNumber} &middot; {editTarget.level}
            </p>
          )}

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="mb-1 block text-xs text-[var(--admin-text-muted)]">Lesen</label>
              <input
                type="number"
                value={lesenScore}
                onChange={(e) => setLesenScore(e.target.value)}
                className="w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-[var(--admin-text-muted)]">Hören</label>
              <input
                type="number"
                value={hoerenScore}
                onChange={(e) => setHoerenScore(e.target.value)}
                className="w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-[var(--admin-text-muted)]">Schreiben</label>
              <input
                type="number"
                value={schreibenScore}
                onChange={(e) => setSchreibenScore(e.target.value)}
                className="w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-[var(--admin-text-muted)]">Sprechen</label>
              <input
                type="number"
                value={sprechenScore}
                onChange={(e) => setSprechenScore(e.target.value)}
                className="w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
              />
            </div>
          </div>

          <label className="flex items-center gap-2 text-sm text-[var(--admin-text-secondary)]">
            <input
              type="checkbox"
              checked={isValid}
              onChange={(e) => setIsValid(e.target.checked)}
              className="h-4 w-4 rounded border-[var(--admin-border)]"
            />
            Valid
          </label>

          {error && <p className="text-xs text-[#ef4444]">{error}</p>}

          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="w-full rounded-xl bg-[var(--admin-primary)] py-2.5 text-sm font-semibold text-white disabled:opacity-40"
          >
            {saving ? "Saving…" : "Save Changes"}
          </button>
        </div>
      </AdminModal>
    </>
  );
}
