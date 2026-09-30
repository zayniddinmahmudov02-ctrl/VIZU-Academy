"use client";

import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Loader2, Trash2, Upload } from "lucide-react";

import { AdminButton, AdminCard } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import FileUploadField from "@/components/admin/file-upload-field";
import {
  createVizuMockAudio,
  deleteVizuMockAudio,
  getVizuMockHoerenContent,
  importVizuMockHoerenCsv,
  listVizuMockAudio,
  updateVizuMockAudio,
  type VizuMockHoerenCsvImportResult,
} from "@/features/admin/services/vizu-mock-admin-service";
import type { VizuMockAdminHoerenTask, VizuMockAudio } from "@/features/admin/types/vizu-mock-admin.types";

function formatDuration(seconds: number | null): string {
  if (seconds === null) return "—";
  const mm = Math.floor(seconds / 60);
  const ss = seconds % 60;
  return `${mm}:${String(ss).padStart(2, "0")}`;
}

function AufgabeAudioSlot({ task, audio }: { task: VizuMockAdminHoerenTask; audio: VizuMockAudio | undefined }) {
  const queryClient = useQueryClient();
  const [confirmDelete, setConfirmDelete] = useState(false);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["vizu-mock-admin-audio"] });
    queryClient.invalidateQueries({ queryKey: ["vizu-mock-admin-hoeren-content"] });
  };

  const createMutation = useMutation({
    mutationFn: (url: string) =>
      createVizuMockAudio({ title: `Aufgabe ${task.order_index} Audio`, audio_url: url, task_id: task.id }),
    onSuccess: invalidate,
  });

  const replaceMutation = useMutation({
    mutationFn: (url: string) => updateVizuMockAudio(audio!.id, { audio_url: url }),
    onSuccess: invalidate,
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteVizuMockAudio(audio!.id),
    onSuccess: () => {
      invalidate();
      setConfirmDelete(false);
    },
  });

  return (
    <div>
      {audio ? (
        <div className="space-y-2">
          <audio controls src={audio.audio_url} className="h-9 w-full" />
          <div className="flex items-center justify-between text-xs text-[var(--admin-text-muted)]">
            <span>Dauer: {formatDuration(audio.duration_seconds)}</span>
            <span className="rounded-full bg-[var(--admin-success,#22c55e)]/15 px-2 py-0.5 font-semibold text-[var(--admin-success,#22c55e)]">
              Hochgeladen
            </span>
          </div>
          <div className="flex items-center gap-2">
            <FileUploadField
              value={null}
              onChange={(url) => replaceMutation.mutate(url)}
              folder="audio"
              accept="audio/*"
              label={undefined}
            />
            <button
              type="button"
              onClick={() => setConfirmDelete(true)}
              aria-label="Audio löschen"
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[var(--admin-text-secondary)] transition hover:bg-[var(--admin-danger)]/10 hover:text-[var(--admin-danger)]"
            >
              <Trash2 size={15} />
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-[var(--admin-warning,#f59e0b)]">Nicht hochgeladen</p>
          <FileUploadField
            value={null}
            onChange={(url) => createMutation.mutate(url)}
            folder="audio"
            accept="audio/*"
            label="Audio-Datei"
          />
        </div>
      )}

      <ConfirmDialog
        open={confirmDelete}
        onOpenChange={setConfirmDelete}
        title="Audio löschen"
        description={`Möchten Sie das Audio für Aufgabe ${task.order_index} wirklich löschen?`}
        onConfirm={() => deleteMutation.mutate()}
        isPending={deleteMutation.isPending}
      />
    </div>
  );
}

/** CSV import for VIZU-Mock's own Hören Aufgabe/question/option content
 * — entirely separate from the regular course lesson's content, never
 * touches it. Columns: aufgabe (or task), question, type, option_a-d,
 * correct_answer, level (A1-C1 — determines each question's points:
 * A1=0.5 ... C1=2.5), points (informational, not authoritative), order.
 * Idempotent: re-importing an edited CSV updates existing Aufgabe/
 * questions/options in place instead of duplicating them. */
function HoerenCsvImport() {
  const queryClient = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<VizuMockHoerenCsvImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const importMutation = useMutation({
    mutationFn: () => importVizuMockHoerenCsv(file!),
    onSuccess: (res) => {
      setResult(res);
      setError(null);
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
      queryClient.invalidateQueries({ queryKey: ["vizu-mock-admin-hoeren-content"] });
      queryClient.invalidateQueries({ queryKey: ["vizu-mock-admin-overview"] });
      queryClient.invalidateQueries({ queryKey: ["vizu-mock-admin-level-analytics"] });
    },
    onError: () => {
      setResult(null);
      setError(
        "Import fehlgeschlagen. Bitte CSV-Format prüfen (aufgabe, question, type, option_a-d, correct_answer, level, points, order).",
      );
    },
  });

  return (
    <AdminCard className="mb-4">
      <h3 className="text-sm font-semibold text-[var(--admin-text-primary)]">Hören-Aufgaben per CSV importieren</h3>
      <p className="mt-1 text-xs text-[var(--admin-text-secondary)]">
        Spalten: aufgabe (oder task), question, type (MULTIPLE_CHOICE / TRUE_FALSE / CLOZE), option_a–d,
        correct_answer, level (A1–C1), points, order. Die Punktzahl wird immer aus dem Niveau abgeleitet (A1=0,5 ...
        C1=2,5) — die points-Spalte ist rein informativ.
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

export default function VizuMockHoerenTab() {
  const { data: tasks, isLoading: tasksLoading } = useQuery({
    queryKey: ["vizu-mock-admin-hoeren-content"],
    queryFn: getVizuMockHoerenContent,
  });

  const { data: audios, isLoading: audioLoading } = useQuery({
    queryKey: ["vizu-mock-admin-audio"],
    queryFn: listVizuMockAudio,
  });

  const isLoading = tasksLoading || audioLoading;

  const audioByTaskId = new Map((audios ?? []).filter((a) => a.task_id).map((a) => [a.task_id as string, a]));

  return (
    <div>
      <HoerenCsvImport />

      <p className="mb-4 text-sm text-[var(--admin-text-secondary)]">
        Hören-Aufgaben (Punkte je Niveau: A1=0,5 · A2=1,0 · B1=1,5 · B2=2,0 · C1=2,5 pro Frage). Fragen/Optionen
        werden per CSV-Import gepflegt — hier wird zusätzlich die zugehörige Audiodatei je Aufgabe verwaltet.
      </p>

      {isLoading ? (
        <div className="flex h-40 items-center justify-center">
          <Loader2 size={22} className="animate-spin text-[var(--admin-primary)]" />
        </div>
      ) : (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tasks?.map((task) => {
          const points = task.questions.reduce((sum, q) => sum + q.points, 0);
          return (
            <AdminCard key={task.id}>
              <div className="mb-3 flex items-center justify-between">
                <p className="text-sm font-semibold text-[var(--admin-text-primary)]">Aufgabe {task.order_index}</p>
                <span className="rounded-full bg-[var(--admin-primary)]/10 px-2 py-0.5 text-xs font-semibold text-[var(--admin-primary)]">
                  {task.level}
                </span>
              </div>
              <p className="mb-3 text-xs text-[var(--admin-text-muted)]">
                {task.questions.length} Frage(n) · {points} Punkt(e)
              </p>
              <AufgabeAudioSlot task={task} audio={audioByTaskId.get(task.id)} />
            </AdminCard>
          );
        })}
      </div>
      )}
    </div>
  );
}
