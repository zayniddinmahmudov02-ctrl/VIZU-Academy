"use client";

import { useRouter } from "next/navigation";
import { Trash2 } from "lucide-react";

import DataTable, { type DataTableColumn } from "./data-table";
import { Badge } from "./badges";
import type { AdminLessonItem, AdminModuleOption } from "../types/lesson";

interface Props {
  lessons: AdminLessonItem[];
  modules: AdminModuleOption[];
  loading: boolean;
  onEdit: (lesson: AdminLessonItem) => void;
  onDelete: (lessonId: string) => void;
}

export default function LessonsTable({ lessons, modules, loading, onEdit, onDelete }: Props) {
  const router = useRouter();
  const moduleTitleById = Object.fromEntries(modules.map((m) => [m.id, m.title]));

  const columns: DataTableColumn<AdminLessonItem>[] = [
    {
      key: "title",
      label: "Lesson",
      render: (lesson) => (
        <div>
          <p className="font-medium text-white">
            {lesson.number}. {lesson.title}
          </p>
          <p className="text-xs text-[var(--admin-text-muted)]">
            {moduleTitleById[lesson.moduleId] ?? lesson.moduleId}
          </p>
        </div>
      ),
    },
    {
      key: "duration",
      label: "Duration",
      render: (lesson) => <span className="text-[var(--admin-text-secondary)]">{lesson.duration} min</span>,
    },
    {
      key: "free",
      label: "Access",
      render: (lesson) => <Badge label={lesson.isFree ? "Free" : "Paid"} tone={lesson.isFree ? "success" : "neutral"} />,
    },
    {
      key: "actions",
      label: "Actions",
      render: (lesson) => (
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => router.push(`/admin/lessons/${lesson.id}`)}
            className="rounded-lg border border-[var(--admin-border)] px-2.5 py-1.5 text-xs font-semibold text-[var(--admin-text-secondary)] transition-colors hover:bg-white/5 hover:text-white"
          >
            Manage Activities
          </button>
          <button
            type="button"
            onClick={() => onEdit(lesson)}
            className="rounded-lg border border-[var(--admin-border)] px-2.5 py-1.5 text-xs font-semibold text-[var(--admin-text-secondary)] transition-colors hover:bg-white/5 hover:text-white"
          >
            Edit
          </button>
          <button
            type="button"
            onClick={() => onDelete(lesson.id)}
            aria-label="Delete lesson"
            className="rounded-lg border border-[var(--admin-border)] p-1.5 text-[var(--admin-text-secondary)] transition-colors hover:border-[var(--admin-danger)]/40 hover:text-[var(--admin-danger)]"
          >
            <Trash2 size={14} />
          </button>
        </div>
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      rows={lessons}
      getRowKey={(lesson) => lesson.id}
      loading={loading}
      emptyLabel="No lessons yet."
      minWidth="720px"
    />
  );
}
