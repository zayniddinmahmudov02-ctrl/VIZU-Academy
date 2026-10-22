"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Link2, LoaderCircle, Plus } from "lucide-react";

import { AdminButton, AdminSelect } from "@/components/admin/admin-ui";
import {
  assignA2ListeningSlotTask,
  createA2ListeningSlotTask,
  getA2ListeningOverview,
  type MediaItem,
} from "@/features/admin/services/media-management-service";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";

interface Props {
  lessonNumber: number;
  lessonTasks: MediaItem[];
  onTaskSelected: (taskId: string) => void;
}

export default function A2ListeningSlots({ lessonNumber, lessonTasks, onTaskSelected }: Props) {
  const queryClient = useQueryClient();
  const overview = useQuery({
    queryKey: ["media-mgmt", "a2-listening"],
    queryFn: getA2ListeningOverview,
  });
  const [selectedTasks, setSelectedTasks] = useState<Record<string, string>>({});
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const lesson = overview.data?.lessons.find((item) => item.lesson_number === lessonNumber);

  async function refresh(taskId?: string) {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["media-mgmt", "a2-listening"] }),
      queryClient.invalidateQueries({ queryKey: ["media-mgmt", "items"] }),
    ]);
    if (taskId) onTaskSelected(taskId);
  }

  async function run(key: string, action: () => Promise<{ id: string }>) {
    setBusyKey(key);
    setError(null);
    try {
      const task = await action();
      await refresh(task.id);
    } catch (cause) {
      setError(apiErrorMessage(cause, "Die Hören-Aufgabe konnte nicht eingerichtet werden."));
    } finally {
      setBusyKey(null);
    }
  }

  return (
    <section className="space-y-4 rounded-2xl bg-[var(--admin-card)] p-4 ring-1 ring-[var(--admin-border)] sm:p-5" data-testid="a2-listening-slots">
      <div>
        <h2 className="text-sm font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">A2 Hören — Material-Slots</h2>
        <p className="mt-1 text-xs text-[var(--admin-text-secondary)]">
          Leere Aufgaben werden nur auf ausdrücklichen Klick angelegt. Audio und Aufgabeninhalt werden hier nicht erzeugt.
        </p>
      </div>

      {overview.isPending ? (
        <p role="status" className="text-sm text-[var(--admin-text-muted)]">A2-Material wird geladen …</p>
      ) : overview.isError ? (
        <p role="alert" className="text-sm text-[var(--admin-danger)]">A2-Material konnte nicht geladen werden. Bitte Seite aktualisieren.</p>
      ) : !lesson?.lesson_exists ? (
        <p role="status" className="text-sm text-[var(--admin-warning)]">Diese A2-Lektion ist in der Kursstruktur nicht vorhanden; es wurde nichts angelegt.</p>
      ) : (
        <div className="space-y-3">
          {lesson.expected_materials.map((material) => {
            const task = material.listening;
            const availableTasks = lessonTasks.filter((item) => material.available_task_ids.includes(item.id));
            const selectedTask = selectedTasks[material.key] ?? "";
            return (
              <article key={material.key} className="grid gap-3 rounded-xl border border-[var(--admin-border)] p-3 sm:grid-cols-[minmax(0,1fr)_minmax(220px,auto)] sm:items-center">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-[var(--admin-text-primary)]">
                    {task ? <Check aria-label="Aufgabe zugeordnet" className="mr-1 inline text-[var(--admin-success)]" size={15} /> : null}
                    Material {material.slot_number}: {material.source_name}
                  </p>
                  <p className="mt-1 text-xs text-[var(--admin-text-muted)]">
                    Sollformat: {material.expected_format}
                    {task
                      ? ` · Aufgabe: ${task.title} · ${task.question_count} Fragen${task.key_missing ? ` · ${task.key_missing} Lösungen fehlen` : ""} · ${task.file_status === "ok" ? "Audio vorhanden" : "Audio fehlt"}`
                      : " · Noch keiner Hören-Aufgabe zugeordnet"}
                  </p>
                </div>
                {!task && (
                  <div className="flex flex-wrap gap-2">
                    {availableTasks.length > 0 && (
                      <>
                        <AdminSelect
                          value={selectedTask}
                          onChange={(event) => setSelectedTasks((current) => ({ ...current, [material.key]: event.target.value }))}
                          aria-label={`Vorhandene Hören-Aufgabe für Material ${material.slot_number}`}
                          className="min-w-48"
                        >
                          <option value="">Vorhandene Aufgabe wählen</option>
                          {availableTasks.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}
                        </AdminSelect>
                        <AdminButton
                          size="sm"
                          variant="secondary"
                          disabled={!selectedTask || busyKey !== null}
                          onClick={() => void run(material.key, () => assignA2ListeningSlotTask(material.key, selectedTask))}
                          aria-label={`Aufgabe Material ${material.slot_number} zuordnen`}
                        >
                          {busyKey === material.key ? <LoaderCircle className="animate-spin" size={14} /> : <Link2 size={14} />}
                          Zuordnen
                        </AdminButton>
                      </>
                    )}
                    <AdminButton
                      size="sm"
                      disabled={busyKey !== null}
                      onClick={() => void run(material.key, () => createA2ListeningSlotTask(lessonNumber, material.key))}
                    >
                      {busyKey === material.key ? <LoaderCircle className="animate-spin" size={14} /> : <Plus size={14} />}
                      Leere Aufgabe anlegen
                    </AdminButton>
                  </div>
                )}
              </article>
            );
          })}
          {lesson.expected_materials.length === 0 && (
            <p className="text-sm text-[var(--admin-text-muted)]">Für diese Lektion sind keine Hören-Material-Slots konfiguriert.</p>
          )}
        </div>
      )}
      {error && <p role="alert" className="text-sm text-[var(--admin-danger)]">{error}</p>}
    </section>
  );
}
