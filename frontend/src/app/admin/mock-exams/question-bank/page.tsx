"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Copy, FolderInput, Search, Trash2 } from "lucide-react";

import { AdminButton, AdminInput, AdminPageHeader } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FormDialog from "@/components/admin/form-dialog";
import { useCrudList, useCrudMutations } from "@/features/admin/hooks/use-crud";
import {
  duplicateQuestion,
  listQuestions,
  mockExamKompetenzenApi,
  mockExamLevelsApi,
  mockExamModelTestsApi,
  mockExamProvidersApi,
  mockExamQuestionsApi,
  mockExamTeileApi,
  moveQuestion,
  getReadingContentByTeil,
  getListeningContentByTeil,
} from "@/features/admin/services/mock-exam-service";
import type { MockQuestion } from "@/features/admin/types/mock-exam.types";

const TYPE_LABELS: Record<string, string> = {
  SINGLE_CHOICE: "Single Choice",
  MULTIPLE_CHOICE: "Multiple Choice",
  TRUE_FALSE: "Richtig/Falsch",
  MATCHING: "Zuordnung",
  ORDERING: "Reihenfolge",
  FILL_BLANK: "Lückentext",
  DROPDOWN: "Dropdown",
};

export default function QuestionBankPage() {
  const queryClient = useQueryClient();
  const { data: questions, isLoading } = useQuery({
    queryKey: ["mock-exam-question-bank"],
    queryFn: () => listQuestions({}),
  });
  const { remove } = useCrudMutations("mock-exam-question-bank", mockExamQuestionsApi);

  const [search, setSearch] = useState("");
  const [deleting, setDeleting] = useState<MockQuestion | null>(null);
  const [moving, setMoving] = useState<MockQuestion | null>(null);

  const filtered = useMemo(() => {
    if (!questions) return [];
    const term = search.trim().toLowerCase();
    if (!term) return questions;
    return questions.filter((q) => q.question_text.toLowerCase().includes(term));
  }, [questions, search]);

  async function handleDuplicate(question: MockQuestion) {
    await duplicateQuestion(question.id);
    queryClient.invalidateQueries({ queryKey: ["mock-exam-question-bank"] });
  }

  const columns: DataTableColumn<MockQuestion>[] = [
    { key: "text", header: "Frage", render: (item) => item.question_text },
    { key: "type", header: "Typ", render: (item) => TYPE_LABELS[item.question_type] },
    { key: "points", header: "Punkte", render: (item) => item.points },
    { key: "options", header: "Optionen", render: (item) => item.options.length },
    {
      key: "actions",
      header: "",
      render: (item) => (
        <div className="flex items-center justify-end gap-1.5">
          <button
            onClick={() => handleDuplicate(item)}
            aria-label="Duplizieren"
            title="Duplizieren"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--admin-text-secondary)] hover:bg-[var(--admin-primary)]/10 hover:text-[var(--admin-primary)]"
          >
            <Copy size={15} />
          </button>
          <button
            onClick={() => setMoving(item)}
            aria-label="Verschieben"
            title="Verschieben"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--admin-text-secondary)] hover:bg-[var(--admin-primary)]/10 hover:text-[var(--admin-primary)]"
          >
            <FolderInput size={15} />
          </button>
          <button
            onClick={() => setDeleting(item)}
            aria-label="Löschen"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--admin-text-secondary)] hover:bg-[var(--admin-danger)]/10 hover:text-[var(--admin-danger)]"
          >
            <Trash2 size={15} />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <Link
        href="/admin/mock-exams"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--admin-text-muted)] hover:text-[var(--admin-text-primary)]"
      >
        <ArrowLeft size={14} />
        Mock Test Management
      </Link>

      <AdminPageHeader
        title="Question Bank"
        description="Alle Fragen systemweit — duplizieren, verschieben oder löschen."
      />

      <div className="relative mb-6 max-w-sm">
        <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--admin-text-muted)]" />
        <AdminInput
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Fragen durchsuchen..."
          className="pl-9"
        />
      </div>

      <DataTable
        columns={columns}
        data={filtered}
        isLoading={isLoading}
        getRowId={(item) => item.id}
        emptyMessage="Noch keine Fragen im System."
      />

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(open) => !open && setDeleting(null)}
        title="Frage löschen"
        description="Diese Frage wird dauerhaft gelöscht."
        isPending={remove.isPending}
        onConfirm={async () => {
          if (!deleting) return;
          await remove.mutateAsync(deleting.id);
          queryClient.invalidateQueries({ queryKey: ["mock-exam-question-bank"] });
          setDeleting(null);
        }}
      />

      <FormDialog open={!!moving} onOpenChange={(open) => !open && setMoving(null)} title="Frage verschieben" size="lg">
        {moving && (
          <MoveQuestionForm
            question={moving}
            onDone={() => {
              setMoving(null);
              queryClient.invalidateQueries({ queryKey: ["mock-exam-question-bank"] });
            }}
          />
        )}
      </FormDialog>
    </div>
  );
}

