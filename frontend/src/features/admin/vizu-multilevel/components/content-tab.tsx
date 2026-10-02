"use client";

import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpen, CheckCircle2, Eye, EyeOff, Headphones, Loader2, Pencil, Plus, Trash2, Upload } from "lucide-react";

import {
  AdminButton,
  AdminCard,
  AdminCheckbox,
  AdminInput,
  AdminLabel,
  AdminSelect,
  AdminTextarea,
} from "@/components/admin/admin-ui";
import AdminEmptySection from "@/components/admin/admin-empty-section";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import FormDialog from "@/components/admin/form-dialog";
import {
  createVizuMultilevelContentQuestion,
  createVizuMultilevelContentTask,
  deleteVizuMultilevelContentQuestion,
  deleteVizuMultilevelContentTask,
  getVizuMultilevelHoerenContent,
  getVizuMultilevelLesenContent,
  importVizuMultilevelHoerenCsv,
  importVizuMultilevelLesenCsv,
  listVizuMultilevelAudio,
  updateVizuMultilevelContentQuestion,
  updateVizuMultilevelContentTask,
} from "@/features/admin/vizu-multilevel/services/vizu-multilevel-admin-service";
import type {
  VizuMultilevelAdminQuestion,
  VizuMultilevelContentTask,
  VizuMultilevelQuestionPayload,
} from "@/features/admin/vizu-multilevel/types/vizu-multilevel-admin.types";

import VizuMultilevelAudioSlot from "./audio-slot";

type ContentSkill = "lesen" | "hoeren";

const LEVELS = ["A1", "A2", "B1", "B2", "C1"];
const QUESTION_TYPES: { value: VizuMultilevelQuestionPayload["question_type"]; label: string }[] = [
  { value: "MULTIPLE_CHOICE", label: "Multiple Choice" },
  { value: "TRUE_FALSE", label: "Richtig / Falsch" },
  { value: "CLOZE_TEXT", label: "Lückentext" },
  { value: "HEADLINE_MATCH", label: "Überschrift zuordnen" },
  { value: "AD_MATCH", label: "Anzeige zuordnen" },
  { value: "STATEMENT_MATCH", label: "Aussage zuordnen" },
  { value: "MAIN_IDEA", label: "Hauptaussage finden" },
  { value: "DETAIL", label: "Detailinformation" },
  { value: "INFO_MATCH", label: "Passende Information finden" },
  { value: "COMPREHENSION", label: "Textverständnis" },
];

const COPY: Record<ContentSkill, { label: string; queryKey: string; emptyTitle: string }> = {
  lesen: { label: "Lesen", queryKey: "vizu-multilevel-admin-lesen-content", emptyTitle: "Noch kein Lesen-Inhalt vorhanden" },
  hoeren: { label: "Hören", queryKey: "vizu-multilevel-admin-hoeren-content", emptyTitle: "Noch kein Hören-Inhalt vorhanden" },
};

function errorMessage(error: unknown): string {
  const data = (error as { response?: { data?: { message?: unknown; detail?: unknown } } }).response?.data;
  const raw = data?.message ?? data?.detail;
  return typeof raw === "string" ? raw : "Speichern fehlgeschlagen. Bitte Eingaben prüfen.";
}

// ============================================================
// CSV import (bulk content entry — idempotent)
// ============================================================

