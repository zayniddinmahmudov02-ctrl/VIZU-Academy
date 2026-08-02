"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";

import { AdminCard, AdminPageHeader } from "@/components/admin/admin-ui";
import { useCrudList } from "@/features/admin/hooks/use-crud";
import {
  getDashboardSummary,
  getProviderAnalytics,
  mockExamProvidersApi,
} from "@/features/admin/services/mock-exam-service";

export default function MockExamAnalyticsPage() {
  const { data: summary } = useQuery({ queryKey: ["mock-exam-dashboard-summary"], queryFn: getDashboardSummary });
  const { data: providers } = useCrudList("mock-exam-providers", mockExamProvidersApi);
  const [providerId, setProviderId] = useState<string>("");

  const { data: analytics, isLoading } = useQuery({
    queryKey: ["mock-exam-provider-analytics", providerId],
    queryFn: () => getProviderAnalytics(providerId),
    enabled: !!providerId,
  });

  return (
    <div>
      <Link
        href="/admin/mock-exams"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--admin-text-muted)] hover:text-[var(--admin-text-primary)]"
      >
        <ArrowLeft size={14} />
        Mock Test Management
      </Link>

      <AdminPageHeader title="Analytics" description="Durchschnittswerte, Bestehensquote und Schwachstellen." />

      {summary && (
        <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard label="Prüfungsversuche" value={summary.total_attempts} />
          <StatCard label="Aktive Schüler" value={summary.students_attempted} />
          <StatCard label="Fragen im System" value={summary.questions} />
          <StatCard label="KI-Bewertungen" value={summary.ai_evaluations_used} />
        </div>
      )}

      <div className="mb-6 flex flex-wrap gap-2">
        {(providers ?? []).map((p) => (
          <button
            key={p.id}
            onClick={() => setProviderId(p.id)}
            className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
              providerId === p.id
                ? "bg-[var(--admin-primary)] text-white"
                : "bg-[var(--admin-card)] text-[var(--admin-text-primary)] ring-1 ring-[var(--admin-border-strong)] hover:bg-[var(--admin-card-hover)]"
            }`}
          >
            {p.name}
          </button>
        ))}
      </div>

      {!providerId && (
        <p className="text-sm text-[var(--admin-text-muted)]">Wähle ein Zertifikat, um Details zu sehen.</p>
      )}

      {isLoading && <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>}

      {analytics && (
        <div className="space-y-6">
          <div className="grid grid-cols-3 gap-4">
            <StatCard label="Durchschnitt" value={`${analytics.average_score_percent}%`} />
            <StatCard label="Bestehensquote" value={`${analytics.pass_rate_percent}%`} />
            <StatCard label="Versuche gesamt" value={analytics.total_attempts} />
          </div>

          <AdminCard>
            <h3 className="mb-3 text-sm font-semibold text-[var(--admin-text-primary)]">Modelltests</h3>
            <div className="space-y-3">
              {analytics.model_tests.map((mt) => (
                <div key={mt.model_test_id} className="rounded-lg bg-white/[0.02] p-3 ring-1 ring-[var(--admin-border)]">
                  <div className="mb-2 flex items-center justify-between">
                    <p className="text-sm font-semibold text-[var(--admin-text-primary)]">{mt.title}</p>
                    <p className="text-xs text-[var(--admin-text-muted)]">
                      {mt.average_score_percent}% Ø · {mt.pass_rate_percent}% bestanden · {mt.attempts} Versuche
                    </p>
                  </div>
                  <div className="grid grid-cols-4 gap-2">
                    {mt.kompetenzen.map((k) => (
                      <div key={k.kompetenz_id} className="rounded-md bg-white/[0.02] p-2 text-xs">
                        <p className="font-medium text-[var(--admin-text-secondary)]">{k.title}</p>
                        <p className="text-[var(--admin-text-muted)]">{k.average_score_percent}%</p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              {analytics.model_tests.length === 0 && (
                <p className="text-sm text-[var(--admin-text-muted)]">Noch keine Modelltests.</p>
              )}
            </div>
          </AdminCard>

          <AdminCard>
            <h3 className="mb-3 text-sm font-semibold text-[var(--admin-text-primary)]">
              Am häufigsten falsch beantwortet
            </h3>
            <div className="space-y-2">
              {analytics.most_failed_questions.map((q) => (
                <div key={q.question_id} className="flex items-center justify-between text-sm">
                  <span className="text-[var(--admin-text-secondary)]">{q.question_text}</span>
                  <span className="text-xs text-[var(--admin-text-muted)]">
                    {q.failure_rate_percent}% falsch ({q.times_correct}/{q.times_answered} richtig)
                  </span>
                </div>
              ))}
              {analytics.most_failed_questions.length === 0 && (
                <p className="text-sm text-[var(--admin-text-muted)]">Noch keine Daten.</p>
              )}
            </div>
          </AdminCard>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <AdminCard>
      <p className="text-2xl font-bold text-[var(--admin-text-primary)]">{value}</p>
      <p className="text-xs text-[var(--admin-text-muted)]">{label}</p>
    </AdminCard>
  );
}
