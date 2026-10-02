"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";

import ConfirmDialog from "@/components/admin/confirm-dialog";
import FileUploadField from "@/components/admin/file-upload-field";
import {
  createVizuMultilevelAudio,
  deleteVizuMultilevelAudio,
  updateVizuMultilevelAudio,
} from "@/features/admin/vizu-multilevel/services/vizu-multilevel-admin-service";
import type {
  VizuMultilevelAudio,
  VizuMultilevelContentTask,
} from "@/features/admin/vizu-multilevel/types/vizu-multilevel-admin.types";

function formatDuration(seconds: number | null): string {
  if (seconds === null) return "—";
  const mm = Math.floor(seconds / 60);
  const ss = seconds % 60;
  return `${mm}:${String(ss).padStart(2, "0")}`;
}

/** Audio upload / replace / delete for one Hören Aufgabe. The file goes to
 * the generic media storage; the resulting URL is recorded on a
 * VIZU-Multilevel-owned audio row linked to the Aufgabe. */
export default function VizuMultilevelAudioSlot({
  task,
  audio,
}: {
  task: VizuMultilevelContentTask;
  audio: VizuMultilevelAudio | undefined;
}) {
  const queryClient = useQueryClient();
  const [confirmDelete, setConfirmDelete] = useState(false);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["vizu-multilevel-admin-audio"] });
    queryClient.invalidateQueries({ queryKey: ["vizu-multilevel-admin-hoeren-content"] });
  };

  const createMutation = useMutation({
    mutationFn: (url: string) =>
      createVizuMultilevelAudio({ title: `Aufgabe ${task.order_index} Audio`, audio_url: url, task_id: task.id }),
    onSuccess: invalidate,
  });

  const replaceMutation = useMutation({
    mutationFn: (url: string) => updateVizuMultilevelAudio(audio!.id, { audio_url: url }),
    onSuccess: invalidate,
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteVizuMultilevelAudio(audio!.id),
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
