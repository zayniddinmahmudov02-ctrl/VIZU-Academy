"use client";

import { useState } from "react";
import { isAxiosError } from "axios";
import { BookOpen } from "lucide-react";

import { useAdminCourses } from "../hooks/use-admin-courses";
import AdminModal from "../components/admin-modal";
import CoursesTable from "../components/courses-table";
import type { AdminCourseItem } from "../types/course";

export default function AdminCoursesPage() {
  const courses = useAdminCourses();

  const [modalOpen, setModalOpen] = useState(false);
  const [editingCourse, setEditingCourse] = useState<AdminCourseItem | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const [languageId, setLanguageId] = useState("");
  const [level, setLevel] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [orderIndex, setOrderIndex] = useState("1");
  const [isActive, setIsActive] = useState(true);

  function resetForm() {
    setLanguageId("");
    setLevel("");
    setTitle("");
    setDescription("");
    setOrderIndex("1");
    setIsActive(true);
    setFormError(null);
    setEditingCourse(null);
  }

  function openCreateModal() {
    resetForm();
    setModalOpen(true);
  }

  function openEditModal(course: AdminCourseItem) {
    setEditingCourse(course);
    setLanguageId(course.languageId);
    setLevel(course.level);
    setTitle(course.title);
    setDescription(course.description ?? "");
    setOrderIndex(String(course.orderIndex));
    setIsActive(course.isActive);
    setFormError(null);
    setModalOpen(true);
  }

  async function handleSubmit() {
    if (!languageId.trim() || !level.trim() || !title.trim()) return;
    setFormError(null);

    try {
      if (editingCourse) {
        await courses.update(editingCourse.id, {
          languageId: languageId.trim(),
          level: level.trim(),
          title: title.trim(),
          description: description.trim() || undefined,
          orderIndex: Number(orderIndex) || 1,
          isActive,
        });
      } else {
        await courses.create({
          languageId: languageId.trim(),
          level: level.trim(),
          title: title.trim(),
          description: description.trim() || undefined,
          orderIndex: Number(orderIndex) || 1,
          isActive,
        });
      }
      setModalOpen(false);
      resetForm();
    } catch (err) {
      const message = isAxiosError<{ message?: string }>(err)
        ? err.response?.data?.message
        : undefined;
      setFormError(message ?? "Failed to save course.");
    }
  }

  async function handleToggleActive(course: AdminCourseItem) {
    await courses.update(course.id, { isActive: !course.isActive });
  }

  async function handleDelete(courseId: string) {
    if (!window.confirm("Delete this course? This also removes its modules.")) return;
    await courses.remove(courseId);
  }

  return (
    <div className="space-y-6">
      <div className="admin-glass flex flex-wrap items-center justify-between gap-4 rounded-2xl p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--admin-primary)] to-[var(--admin-secondary)] text-white">
            <BookOpen size={20} />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">Courses</h1>
            <p className="text-xs text-[var(--admin-text-muted)]">{courses.data?.length ?? 0} courses</p>
          </div>
        </div>
        <button
          type="button"
          onClick={openCreateModal}
          className="rounded-xl bg-[var(--admin-primary)] px-4 py-2.5 text-xs font-semibold text-white"
        >
          + New Course
        </button>
      </div>

      <CoursesTable
        courses={courses.data ?? []}
        loading={courses.loading}
        onEdit={openEditModal}
        onToggleActive={handleToggleActive}
        onDelete={handleDelete}
      />

      <AdminModal
        open={modalOpen}
        onOpenChange={(open) => {
          setModalOpen(open);
          if (!open) resetForm();
        }}
        title={editingCourse ? "Edit Course" : "New Course"}
      >
        <div className="space-y-3">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Title"
            className="w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
          />
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description (optional)"
            rows={3}
            className="w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
          />
          <div className="flex gap-2">
            <input
              value={languageId}
              onChange={(e) => setLanguageId(e.target.value)}
              placeholder="Language ID"
              className="w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
            />
            <input
              value={level}
              onChange={(e) => setLevel(e.target.value)}
              placeholder="Level (e.g. A1)"
              className="w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              type="number"
              min={1}
              value={orderIndex}
              onChange={(e) => setOrderIndex(e.target.value)}
              placeholder="Order"
              className="w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
            />
            <label className="flex shrink-0 items-center gap-2 whitespace-nowrap rounded-xl border border-[var(--admin-border)] bg-white/[0.03] px-3 py-3 text-sm text-[var(--admin-text-secondary)]">
              <input
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                className="h-4 w-4 rounded border-[var(--admin-border)]"
              />
              Active
            </label>
          </div>

          {formError && <p className="text-xs text-[#ef4444]">{formError}</p>}

          <button
            type="button"
            onClick={handleSubmit}
            disabled={!languageId.trim() || !level.trim() || !title.trim() || courses.creating}
            className="w-full rounded-xl bg-[var(--admin-primary)] py-2.5 text-sm font-semibold text-white disabled:opacity-40"
          >
            {editingCourse ? "Save Changes" : "Create Course"}
          </button>
        </div>
      </AdminModal>
    </div>
  );
}
