"use client";

import TeacherAssignmentManager from "@/features/admin/components/managers/teacher-assignment-manager";

export default function AdminTeacherAssignmentsPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-[var(--admin-text-primary)]">Lehrer-Zuweisungen</h1>
        <p className="mt-1 text-sm text-[var(--admin-text-secondary)]">
          Legt fest, welche Kurse ein Lehrer im Teacher-Panel sehen darf. Die Rolle TEACHER selbst wird weiterhin
          über Users → Rolle ändern vergeben.
        </p>
      </div>

      <TeacherAssignmentManager />
    </div>
  );
}
