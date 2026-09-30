"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Trash2 } from "lucide-react";

import { AdminCard } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import FileUploadField from "@/components/admin/file-upload-field";
import {
  createVizuMockAudio,
  deleteVizuMockAudio,
  getVizuMockHoerenContent,
  listVizuMockAudio,
  updateVizuMockAudio,
} from "@/features/admin/services/vizu-mock-admin-service";
import type { VizuMockAdminHoerenTask, VizuMockAudio } from "@/features/admin/types/vizu-mock-admin.types";
import { useState } from "react";

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

  if (isLoading) {
    return (
      <div className="flex h-40 items-center justify-center">
        <Loader2 size={22} className="animate-spin text-[var(--admin-primary)]" />
      </div>
    );
  }

  return (
    <div>
      <p className="mb-4 text-sm text-[var(--admin-text-secondary)]">
        5 Hören-Aufgaben (je 4 Fragen, 1 Punkt pro Frage). Fragen/Optionen werden per Import gepflegt — hier wird nur
        die zugehörige Audiodatei je Aufgabe verwaltet.
      </p>
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
    </div>
  );
}
