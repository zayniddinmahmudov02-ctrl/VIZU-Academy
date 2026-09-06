"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { AdminButton, AdminSelect } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import { levelsApi } from "@/features/admin/services/levels-service";
import { teacherAssignmentsApi } from "@/features/admin/services/teacher-assignments-service";
import type { TeacherAssignment } from "@/features/admin/types/teacher.types";

const QUERY_KEY = ["admin-teacher-assignments"];
const CANDIDATES_KEY = ["admin-teacher-assignment-candidates"];
const COURSES_KEY = ["admin-teacher-assignment-courses"];

/** Assigns a TEACHER-role user to a course — the Teacher Panel's "Meine
 * Schüler" list (GET /teacher/students) is scoped to exactly these rows
 * (see backend/app/models/teacher_assignment.py). A user first becomes a
 * TEACHER via the existing Users page's "Rolle ändern" (that already
 * lists TEACHER as an option — nothing new needed there); this page is
 * only the second step, picking which course(s) they can see students
 * for. */
export default function TeacherAssignmentManager() {
  const queryClient = useQueryClient();
  const [teacherId, setTeacherId] = useState("");
  const [courseId, setCourseId] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [pendingDelete, setPendingDelete] = useState<TeacherAssignment | null>(null);

  const { data: assignments, isLoading } = useQuery({ queryKey: QUERY_KEY, queryFn: teacherAssignmentsApi.list });
  const { data: candidates } = useQuery({ queryKey: CANDIDATES_KEY, queryFn: teacherAssignmentsApi.listCandidates });
  const { data: courses } = useQuery({ queryKey: COURSES_KEY, queryFn: () => levelsApi.list() });

  const createMutation = useMutation({
    mutationFn: () => teacherAssignmentsApi.create(teacherId, courseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
      setTeacherId("");
      setCourseId("");
      setFormError(null);
    },
    onError: (err: unknown) => {
      const message =
        err && typeof err === "object" && "response" in err
          ? // Axios error shape — surface the backend's own message
            // (e.g. "already assigned") instead of a generic failure.
            (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      setFormError(message ?? "Zuweisung fehlgeschlagen.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => teacherAssignmentsApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
      setPendingDelete(null);
    },
  });

  const columns: DataTableColumn<TeacherAssignment>[] = [
    { key: "teacher", header: "Lehrer", render: (a) => `${a.teacher_name} (${a.teacher_email})` },
    { key: "course", header: "Kurs", render: (a) => `${a.course_level} — ${a.course_title}` },
  ];

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-[var(--admin-card)] p-5 shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-border)]">
        <h2 className="text-sm font-bold text-[var(--admin-text-primary)]">Neue Zuweisung</h2>
        <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="flex-1">
            <AdminSelect value={teacherId} onChange={(e) => setTeacherId(e.target.value)}>
              <option value="">Lehrer wählen…</option>
              {candidates?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.email})
                </option>
              ))}
            </AdminSelect>
          </div>
          <div className="flex-1">
            <AdminSelect value={courseId} onChange={(e) => setCourseId(e.target.value)}>
              <option value="">Kurs wählen…</option>
              {courses?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.level} — {c.title}
                </option>
              ))}
            </AdminSelect>
          </div>
          <AdminButton
            disabled={!teacherId || !courseId || createMutation.isPending}
            onClick={() => createMutation.mutate()}
          >
            {createMutation.isPending ? "Wird zugewiesen..." : "Zuweisen"}
          </AdminButton>
        </div>
        {(!candidates || candidates.length === 0) && (
          <p className="mt-2 text-xs text-[var(--admin-text-muted)]">
            Kein Nutzer hat aktuell die Rolle TEACHER — weise sie zuerst über Users → Rolle ändern zu.
          </p>
        )}
        {formError && <p className="mt-2 text-xs text-[var(--admin-danger)]">{formError}</p>}
      </div>

      <DataTable
        columns={columns}
        data={assignments}
        isLoading={isLoading}
        getRowId={(a) => a.id}
        onDelete={(a) => setPendingDelete(a)}
        emptyMessage="Noch keine Zuweisungen."
      />

      <ConfirmDialog
        open={!!pendingDelete}
        onOpenChange={(open) => !open && setPendingDelete(null)}
        title="Zuweisung entfernen"
        description={
          pendingDelete
            ? `${pendingDelete.teacher_name} verliert den Zugriff auf die Schüler von "${pendingDelete.course_title}".`
            : ""
        }
        onConfirm={() => pendingDelete && deleteMutation.mutate(pendingDelete.id)}
        isPending={deleteMutation.isPending}
      />
    </div>
  );
}
