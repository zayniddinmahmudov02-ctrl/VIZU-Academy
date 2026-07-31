"use client";

import { useState } from "react";
import { Award } from "lucide-react";

import { useAdminCertificates } from "../hooks/use-admin-certificates";
import AdminModal from "../components/admin-modal";
import CertificatesTable from "../components/certificates-table";

const LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"];

export default function AdminCertificatesPage() {
  const certificates = useAdminCertificates();
  const [createOpen, setCreateOpen] = useState(false);

  const [userId, setUserId] = useState("");
  const [courseId, setCourseId] = useState("");
  const [level, setLevel] = useState("A1");
  const [lesenScore, setLesenScore] = useState("0");
  const [hoerenScore, setHoerenScore] = useState("0");
  const [schreibenScore, setSchreibenScore] = useState("0");
  const [sprechenScore, setSprechenScore] = useState("0");

  function resetForm() {
    setUserId("");
    setCourseId("");
    setLevel("A1");
    setLesenScore("0");
    setHoerenScore("0");
    setSchreibenScore("0");
    setSprechenScore("0");
  }

  async function handleIssue() {
    if (!userId.trim() || !courseId.trim()) return;

    try {
      await certificates.issue({
        userId: userId.trim(),
        courseId: courseId.trim(),
        level,
        lesenScore: Number(lesenScore),
        hoerenScore: Number(hoerenScore),
        schreibenScore: Number(schreibenScore),
        sprechenScore: Number(sprechenScore),
      });
      setCreateOpen(false);
      resetForm();
    } catch {
      // issueError is surfaced in the modal below.
    }
  }

  async function handleUpdate(certificateId: string, data: Parameters<typeof certificates.update>[1]) {
    await certificates.update(certificateId, data);
  }

  function handleRevoke(certificateId: string) {
    certificates.revoke(certificateId);
  }

  return (
    <div className="space-y-6">
      <div className="admin-glass flex flex-wrap items-center justify-between gap-4 rounded-2xl p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--admin-primary)] to-[var(--admin-secondary)] text-white">
            <Award size={20} />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">Certificates</h1>
            <p className="text-xs text-[var(--admin-text-muted)]">{certificates.data?.length ?? 0} certificates</p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setCreateOpen(true)}
          className="rounded-xl bg-[var(--admin-primary)] px-4 py-2.5 text-xs font-semibold text-white"
        >
          + Issue Certificate
        </button>
      </div>

      <CertificatesTable
        certificates={certificates.data ?? []}
        loading={certificates.loading}
        onUpdate={handleUpdate}
        onRevoke={handleRevoke}
      />

      <AdminModal
        open={createOpen}
        onOpenChange={(open) => {
          setCreateOpen(open);
          if (!open) resetForm();
        }}
        title="Issue Certificate"
      >
        <div className="space-y-3">
          <input
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="User ID"
            className="w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
          />
          <input
            value={courseId}
            onChange={(e) => setCourseId(e.target.value)}
            placeholder="Course ID"
            className="w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
          />
          <select
            value={level}
            onChange={(e) => setLevel(e.target.value)}
            className="w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
          >
            {LEVELS.map((lvl) => (
              <option key={lvl} value={lvl} className="bg-[#111827]">
                {lvl}
              </option>
            ))}
          </select>

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

          {certificates.issueError && <p className="text-xs text-[#ef4444]">{certificates.issueError}</p>}

          <button
            type="button"
            onClick={handleIssue}
            disabled={!userId.trim() || !courseId.trim() || certificates.issuing}
            className="w-full rounded-xl bg-[var(--admin-primary)] py-2.5 text-sm font-semibold text-white disabled:opacity-40"
          >
            {certificates.issuing ? "Issuing…" : "Issue Certificate"}
          </button>
        </div>
      </AdminModal>
    </div>
  );
}
