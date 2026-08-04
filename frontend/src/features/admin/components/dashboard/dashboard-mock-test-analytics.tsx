"use client";

import { useState } from "react";
import Link from "next/link";
import { Award, ChevronDown, ChevronRight, FileCheck } from "lucide-react";

import { AdminCard } from "@/components/admin/admin-ui";
import type {
  CertificateMockAnalytics,
  MockTestSkillAnalytics,
} from "@/features/admin/types/enterprise-dashboard.types";

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-center">
      <p className="text-sm font-bold text-[var(--admin-text-primary)]">{value}</p>
      <p className="text-[10px] uppercase tracking-wide text-[var(--admin-text-muted)]">{label}</p>
    </div>
  );
}

function SkillBar({ label, percent }: { label: string; percent: number | null }) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-[11px]">
        <span className="text-[var(--admin-text-secondary)]">{label}</span>
        <span className="font-semibold text-[var(--admin-text-primary)]">{percent ?? "—"}{percent !== null && "%"}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-white/5">
        <div
          className="h-full rounded-full bg-[var(--admin-accent)] transition-all duration-500"
          style={{ width: `${percent ?? 0}%` }}
        />
      </div>
    </div>
  );
}

function ModelTestRow({ modelTest }: { modelTest: MockTestSkillAnalytics }) {
  return (
    <div className="rounded-lg bg-white/[0.02] p-3 ring-1 ring-[var(--admin-border)]">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm font-semibold text-[var(--admin-text-primary)]">{modelTest.title}</p>
        <div className="flex gap-4">
          <Stat label="Attempts" value={String(modelTest.attempts)} />
          <Stat label="Avg Score" value={`${modelTest.average_score_percent}%`} />
          <Stat label="Pass Rate" value={`${modelTest.pass_rate_percent}%`} />
          <Stat label="Fail Rate" value={`${modelTest.fail_rate_percent}%`} />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <SkillBar label="Reading" percent={modelTest.average_reading_percent} />
        <SkillBar label="Listening" percent={modelTest.average_listening_percent} />
        <SkillBar label="Writing" percent={modelTest.average_writing_percent} />
        <SkillBar label="Speaking" percent={modelTest.average_speaking_percent} />
      </div>
    </div>
  );
}

function CertificateSection({ certificate }: { certificate: CertificateMockAnalytics }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-xl bg-white/[0.02] ring-1 ring-[var(--admin-border)]">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-center gap-3 p-4 text-left"
      >
        {expanded ? (
          <ChevronDown size={16} className="shrink-0 text-[var(--admin-text-muted)]" />
        ) : (
          <ChevronRight size={16} className="shrink-0 text-[var(--admin-text-muted)]" />
        )}
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]">
          <Award size={16} />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-[var(--admin-text-primary)]">{certificate.name}</p>
          <p className="text-xs text-[var(--admin-text-muted)]">{certificate.code}</p>
        </div>
        <div className="flex gap-4">
          <Stat label="Attempts" value={String(certificate.total_attempts)} />
          <Stat label="Avg Score" value={`${certificate.average_score_percent}%`} />
          <Stat label="Pass Rate" value={`${certificate.pass_rate_percent}%`} />
        </div>
      </button>

      {expanded && (
        <div className="space-y-2 border-t border-[var(--admin-border)] p-3">
          {certificate.model_tests.length === 0 ? (
            <p className="py-4 text-center text-sm text-[var(--admin-text-muted)]">
              Noch keine Modelltests für dieses Zertifikat.
            </p>
          ) : (
            certificate.model_tests.map((mt) => <ModelTestRow key={mt.model_test_id} modelTest={mt} />)
          )}
        </div>
      )}
    </div>
  );
}

export function MockTestAnalyticsSkeleton() {
  return (
    <AdminCard className="h-[200px] animate-pulse">
      <div className="h-3 w-48 rounded bg-white/5" />
      <div className="mt-6 h-16 rounded-xl bg-white/5" />
    </AdminCard>
  );
}

export default function DashboardMockTestAnalytics({
  certificates,
}: {
  certificates: CertificateMockAnalytics[];
}) {
  return (
    <AdminCard>
      <h3 className="mb-4 text-sm font-semibold text-[var(--admin-text-primary)]">Mock Test Analytics</h3>
      {certificates.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-10 text-center">
          <FileCheck size={28} className="text-[var(--admin-text-muted)]" />
          <p className="text-sm text-[var(--admin-text-muted)]">
            Noch keine Zertifikate im Mock Test Management angelegt.
          </p>
          <Link
            href="/admin/mock-exams"
            className="text-xs font-medium text-[var(--admin-primary)] hover:underline"
          >
            Zertifikat anlegen →
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {certificates.map((certificate) => (
            <CertificateSection key={certificate.provider_id} certificate={certificate} />
          ))}
        </div>
      )}
    </AdminCard>
  );
}