function MoveQuestionForm({ question, onDone }: { question: MockQuestion; onDone: () => void }) {
  const { data: providers } = useCrudList("mock-exam-providers", mockExamProvidersApi);
  const [providerId, setProviderId] = useState("");

  const { data: levels } = useCrudList("mock-exam-levels", mockExamLevelsApi, { provider_id: providerId });
  const [levelId, setLevelId] = useState("");

  const { data: modelTests } = useCrudList("mock-exam-model-tests", mockExamModelTestsApi, { level_id: levelId });
  const [modelTestId, setModelTestId] = useState("");

  const { data: kompetenzen } = useCrudList("mock-exam-kompetenzen", mockExamKompetenzenApi, {
    model_test_id: modelTestId,
  });
  const relevantKompetenzen = (kompetenzen ?? []).filter((k) =>
    question.reading_content_id ? k.type === "LESEN" : k.type === "HOEREN",
  );
  const [kompetenzId, setKompetenzId] = useState("");

  const { data: teile } = useCrudList("mock-exam-teile", mockExamTeileApi, { kompetenz_id: kompetenzId });
  const [teilId, setTeilId] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleMove() {
    if (!teilId) return;
    setSubmitting(true);
    setError(null);
    try {
      const target = question.reading_content_id
        ? await getReadingContentByTeil(teilId)
        : await getListeningContentByTeil(teilId);
      if (!target) {
        setError("Der gewählte Teil hat noch keinen passenden Inhalt (Lesetext/Hörtext).");
        return;
      }
      await moveQuestion(
        question.id,
        question.reading_content_id ? { reading_content_id: target.id } : { listening_content_id: target.id },
      );
      onDone();
    } catch {
      setError("Verschieben fehlgeschlagen.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-[var(--admin-text-secondary)]">
        Verschiebe „{question.question_text}“ in einen anderen {question.reading_content_id ? "Lesetext" : "Hörtext"}.
      </p>
      {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}

      <Selector label="Zertifikat" value={providerId} onChange={(v) => { setProviderId(v); setLevelId(""); setModelTestId(""); setKompetenzId(""); setTeilId(""); }} options={(providers ?? []).map((p) => ({ id: p.id, label: p.name }))} />
      <Selector label="Level" value={levelId} onChange={(v) => { setLevelId(v); setModelTestId(""); setKompetenzId(""); setTeilId(""); }} options={(levels ?? []).map((l) => ({ id: l.id, label: l.level }))} disabled={!providerId} />
      <Selector label="Modelltest" value={modelTestId} onChange={(v) => { setModelTestId(v); setKompetenzId(""); setTeilId(""); }} options={(modelTests ?? []).map((m) => ({ id: m.id, label: m.title }))} disabled={!levelId} />
      <Selector label="Kompetenz" value={kompetenzId} onChange={(v) => { setKompetenzId(v); setTeilId(""); }} options={relevantKompetenzen.map((k) => ({ id: k.id, label: k.title }))} disabled={!modelTestId} />
      <Selector label="Teil" value={teilId} onChange={setTeilId} options={(teile ?? []).map((t) => ({ id: t.id, label: t.title }))} disabled={!kompetenzId} />

      <div className="flex justify-end gap-3 pt-2">
        <AdminButton onClick={handleMove} disabled={!teilId || submitting}>
          {submitting ? "Wird verschoben..." : "Verschieben"}
        </AdminButton>
      </div>
    </div>
  );
}

function Selector({
  label,
  value,
  onChange,
  options,
  disabled,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { id: string; label: string }[];
  disabled?: boolean;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">{label}</label>
      <select
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className="h-10 w-full rounded-lg bg-[var(--admin-card)] px-3.5 text-sm text-[var(--admin-text-primary)] outline-none ring-1 ring-[var(--admin-border-strong)] disabled:opacity-40"
      >
        <option value="">— auswählen —</option>
        {options.map((o) => (
          <option key={o.id} value={o.id}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}
