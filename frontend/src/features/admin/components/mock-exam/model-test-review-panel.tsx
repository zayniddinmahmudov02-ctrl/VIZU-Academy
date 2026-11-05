"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, Eye, EyeOff, FileText } from "lucide-react";

import { AdminButton } from "@/components/admin/admin-ui";
import {
  getModelTestReview,
  getModelTestSourcePdf,
  mockExamModelTestsApi,
} from "@/features/admin/services/mock-exam-service";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import type { ModelTest } from "@/features/admin/types/mock-exam.types";

// Status + publish/hide, source PDF, admin check-list and readiness (keys / audio) of one Modelltest.
// Publishing is refused by the backend (MODEL_TEST_NOT_READY) while a key or a Hören audio is missing.
export default function ModelTestReviewPanel({ modelTest }: { modelTest: ModelTest }) {
  const queryClient = useQueryClient();
  const { data: review } = useQuery({
    queryKey: ["mock-exam-model-test-review", modelTest.id],
    queryFn: () => getModelTestReview(modelTest.id),
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const published = modelTest.status === "PUBLISHED";

  async function toggleStatus() {
    setBusy(true);
    setError(null);
    try {
      await mockExamModelTestsApi.update(modelTest.id, { status: published ? "DRAFT" : "PUBLISHED" });
      await queryClient.invalidateQueries({ queryKey: ["mock-exam-model-tests"] });
    } catch (err) {
      setError(apiErrorMessage(err, "Status konnte nicht geändert werden."));
    } finally {
      setBusy(false);
    }
  }

  async function openPdf() {
    setError(null);
    const tab = window.open("", "_blank");
    try {
      const blob = await getModelTestSourcePdf(modelTest.id);
      const url = URL.createObjectURL(new Blob([blob], { type: "application/pdf" }));
      if (tab) tab.location.href = url;
      else window.location.assign(url);
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch (err) {
      tab?.close();
      setError(apiErrorMessage(err, "PDF konnte nicht geladen werden."));
    }
  }

  const r = review?.readiness;

  return (
    <div className="mb-6 space-y-4 rounded-2xl bg-[var(--admin-card)] p-5 ring-1 ring-[var(--admin-border)]" data-testid="model-test-review">
      <div className="flex flex-wrap items-center gap-3">
        <span
          className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
            published ? "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]" : "bg-white/5 text-[var(--admin-text-muted)]"
          }`}
        >
          {published ? "Veröffentlicht" : modelTest.status === "ARCHIVED" ? "Archiviert" : "Entwurf (für Schüler unsichtbar)"}
        </span>
        <AdminButton size="sm" variant={published ? "secondary" : "primary"} onClick={toggleStatus} disabled={busy} data-testid="toggle-publish">
          {published ? <EyeOff size={14} /> : <Eye size={14} />}
          {published ? "Verbergen" : "Veröffentlichen"}
        </AdminButton>
        {review?.has_source_pdf && (
          <AdminButton size="sm" variant="secondary" onClick={openPdf} data-testid="open-source-pdf">
            <FileText size={14} />
            PDF ansehen
          </AdminButton>
        )}
        {review?.source_pdf_name && <span className="text-xs text-[var(--admin-text-muted)]">{review.source_pdf_name}</span>}
        {review?.origin === "vizu" && (
          <span className="text-xs text-[var(--admin-text-muted)]">Von VIZU erstellt — kein offizielles Prüfungsmaterial</span>
        )}
      </div>

      {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}

      {r && (
        <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
          <span className="flex items-center gap-1.5 text-[var(--admin-text-primary)]">
            {r.missing_keys.length ? <AlertTriangle size={14} className="text-[#f59e0b]" /> : <CheckCircle2 size={14} className="text-[var(--admin-accent)]" />}
            Lösungen: {r.keys_set} / {r.questions}
          </span>
          <span className="flex items-center gap-1.5 text-[var(--admin-text-primary)]">
            {r.missing_audio.length ? <AlertTriangle size={14} className="text-[#f59e0b]" /> : <CheckCircle2 size={14} className="text-[var(--admin-accent)]" />}
            Hören-Audio fehlt: {r.missing_audio.length ? r.missing_audio.join(", ") : "—"}
          </span>
        </div>
      )}

      {review && review.review.length > 0 && (
        <details open={review.review.length <= 6}>
          <summary className="cursor-pointer text-sm font-semibold text-[var(--admin-text-primary)]">
            Prüfliste ({review.review.length})
          </summary>
          <ul className="mt-2 space-y-1.5" data-testid="review-list">
            {review.review.map((item, i) => (
              <li key={i} className="text-sm text-[var(--admin-text-muted)]">
                <span className="font-semibold text-[var(--admin-text-primary)]">{item.where}:</span> {item.note}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}
