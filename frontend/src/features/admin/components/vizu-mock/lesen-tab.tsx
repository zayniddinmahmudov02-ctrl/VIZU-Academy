"use client";

import { useQuery } from "@tanstack/react-query";
import { BookOpen, Loader2 } from "lucide-react";

import { AdminCard } from "@/components/admin/admin-ui";
import AdminEmptySection from "@/components/admin/admin-empty-section";
import { getVizuMockLesenContent } from "@/features/admin/services/vizu-mock-admin-service";

export default function VizuMockLesenTab() {
  const { data: tasks, isLoading } = useQuery({
    queryKey: ["vizu-mock-admin-lesen-content"],
    queryFn: getVizuMockLesenContent,
  });

  if (isLoading) {
    return (
      <div className="flex h-40 items-center justify-center">
        <Loader2 size={22} className="animate-spin text-[var(--admin-primary)]" />
      </div>
    );
  }

  if (!tasks || tasks.length === 0) {
    return (
      <AdminEmptySection
        icon={BookOpen}
        title="Noch kein Lesen-Inhalt vorhanden"
        description="Für Lesen wurden noch keine Aufgaben angelegt."
      />
    );
  }

  return (
    <div>
      <p className="mb-4 text-sm text-[var(--admin-text-secondary)]">
        Schreibgeschützte Übersicht der bereits eingepflegten Lesen-Aufgaben ({tasks.length} Aufgaben). Inhalte werden
        in einer späteren Phase separat gepflegt.
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
    </div>
  );
}