function ContentCsvImport({ skill }: { skill: ContentSkill }) {
  const queryClient = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  const importMutation = useMutation({
    mutationFn: () => (skill === "lesen" ? importVizuMultilevelLesenCsv(file!) : importVizuMultilevelHoerenCsv(file!)),
    onSuccess: (res) => {
      setMessage({
        ok: true,
        text: `${res.total_questions} Frage(n) importiert (${res.tasks_created} Aufgabe(n) neu, ${res.tasks_updated} aktualisiert · ${res.questions_created} Frage(n) neu, ${res.questions_updated} aktualisiert).`,
      });
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
      queryClient.invalidateQueries({ queryKey: [COPY[skill].queryKey] });
    },
    onError: () =>
      setMessage({
        ok: false,
        text: "Import fehlgeschlagen. Bitte CSV-Format prüfen (aufgabe, level, question, type, option_a-d, correct_answer, order).",
      }),
  });

  return (
    <div>
      <h3 className="text-sm font-semibold text-[var(--admin-text-primary)]">{COPY[skill].label}-Aufgaben per CSV importieren</h3>
      <p className="mt-1 text-xs text-[var(--admin-text-secondary)]">
        Optional für große Mengen. Spalten: aufgabe, level (A1–C1), question, type, option_a–d, correct_answer, order
        {skill === "lesen" ? ", task_passage / question_passage" : ""}. Erneutes Importieren aktualisiert vorhandene Einträge.
      </p>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="text-sm text-[var(--admin-text-secondary)]"
        />
        <AdminButton size="sm" variant="secondary" onClick={() => importMutation.mutate()} disabled={!file || importMutation.isPending}>
          <Upload size={14} />
          {importMutation.isPending ? "Wird importiert..." : "Importieren"}
        </AdminButton>
      </div>
      {message && (
        <p
          className={`mt-3 flex items-center gap-2 text-sm ${message.ok ? "text-[var(--admin-success,#22c55e)]" : "text-[var(--admin-danger)]"}`}
        >
          {message.ok && <CheckCircle2 size={15} />}
          {message.text}
        </p>
      )}
    </div>
  );
}

// ============================================================
// Aufgabe dialog
// ============================================================

interface TaskForm {
  level: string;
  order_index: number;
  text: string;
  is_published: boolean;
}

function TaskDialog({
  skill,
  task,
  open,
  nextOrder,
  onClose,
}: {
  skill: ContentSkill;
  task: VizuMultilevelContentTask | null;
  open: boolean;
  nextOrder: number;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const isEdit = task !== null;
  const [form, setForm] = useState<TaskForm>({ level: "A1", order_index: nextOrder, text: "", is_published: true });
  const [error, setError] = useState<string | null>(null);
  const [syncedKey, setSyncedKey] = useState<string>("");

  // Reset the form whenever the dialog opens for a (different) Aufgabe.
  const key = open ? `${task?.id ?? "new"}:${nextOrder}` : "";
  if (key !== syncedKey) {
    setSyncedKey(key);
    if (open) {
      setError(null);
      setForm(
        task
          ? {
              level: task.level,
              order_index: task.order_index,
              text: (skill === "lesen" ? task.passage_text : task.transcript) ?? "",
              is_published: task.is_published,
            }
          : { level: "A1", order_index: nextOrder, text: "", is_published: true },
      );
    }
  }

  const saveMutation = useMutation({
    mutationFn: () => {
      const payload = {
        level: form.level,
        order_index: form.order_index,
        is_published: form.is_published,
        ...(skill === "lesen" ? { passage_text: form.text || null } : { transcript: form.text || null }),
      };
      return isEdit ? updateVizuMultilevelContentTask(task!.id, payload) : createVizuMultilevelContentTask(skill, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [COPY[skill].queryKey] });
      onClose();
    },
    onError: (e) => setError(errorMessage(e)),
  });

  return (
    <FormDialog
      open={open}
      onOpenChange={(o) => !o && onClose()}
      title={isEdit ? `Aufgabe ${task!.order_index} bearbeiten` : `Neue ${COPY[skill].label}-Aufgabe`}
      size="lg"
      footer={
        <>
          <AdminButton variant="ghost" onClick={onClose} disabled={saveMutation.isPending}>
            Abbrechen
          </AdminButton>
          <AdminButton onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}>
            {saveMutation.isPending ? "Wird gespeichert..." : "Speichern"}
          </AdminButton>
        </>
      }
    >
      <div className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <AdminLabel>Niveau (nur intern — Studenten sehen es nicht)</AdminLabel>
            <AdminSelect value={form.level} onChange={(e) => setForm({ ...form, level: e.target.value })}>
              {LEVELS.map((l) => (
                <option key={l} value={l}>
                  {l}
                </option>
              ))}
            </AdminSelect>
          </div>
          <div>
            <AdminLabel>Reihenfolge</AdminLabel>
            <AdminInput
              type="number"
              min={1}
              value={form.order_index}
              onChange={(e) => setForm({ ...form, order_index: Number(e.target.value) })}
            />
          </div>
        </div>

        <div>
          <AdminLabel>{skill === "lesen" ? "Lesetext (gemeinsam für alle Fragen, optional)" : "Transkript (nur für Admins sichtbar)"}</AdminLabel>
          <AdminTextarea value={form.text} onChange={(e) => setForm({ ...form, text: e.target.value })} rows={8} />
        </div>

        <div className="flex items-center gap-2">
          <AdminCheckbox
            checked={form.is_published}
            onCheckedChange={(checked) => setForm({ ...form, is_published: checked })}
            aria-label="Veröffentlicht"
          />
          <span className="text-sm text-[var(--admin-text-primary)]">Veröffentlicht (für Studenten sichtbar)</span>
        </div>

        {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}
      </div>
    </FormDialog>
  );
}

