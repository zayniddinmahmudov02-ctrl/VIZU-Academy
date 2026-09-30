"use client";

import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpen, CheckCircle2, Loader2, Upload } from "lucide-react";

import { AdminButton, AdminCard } from "@/components/admin/admin-ui";
import AdminEmptySection from "@/components/admin/admin-empty-section";
import {
  getVizuMockLesenContent,
  importVizuMockLesenCsv,
  type VizuMockLesenCsvImportResult,
} from "@/features/admin/services/vizu-mock-admin-service";

/** CSV import for VIZU-Mock's own Lesen Aufgabe/question/option content
 * — mirrors the Hören tab's importer (see hoeren-tab.tsx). Columns:
 * aufgabe (or task), level, task_passage, question, question_passage,
 * type, option_a-d, correct_answer, points (informational — always 5
 * per question), order. Idempotent: re-importing an edited CSV updates
 * existing Aufgabe/questions/options in place instead of duplicating. */
function LesenCsvImport() {
  const queryClient = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<VizuMockLesenCsvImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const importMutation = useMutation({
    mutationFn: () => importVizuMockLesenCsv(file!),
    onSuccess: (res) => {
      setResult(res);
      setError(null);
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
      queryClient.invalidateQueries({ queryKey: ["vizu-mock-admin-lesen-content"] });
      queryClient.invalidateQueries({ queryKey: ["vizu-mock-admin-overview"] });
      queryClient.invalidateQueries({ queryKey: ["vizu-mock-admin-level-analytics"] });
    },
    onError: () => {
      setResult(null);
      setError(
        "Import fehlgeschlagen. Bitte CSV-Format prüfen (aufgabe, level, task_passage, question, question_passage, type, option_a-d, correct_answer, points, order).",
      );
    },
  });

  return (
    <AdminCard className="mb-4">
      <h3 className="text-sm font-semibold text-[var(--admin-text-primary)]">Lesen-Aufgaben per CSV importieren</h3>
      <p className="mt-1 text-xs text-[var(--admin-text-secondary)]">
        Spalten: aufgabe (oder task), level (A1–C1), task_passage (gemeinsamer Text je Aufgabe), question,
        question_passage (eigener Text je Frage), type (MULTIPLE_CHOICE / TRUE_FALSE / CLOZE), option_a–d,
        correct_answer, points, order. Die Punktzahl bleibt fest bei 5 pro Frage — die points-Spalte ist rein
        informativ.
      </p>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="text-sm text-[var(--admin-text-secondary)]"
        />
        <AdminButton size="sm" onClick={() => importMutation.mutate()} disabled={!file || importMutation.isPending}>
          <Upload size={14} />
          {importMutation.isPending ? "Wird importiert..." : "Importieren"}
        </AdminButton>
      </div>

      {error && <p className="mt-3 text-sm text-[var(--admin-danger)]">{error}</p>}

      {result && (
        <div className="mt-3 flex items-center gap-2 rounded-lg bg-[var(--admin-success,#22c55e)]/10 px-3 py-2 text-sm text-[var(--admin-success,#22c55e)]">
          <CheckCircle2 size={15} />
          {result.total_questions} Frage(n) importiert ({result.tasks_created} Aufgabe(n) neu,{" "}
          {result.tasks_updated} aktualisiert · {result.questions_created} Frage(n) neu,{" "}
          {result.questions_updated} aktualisiert).
        </div>
      )}
    </AdminCard>
  );
}

export default function VizuMockLesenTab() {
  const { data: tasks, isLoading } = useQuery({
    queryKey: ["vizu-mock-admin-lesen-content"],
    queryFn: getVizuMockLesenContent,
  });

  return (
    <div>
      <LesenCsvImport />

      {isLoading && (
        <div className="flex h-40 items-center justify-center">
          <Loader2 size={22} className="animate-spin text-[var(--admin-primary)]" />
        </div>
      )}

      {!isLoading && (!tasks || tasks.length === 0) && (
        <AdminEmptySection
          icon={BookOpen}
          title="Noch kein Lesen-Inhalt vorhanden"
          description="Für Lesen wurden noch keine Aufgaben angelegt."
        />
      )}

      {!isLoading && tasks && tasks.length > 0 && (
        <>
          <p className="mb-4 text-sm text-[var(--admin-text-secondary)]">
            Schreibgeschützte Übersicht der eingepflegten Lesen-Aufgaben ({tasks.length} Aufgaben) — Fragen/Optionen
            werden per CSV-Import oben gepflegt.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            {tasks.map((task) => (
              <AdminCard key={task.id}>
                <div className="mb-2 flex items-center justify-between">
                  <p className="text-sm font-semibold text-[var(--admin-text-primary)]">
                    Aufgabe {task.order_index}
                  </p>
                  <span className="rounded-full bg-[var(--admin-primary)]/10 px-2 py-0.5 text-xs font-semibold text-[var(--admin-primary)]">
                    {task.level}
                  </span>
                </div>
                <p className="text-xs text-[var(--admin-text-muted)]">{task.questions.length} Frage(n)</p>
                {task.passage_text && (
                  <p className="mt-2 line-clamp-3 text-sm text-[var(--admin-text-secondary)]">{task.passage_text}</p>
                )}
              </AdminCard>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
