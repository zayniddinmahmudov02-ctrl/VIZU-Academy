"use client";

import { Pencil, Trash2 } from "lucide-react";

import DataTable, { type DataTableColumn } from "./data-table";
import { Badge } from "./badges";
import type { AdminCourseItem } from "../types/course";

interface Props {
  courses: AdminCourseItem[];
  loading: boolean;
  onEdit: (course: AdminCourseItem) => void;
  onToggleActive: (course: AdminCourseItem) => void;
  onDelete: (courseId: string) => void;
}

export default function CoursesTable({ courses, loading, onEdit, onToggleActive, onDelete }: Props) {
  const columns: DataTableColumn<AdminCourseItem>[] = [
    {
      key: "title",
      label: "Title",
      render: (course) => (
        <div>
          <p className="font-medium text-white">{course.title}</p>
          {course.description && (
            <p className="max-w-xs truncate text-xs text-[var(--admin-text-muted)]">{course.description}</p>
          )}
        </div>
      ),
    },
    {
      key: "level",
      label: "Level",
      render: (course) => <span className="text-[var(--admin-text-secondary)]">{course.level}</span>,
    },
    {
      key: "language",
      label: "Language",
      render: (course) => (
        <span className="font-mono text-xs text-[var(--admin-text-secondary)]">{course.languageId || "Unknown"}</span>
      ),
    },
    {
      key: "order",
      label: "Order",
      render: (course) => <span className="text-[var(--admin-text-secondary)]">{course.orderIndex}</span>,
    },
    {
      key: "status",
      label: "Status",
      render: (course) => (
        <button type="button" onClick={() => onToggleActive(course)}>
          <Badge label={course.isActive ? "Active" : "Inactive"} tone={course.isActive ? "success" : "neutral"} />
        </button>
      ),
    },
    {
      key: "actions",
      label: "Actions",
      render: (course) => (
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onEdit(course)}
            aria-label="Edit course"
            className="rounded-lg border border-[var(--admin-border)] p-1.5 text-[var(--admin-text-secondary)] transition-colors hover:bg-white/5 hover:text-white"
          >
            <Pencil size={14} />
          </button>
          <button
            type="button"
            onClick={() => onDelete(course.id)}
            aria-label="Delete course"
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
      rows={courses}
      getRowKey={(course) => course.id}
      loading={loading}
      emptyLabel="No courses yet."
      minWidth="760px"
    />
  );
}