// ============================================================
// Question dialog (question + options + correct answer + points + order)
// ============================================================

interface QuestionForm {
  question_type: VizuMultilevelQuestionPayload["question_type"];
  passage_text: string;
  prompt: string;
  order_index: number;
  points: number;
  is_active: boolean;
  options: { option_text: string; is_correct: boolean }[];
}

function emptyQuestionForm(order: number): QuestionForm {
  return {
    question_type: "MULTIPLE_CHOICE",
    passage_text: "",
    prompt: "",
    order_index: order,
    points: 5,
    is_active: true,
    options: [
      { option_text: "", is_correct: true },
      { option_text: "", is_correct: false },
      { option_text: "", is_correct: false },
      { option_text: "", is_correct: false },
    ],
  };
}

function QuestionDialog({
  skill,
  task,
  question,
  open,
  onClose,
}: {
  skill: ContentSkill;
  task: VizuMultilevelContentTask | null;
  question: VizuMultilevelAdminQuestion | null;
  open: boolean;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const isEdit = question !== null;
  const nextOrder = (task?.questions.reduce((max, q) => Math.max(max, q.order_index), 0) ?? 0) + 1;
  const [form, setForm] = useState<QuestionForm>(emptyQuestionForm(1));
  const [error, setError] = useState<string | null>(null);
  const [syncedKey, setSyncedKey] = useState("");

  const key = open ? `${task?.id}:${question?.id ?? "new"}` : "";
  if (key !== syncedKey) {
    setSyncedKey(key);
    if (open) {
      setError(null);
      setForm(
        question
          ? {
              question_type: question.question_type,
              passage_text: question.passage_text ?? "",
              prompt: question.prompt,
              order_index: question.order_index,
              points: question.points,
              is_active: question.is_active,
              options: question.options.map((o) => ({ option_text: o.option_text, is_correct: o.is_correct })),
            }
          : emptyQuestionForm(nextOrder),
      );
    }
  }

  const saveMutation = useMutation({
    mutationFn: () => {
      const payload: VizuMultilevelQuestionPayload = {
        question_type: form.question_type,
        passage_text: skill === "lesen" ? form.passage_text || null : null,
        prompt: form.prompt,
        order_index: form.order_index,
        points: form.points,
        is_active: form.is_active,
        options: form.options.filter((o) => o.option_text.trim() !== ""),
      };
      return isEdit
        ? updateVizuMultilevelContentQuestion(question!.id, payload)
        : createVizuMultilevelContentQuestion(task!.id, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [COPY[skill].queryKey] });
      onClose();
    },
    onError: (e) => setError(errorMessage(e)),
  });

  function setCorrect(index: number) {
    setForm({ ...form, options: form.options.map((o, i) => ({ ...o, is_correct: i === index })) });
  }

  return (
    <FormDialog
      open={open}
      onOpenChange={(o) => !o && onClose()}
      title={isEdit ? "Frage bearbeiten" : "Neue Frage"}
      size="xl"
      footer={
        <>
          <AdminButton variant="ghost" onClick={onClose} disabled={saveMutation.isPending}>
            Abbrechen
          </AdminButton>
          <AdminButton onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}>
            {saveMutation.isPending ? "Wird gespeichert..." : "Speichern"}
          </AdminButton>
        </>
      }
    >
      <div className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <AdminLabel>Fragetyp</AdminLabel>
            <AdminSelect
              value={form.question_type}
              onChange={(e) => setForm({ ...form, question_type: e.target.value as QuestionForm["question_type"] })}
            >
              {QUESTION_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </AdminSelect>
          </div>
          <div>
            <AdminLabel>Reihenfolge</AdminLabel>
            <AdminInput
              type="number"
              min={1}
              value={form.order_index}
              onChange={(e) => setForm({ ...form, order_index: Number(e.target.value) })}
            />
          </div>
          <div>
            <AdminLabel>Punkte</AdminLabel>
            <AdminInput
              type="number"
              min={0}
              step="0.5"
              value={form.points}
              onChange={(e) => setForm({ ...form, points: Number(e.target.value) })}
            />
          </div>
        </div>

        {skill === "lesen" && (
          <div>
            <AdminLabel>Eigener Text für diese Frage (optional)</AdminLabel>
            <AdminTextarea
              value={form.passage_text}
              onChange={(e) => setForm({ ...form, passage_text: e.target.value })}
              rows={4}
            />
          </div>
        )}

        <div>
          <AdminLabel>Frage</AdminLabel>
          <AdminTextarea value={form.prompt} onChange={(e) => setForm({ ...form, prompt: e.target.value })} rows={3} />
        </div>

        <div>
          <AdminLabel>Antwortoptionen — richtige Antwort markieren</AdminLabel>
          <div className="space-y-2">
            {form.options.map((option, index) => (
              <div key={index} className="flex items-center gap-2">
                <input
                  type="radio"
                  name="correct-option"
                  checked={option.is_correct}
                  onChange={() => setCorrect(index)}
                  aria-label={`Option ${index + 1} ist richtig`}
                  className="h-4 w-4 shrink-0 accent-[var(--admin-primary)]"
                />
                <AdminInput
                  value={option.option_text}
                  placeholder={`Option ${index + 1}`}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      options: form.options.map((o, i) => (i === index ? { ...o, option_text: e.target.value } : o)),
                    })
                  }
                />
                {form.options.length > 2 && (
                  <button
                    type="button"
                    aria-label="Option entfernen"
                    onClick={() => {
                      const remaining = form.options.filter((_, i) => i !== index);
                      if (!remaining.some((o) => o.is_correct)) remaining[0] = { ...remaining[0], is_correct: true };
                      setForm({ ...form, options: remaining });
                    }}
                    className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[var(--admin-text-secondary)] transition hover:bg-[var(--admin-danger)]/10 hover:text-[var(--admin-danger)]"
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            ))}
          </div>
          {form.options.length < 6 && (
            <AdminButton
              size="sm"
              variant="ghost"
              className="mt-2"
              onClick={() => setForm({ ...form, options: [...form.options, { option_text: "", is_correct: false }] })}
            >
              <Plus size={13} />
              Option hinzufügen
            </AdminButton>
          )}
        </div>

        {skill === "lesen" && (
          <div className="flex items-center gap-2">
            <AdminCheckbox
              checked={form.is_active}
              onCheckedChange={(checked) => setForm({ ...form, is_active: checked })}
              aria-label="Aktiv"
            />
            <span className="text-sm text-[var(--admin-text-primary)]">Aktiv (inaktive Fragen werden weder gezeigt noch bewertet)</span>
          </div>
        )}

        {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}
      </div>
    </FormDialog>
  );
}

