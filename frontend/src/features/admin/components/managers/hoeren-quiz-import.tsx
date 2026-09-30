"use client";

import { useRef, useState } from "react";
import { CheckCircle2, Upload } from "lucide-react";

import { AdminButton, AdminCard } from "@/components/admin/admin-ui";
import { importQuizCsv, type QuizCsvImportResult } from "@/features/admin/services/quiz-csv-service";

/** Admin-only CSV import for the lesson's real Hören listening-
 * comprehension quiz — no manual question-by-question editor here on
 * purpose (see backend/app/api/quiz/router.py: "Manual quiz authoring
 * was removed from the admin panel — content is inserted directly into
 * the DB instead"); this is an IMPORT mechanism, not a quiz builder,
 * consistent with that decision. Safe to re-run: the backend matches
 * existing questions/options by their natural key and updates them in
 * place instead of duplicating. */
export default function HoerenQuizImport({ lessonId }: { lessonId: string }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<QuizCsvImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleImport() {
    if (!file) return;
    setImporting(true);
    setError(null);
    setResult(null);
    try {
      const res = await importQuizCsv(lessonId, "HOEREN", "Hören", file);
      setResult(res);
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
    } catch {
      setError("Import fehlgeschlagen. Bitte CSV-Format prüfen (aufgabe, question, type, option_a-d, correct_answer, points, order).");
    } finally {
      setImporting(false);
    }
  }

  return (
    <AdminCard>
      <h3 className="text-sm font-semibold text-[var(--admin-text-primary)]">Hören-Quiz per CSV importieren</h3>
      <p className="mt-1 text-xs text-[var(--admin-text-secondary)]">
        Spalten: aufgabe (oder task), question, type (MULTIPLE_CHOICE / TRUE_FALSE / CLOZE), option_a–d,
        correct_answer, points, order. Ein erneuter Import mit derselben Reihenfolge aktualisiert vorhandene Fragen,
        statt Duplikate anzulegen.
      </p>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="text-sm text-[var(--admin-text-secondary)]"
        />
        <AdminButton size="sm" onClick={handleImport} disabled={!file || importing}>
          <Upload size={14} />
          {importing ? "Wird importiert..." : "Importieren"}
        </AdminButton>
      </div>

      {error && <p className="mt-3 text-sm text-[var(--admin-danger)]">{error}</p>}

      {result && (
        <div className="mt-3 flex items-center gap-2 rounded-lg bg-[var(--admin-success,#22c55e)]/10 px-3 py-2 text-sm text-[var(--admin-success,#22c55e)]">
          <CheckCircle2 size={15} />
          {result.total_questions} Frage(n) importiert ({result.created_questions} neu, {result.updated_questions}{" "}
          aktualisiert).
        </div>
      )}
    </AdminCard>
  );
}
