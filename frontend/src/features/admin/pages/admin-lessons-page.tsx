"use client";

import { useState } from "react";
import { GraduationCap } from "lucide-react";

import { useAdminLessons } from "../hooks/use-admin-lessons";
import AdminModal from "../components/admin-modal";
import LessonsTable from "../components/lessons-table";
import type { AdminLessonItem } from "../types/lesson";

const inputClass =
  "w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50";

export default function AdminLessonsPage() {
  const lessons = useAdminLessons();

  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const [moduleId, setModuleId] = useState("");
  const [number, setNumber] = useState("1");
  const [title, setTitle] = useState("");
  const [duration, setDuration] = useState("10");
  const [isFree, setIsFree] = useState(false);

  function resetForm() {
    setEditingId(null);
    setModuleId("");
    setNumber("1");
    setTitle("");
    setDuration("10");
    setIsFree(false);
  }

  function openCreate() {
    resetForm();
    setModalOpen(true);
  }

  function openEdit(lesson: AdminLessonItem) {
    setEditingId(lesson.id);
    setModuleId(lesson.moduleId);
    setNumber(String(lesson.number));
    setTitle(lesson.title);
    setDuration(String(lesson.duration));
    setIsFree(lesson.isFree);
    setModalOpen(true);
  }

  async function handleSave() {
    if (!moduleId || !title.trim() || !number) return;

    const input = {
      moduleId,
      number: Number(number),
      title: title.trim(),
      duration: Number(duration) || 0,
      isFree,
    };

    if (editingId) {
      await lessons.update(editingId, input);
    } else {
      await lessons.create(input);
    }

    setModalOpen(false);
    resetForm();
  }

  async function handleDelete(lessonId: string) {
    if (!window.confirm("Delete this lesson? This also removes its video, vocabulary, grammar, and every other activity attached to it.")) return;
    await lessons.remove(lessonId);
  }

  const canSave = Boolean(moduleId && title.trim() && number);

  return (
    <div className="space-y-6">
      <div className="admin-glass flex flex-wrap items-center justify-between gap-4 rounded-2xl p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--admin-primary)] to-[var(--admin-secondary)] text-white">
            <GraduationCap size={20} />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">Lessons</h1>
            <p className="text-xs text-[var(--admin-text-muted)]">{lessons.data?.length ?? 0} lessons</p>
          </div>
        </div>
        <button
          type="button"
          onClick={openCreate}
          className="rounded-xl bg-[var(--admin-primary)] px-4 py-2.5 text-xs font-semibold text-white"
        >
          + New Lesson
        </button>
      </div>

      <LessonsTable
        lessons={lessons.data ?? []}
        modules={lessons.modules}
        loading={lessons.loading}
        onEdit={openEdit}
        onDelete={handleDelete}
      />

      <AdminModal
        open={modalOpen}
        onOpenChange={(open) => {
          setModalOpen(open);
          if (!open) resetForm();
        }}
        title={editingId ? "Edit Lesson" : "New Lesson"}
      >
        <div className="space-y-3">
          <select
            value={moduleId}
            onChange={(event) => setModuleId(event.target.value)}
            disabled={lessons.modulesLoading}
            className={inputClass}
          >
            <option value="" className="bg-[#111827]">
              {lessons.modulesLoading ? "Loading modules…" : "Select module"}
            </option>
            {lessons.modules.map((module) => (
              <option key={module.id} value={module.id} className="bg-[#111827]">
                {module.title}
              </option>
            ))}
          </select>

          <div className="flex gap-2">
            <input
              type="number"
              min={1}
              value={number}
              onChange={(event) => setNumber(event.target.value)}
              placeholder="Number"
              className={inputClass}
            />
            <input
              type="number"
              min={0}
              value={duration}
              onChange={(event) => setDuration(event.target.value)}
              placeholder="Duration (min)"
              className={inputClass}
            />
          </div>

          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Title"
            className={inputClass}
          />

          <label className="flex items-center gap-2 text-sm text-[var(--admin-text-secondary)]">
            <input
              type="checkbox"
              checked={isFree}
              onChange={(event) => setIsFree(event.target.checked)}
              className="h-4 w-4 rounded border-[var(--admin-border)] accent-[var(--admin-primary)]"
            />
            Free preview lesson
          </label>

          {lessons.saveError && <p className="text-xs text-[#ef4444]">{lessons.saveError}</p>}

          <button
            type="button"
            onClick={handleSave}
            disabled={!canSave || lessons.saving}
            className="w-full rounded-xl bg-[var(--admin-primary)] py-2.5 text-sm font-semibold text-white disabled:opacity-40"
          >
            {lessons.saving ? "Saving…" : editingId ? "Save Changes" : "Create Lesson"}
          </button>
        </div>
      </AdminModal>
    </div>
  );
}
