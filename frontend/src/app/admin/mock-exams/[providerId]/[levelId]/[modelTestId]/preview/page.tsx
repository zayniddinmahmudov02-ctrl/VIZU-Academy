"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft } from "lucide-react";

import { AdminPageHeader } from "@/components/admin/admin-ui";
import PaperTeilView from "@/features/vorbereitung/components/multilevel/paper-teil";
import { getExamPreview } from "@/features/vorbereitung/services/multilevel-exam-service";

// Admin preview of a Modelltest exactly as the exam paper shows it (also for drafts), keys marked green.
export default function ModelTestPreviewPage() {
  const { providerId, levelId, modelTestId } = useParams<{ providerId: string; levelId: string; modelTestId: string }>();
  const { data } = useQuery({ queryKey: ["multilevel-preview", modelTestId], queryFn: () => getExamPreview(modelTestId) });
  const [active, setActive] = useState(0);
  const section = data?.sections[active];

  return (
    <div>
      <Link href={`/admin/mock-exams/${providerId}/${levelId}/${modelTestId}`}
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--admin-text-muted)] hover:text-[var(--admin-text-primary)]">
        <ArrowLeft size={14} /> Zurück zum Editor
      </Link>
      <AdminPageHeader title={`Vorschau · ${data?.title ?? ""}`} description={data ? `Status ${data.status} · Lösungen grün markiert` : undefined} />
      {data && data.gaps.length > 0 && (
        <p className="mb-4 flex items-start gap-2 rounded-lg bg-[#f59e0b]/10 p-3 text-sm text-[#f59e0b]">
          <AlertTriangle size={15} className="mt-0.5 shrink-0" /> Noch keine vollständige Prüfung: {data.gaps.join("; ")}
        </p>
      )}
      <div className="mb-4 flex flex-wrap gap-2">
        {data?.sections.map((s, i) => (
          <button key={s.type} onClick={() => setActive(i)}
            className={`rounded-lg px-4 py-2 text-sm font-semibold ${i === active ? "bg-[var(--admin-primary)] text-white" : "bg-[var(--admin-card)] text-[var(--admin-text-primary)] ring-1 ring-[var(--admin-border-strong)]"}`}>
            {s.title} · {s.duration_minutes} Min.
          </button>
        ))}
      </div>
      {/* the exam paper uses the student theme tokens; shown in a light frame here */}
      <div className="space-y-4 rounded-2xl bg-[var(--admin-card)] p-3 sm:p-5">
        {section?.teile.length === 0 && <p className="text-sm text-[var(--admin-text-muted)]">Noch nicht verfügbar.</p>}
        {section?.teile.map((teil) => <PaperTeilView key={teil.id} teil={teil} mode="preview" />)}
      </div>
    </div>
  );
}
