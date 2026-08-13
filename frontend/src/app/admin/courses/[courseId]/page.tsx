"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Check, Lock, Minus, Pencil, Settings2 } from "lucide-react";

import { AdminButton, AdminInput, AdminLabel, AdminPageHeader } from "@/components/admin/admin-ui";
import FormDialog from "@/components/admin/form-dialog";
import { useCrudList, useCrudMutations } from "@/features/admin/hooks/use-crud";
import {
  getLessonsContentStatus,
  lessonsApi,
  type LessonContentStatus,
} from "@/features/admin/services/lessons-service";
import { levelsApi } from "@/features/admin/services/levels-service";
import { modulesApi } from "@/features/admin/services/modules-service";

const PANELS: { key: keyof LessonContentStatus; label: string }[] = [
  { key: "has_video", label: "Video" },
  { key: "has_grammar", label: "Grammatik" },
  { key: "has_lesen", label: "Lesen" },
  { key: "has_hoeren", label: "Hören" },
  { key: "has_schreiben", label: "Schreiben" },
  { key: "has_sprechen", label: "Sprechen" },
  { key: "has_vocabulary", label: "Wortschatz" },
];

export default function CourseLessonsPage() {
  const { courseId } = useParams<{ courseId: string }>();
  const router = useRouter();

  const { data: courses } = useCrudList("levels", levelsApi);
  const course = courses?.find((c) => c.id === courseId);

  const { data: modules } = useCrudList("modules", modulesApi);
  const module_ = modules?.find((m) => m.course_id === courseId);

  const { data: lessons, isLoading } = useQuery({
    queryKey: ["course-lessons-content-status", module_?.id],
    queryFn: () => getLessonsContentStatus(module_!.id),
    enabled: !!module_,
  });

  const sortedLessons = useMemo(
    () => [...(lessons ?? [])].sort((a, b) => a.number - b.number),
    [lessons],
  );

  // Title-only editing — the lesson's topic/title is the one field this
  // view lets an admin change; content (video, grammar, ...) is still
  // managed on the lesson's own /admin/lessons/{id} page.
  const { update } = useCrudMutations("course-lessons-content-status", lessonsApi);
  const [editing, setEditing] = useState<LessonContentStatus | null>(null);
  const [title, setTitle] = useState("");

  function openEdit(lesson: LessonContentStatus) {
    setEditing(lesson);
    setTitle(lesson.title);
  }

  async function handleSave() {
    if (!editing) return;
    await update.mutateAsync({ id: editing.lesson_id, data: { title } });
    setEditing(null);
  }

  return (
    <div>
      <Link
        href="/admin/courses"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--admin-text-muted)] hover:text-[var(--admin-text-primary)]"
      >
        <ArrowLeft size={14} />
        Courses
      </Link>

      <AdminPageHeader
        title={course ? `${course.level} — ${course.title}` : "Kurs"}
        description={`${sortedLessons.length} Lektionen`}
      />

      {isLoading && (
        <p className="py-10 text-center text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>
      )}

      {!isLoading && module_ && sortedLessons.length === 0 && (
        <div className="rounded-2xl bg-[var(--admin-card)] px-6 py-16 text-center shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-border)]">
          <p className="text-sm text-[var(--admin-text-muted)]">Noch keine Lektionen für dieses Level.</p>
        </div>
      )}

      <div className="space-y-2.5">
        {sortedLessons.map((lesson) => (
          <div
            key={lesson.lesson_id}
            role="button"
            tabIndex={0}
            onClick={() => router.push(`/admin/lessons/${lesson.lesson_id}`)}
            onKeyDown={(e) => {
              if (e.key === "Enter") router.push(`/admin/lessons/${lesson.lesson_id}`);
            }}
            className="flex flex-wrap cursor-pointer items-center justify-between gap-4 rounded-2xl bg-[var(--admin-card)] p-4 shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-border)] transition hover:ring-[var(--admin-primary)]/40"
          >
            <div className="flex items-center gap-3.5">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--admin-primary)]/15 text-xs font-bold text-[var(--admin-primary)]">
                {lesson.number}
              </div>
              <p className="font-medium text-[var(--admin-text-primary)]">{lesson.title}</p>
              <span
                className={`flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
                  lesson.is_locked
                    ? "bg-[var(--admin-warning)]/15 text-[var(--admin-warning)]"
                    : "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]"
                }`}
              >
                {lesson.is_locked ? (
                  <>
                    <Lock size={10} /> Premium
                  </>
                ) : (
                  "Free"
                )}
              </span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  openEdit(lesson);
                }}
                aria-label="Titel bearbeiten"
                className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-[var(--admin-text-muted)] transition hover:bg-[var(--admin-hover)] hover:text-[var(--admin-primary)]"
              >
                <Pencil size={13} />
              </button>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              {PANELS.map((panel) => {
                const done = Boolean(lesson[panel.key]);
                return (
                  <span
                    key={panel.key}
                    className={`flex items-center gap-1 text-xs font-medium ${
                      done ? "text-[var(--admin-accent)]" : "text-[var(--admin-text-muted)]"
                    }`}
                  >
                    {done ? <Check size={12} /> : <Minus size={12} />}
                    {panel.label}
                  </span>
                );
              })}
              <Settings2 size={15} className="shrink-0 text-[var(--admin-text-muted)]" />
            </div>
          </div>
        ))}
      </div>

      <FormDialog
        open={!!editing}
        onOpenChange={(open) => !open && setEditing(null)}
        title="Lektion bearbeiten"
        footer={
          <>
            <AdminButton variant="ghost" onClick={() => setEditing(null)}>
              Abbrechen
            </AdminButton>
            <AdminButton onClick={handleSave} disabled={update.isPending || !title.trim()}>
              {update.isPending ? "Wird gespeichert..." : "Speichern"}
            </AdminButton>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <AdminLabel>Lesson-Nr.</AdminLabel>
            <AdminInput value={editing?.number ?? ""} disabled readOnly />
          </div>

          <div>
            <AdminLabel>Titel</AdminLabel>
            <AdminInput value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Lektionstitel" />
          </div>
        </div>
      </FormDialog>
    </div>
  );
}