// ============================================================
// The tab
// ============================================================

export default function VizuMultilevelContentTab({ skill }: { skill: ContentSkill }) {
  const queryClient = useQueryClient();
  const copy = COPY[skill];

  const { data: tasks, isLoading } = useQuery({
    queryKey: [copy.queryKey],
    queryFn: skill === "lesen" ? getVizuMultilevelLesenContent : getVizuMultilevelHoerenContent,
  });
  const { data: audios } = useQuery({
    queryKey: ["vizu-multilevel-admin-audio"],
    queryFn: listVizuMultilevelAudio,
    enabled: skill === "hoeren",
  });

  const [taskDialog, setTaskDialog] = useState<{ open: boolean; task: VizuMultilevelContentTask | null }>({
    open: false,
    task: null,
  });
  const [questionDialog, setQuestionDialog] = useState<{
    open: boolean;
    task: VizuMultilevelContentTask | null;
    question: VizuMultilevelAdminQuestion | null;
  }>({ open: false, task: null, question: null });
  const [deleteTarget, setDeleteTarget] = useState<
    { kind: "task"; task: VizuMultilevelContentTask } | { kind: "question"; id: string } | null
  >(null);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: [copy.queryKey] });

  const publishMutation = useMutation({
    mutationFn: (task: VizuMultilevelContentTask) => updateVizuMultilevelContentTask(task.id, { is_published: !task.is_published }),
    onSuccess: invalidate,
  });

  const deleteMutation = useMutation({
    mutationFn: async () => {
      if (deleteTarget!.kind === "task") await deleteVizuMultilevelContentTask(deleteTarget!.task.id);
      else await deleteVizuMultilevelContentQuestion(deleteTarget!.id);
    },
    onSuccess: () => {
      invalidate();
      setDeleteTarget(null);
    },
  });

  const audioByTaskId = new Map((audios ?? []).filter((a) => a.task_id).map((a) => [a.task_id as string, a]));
  const nextTaskOrder = (tasks?.reduce((max, t) => Math.max(max, t.order_index), 0) ?? 0) + 1;
  const SkillIcon = skill === "lesen" ? BookOpen : Headphones;

  return (
    <div className="space-y-4">
      <AdminCard>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <p className="max-w-xl text-sm text-[var(--admin-text-secondary)]">
            {copy.label}-Aufgaben mit Fragen, Antwortoptionen, richtiger Antwort, Reihenfolge und Punkten.
            Unveröffentlichte Aufgaben sind für Studenten unsichtbar; das Niveau ist rein intern.
          </p>
          <AdminButton onClick={() => setTaskDialog({ open: true, task: null })}>
            <Plus size={15} />
            Neue Aufgabe
          </AdminButton>
        </div>
        <div className="mt-4 border-t border-[var(--admin-border)] pt-4">
          <ContentCsvImport skill={skill} />
        </div>
      </AdminCard>

      {isLoading && (
        <div className="flex h-40 items-center justify-center">
          <Loader2 size={22} className="animate-spin text-[var(--admin-primary)]" />
        </div>
      )}

      {!isLoading && (!tasks || tasks.length === 0) && (
        <AdminEmptySection
          icon={SkillIcon}
          title={copy.emptyTitle}
          description="Der Inhalt ist bewusst leer. Lege oben die erste Aufgabe an oder importiere eine CSV-Datei."
        />
      )}

      {tasks?.map((task) => {
        const points = task.questions.reduce((sum, q) => sum + q.points, 0);
        return (
          <AdminCard key={task.id}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-sm font-semibold text-[var(--admin-text-primary)]">Aufgabe {task.order_index}</p>
                <span className="rounded-full bg-[var(--admin-primary)]/10 px-2 py-0.5 text-xs font-semibold text-[var(--admin-primary)]">
                  {task.level}
                </span>
                <span
                  className={
                    task.is_published
                      ? "rounded-full bg-[var(--admin-success,#22c55e)]/15 px-2 py-0.5 text-[10px] font-semibold text-[var(--admin-success,#22c55e)]"
                      : "rounded-full bg-[var(--admin-text-muted)]/15 px-2 py-0.5 text-[10px] font-semibold text-[var(--admin-text-muted)]"
                  }
                >
                  {task.is_published ? "Veröffentlicht" : "Entwurf"}
                </span>
                <span className="text-xs text-[var(--admin-text-muted)]">
                  {task.questions.length} Frage(n) · {points} Punkt(e)
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-1.5">
                <AdminButton size="sm" variant="secondary" onClick={() => publishMutation.mutate(task)} disabled={publishMutation.isPending}>
                  {task.is_published ? <EyeOff size={13} /> : <Eye size={13} />}
                  {task.is_published ? "Zurückziehen" : "Veröffentlichen"}
                </AdminButton>
                <AdminButton size="sm" variant="secondary" onClick={() => setTaskDialog({ open: true, task })}>
                  <Pencil size={13} />
                  Bearbeiten
                </AdminButton>
                <AdminButton size="sm" variant="secondary" onClick={() => setQuestionDialog({ open: true, task, question: null })}>
                  <Plus size={13} />
                  Frage
                </AdminButton>
                <AdminButton size="sm" variant="ghost" onClick={() => setDeleteTarget({ kind: "task", task })}>
                  <Trash2 size={13} />
                </AdminButton>
              </div>
            </div>

            {skill === "lesen" && task.passage_text && (
              <p className="mt-3 line-clamp-3 text-sm text-[var(--admin-text-secondary)]">{task.passage_text}</p>
            )}
            {skill === "hoeren" && (
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <VizuMultilevelAudioSlot task={task} audio={audioByTaskId.get(task.id)} />
                {task.transcript && (
                  <p className="line-clamp-4 text-xs text-[var(--admin-text-muted)]">Transkript: {task.transcript}</p>
                )}
              </div>
            )}

            {task.questions.length > 0 && (
              <ul className="mt-4 divide-y divide-[var(--admin-border)] rounded-lg ring-1 ring-[var(--admin-border)]">
                {task.questions.map((q) => (
                  <li key={q.id} className="flex items-start justify-between gap-3 px-3 py-2.5">
                    <div className="min-w-0 text-sm">
                      <p className="font-medium text-[var(--admin-text-primary)]">
                        {q.order_index}. {q.prompt}
                      </p>
                      <p className="mt-0.5 text-xs text-[var(--admin-text-muted)]">
                        Richtig: {q.options.find((o) => o.is_correct)?.option_text ?? "—"} · {q.points} Punkt(e)
                        {skill === "lesen" && !q.is_active ? " · inaktiv" : ""}
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-1">
                      <button
                        type="button"
                        aria-label="Frage bearbeiten"
                        onClick={() => setQuestionDialog({ open: true, task, question: q })}
                        className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--admin-text-secondary)] transition hover:bg-white/5"
                      >
                        <Pencil size={14} />
                      </button>
                      <button
                        type="button"
                        aria-label="Frage löschen"
                        onClick={() => setDeleteTarget({ kind: "question", id: q.id })}
                        className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--admin-text-secondary)] transition hover:bg-[var(--admin-danger)]/10 hover:text-[var(--admin-danger)]"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </AdminCard>
        );
      })}

      <TaskDialog
        skill={skill}
        task={taskDialog.task}
        open={taskDialog.open}
        nextOrder={nextTaskOrder}
        onClose={() => setTaskDialog({ open: false, task: null })}
      />
      <QuestionDialog
        skill={skill}
        task={questionDialog.task}
        question={questionDialog.question}
        open={questionDialog.open}
        onClose={() => setQuestionDialog({ open: false, task: null, question: null })}
      />
      <ConfirmDialog
        open={deleteTarget !== null}
        onOpenChange={(o) => !o && setDeleteTarget(null)}
        title={deleteTarget?.kind === "task" ? "Aufgabe löschen" : "Frage löschen"}
        description={
          deleteTarget?.kind === "task"
            ? `Aufgabe ${deleteTarget.task.order_index} mit allen Fragen wirklich löschen?`
            : "Diese Frage wirklich löschen?"
        }
        onConfirm={() => deleteMutation.mutate()}
        isPending={deleteMutation.isPending}
      />
    </div>
  );
}
