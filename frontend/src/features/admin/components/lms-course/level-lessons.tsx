"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useQueryClient } from "@tanstack/react-query";
import { ArrowDown, ArrowLeft, ArrowUp, Lock, Pencil, Search, Unlock } from "lucide-react";

import { AdminButton, AdminCard, AdminInput, AdminPageHeader, AdminSelect } from "@/components/admin/admin-ui";
import { lmsAdminError, reorderLessons, type AdminLessonCard } from "@/features/admin/services/lms-course-service";

import { adminLmsKeys, useAdminLevelLessons, useCanEditCourses } from "./use-admin-lms";

const PAGE_SIZE = 15;

export function PublishBadge({ published }: { published: boolean }) {
  return published ? (
    <span className="rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-500">Veröffentlicht</span>
  ) : (
    <span className="rounded-full bg-[var(--admin-hover)] px-2.5 py-1 text-xs font-semibold text-[var(--admin-text-muted)]">Entwurf</span>
  );
}

export default function LevelLessons({ level }: { level: string }) {
  const code = level.toUpperCase();
  const canEdit = useCanEditCourses();
  const queryClient = useQueryClient();
  const { data, isLoading, error, refetch } = useAdminLevelLessons(code);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<"all" | "draft" | "published">("all");
  const [page, setPage] = useState(1);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const lessons = useMemo(() => data?.lessons ?? [], [data]);
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return lessons.filter(
      (l) =>
        (filter === "all" || (filter === "published") === l.is_published) &&
        (!q || l.title.toLowerCase().includes(q) || String(l.number) === q || (l.description ?? "").toLowerCase().includes(q)),
    );
  }, [lessons, query, filter]);
  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const current = Math.min(page, pages);
  const shown = filtered.slice((current - 1) * PAGE_SIZE, current * PAGE_SIZE);
  const reorderable = canEdit && !query.trim() && filter === "all";

  async function move(lesson: AdminLessonCard, delta: -1 | 1) {
    const ids = lessons.map((l) => l.id);
    const i = ids.indexOf(lesson.id);
    const j = i + delta;
    if (j < 0 || j >= ids.length) return;
    [ids[i], ids[j]] = [ids[j], ids[i]];
    setBusy(true);
    setMessage(null);
    try {
      await reorderLessons(code, ids);
      await queryClient.invalidateQueries({ queryKey: adminLmsKeys.level(code) });
    } catch (err) {
      setMessage(lmsAdminError(err, "Reihenfolge konnte nicht gespeichert werden."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-5">
      <Link href="/admin/kurse" className="inline-flex items-center gap-1.5 text-sm font-medium text-[var(--admin-text-secondary)] hover:text-[var(--admin-text-primary)]">
        <ArrowLeft size={15} /> Kurse A1–C1
      </Link>
      <AdminPageHeader
        title={`${code} — Lektionen`}
        description={data ? `${data.lessons_existing} von ${data.lessons_target} Lektionen angelegt · ${data.lessons_published} veröffentlicht` : undefined}
      />

      {isLoading && <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>}
      {error ? (
        <AdminCard>
          <p className="text-sm text-[var(--admin-danger)]">{lmsAdminError(error, "Lektionen konnten nicht geladen werden.")}</p>
          <AdminButton variant="secondary" className="mt-3" onClick={() => refetch()}>Erneut versuchen</AdminButton>
        </AdminCard>
      ) : null}

      {data && (
        <>
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative w-full max-w-xs">
              <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--admin-text-muted)]" />
              <AdminInput className="pl-8" value={query} placeholder="Titel oder Nummer suchen…" aria-label="Lektion suchen"
                          onChange={(e) => { setQuery(e.target.value); setPage(1); }} data-testid="admin-lesson-search" />
            </div>
            <AdminSelect value={filter} aria-label="Status" onChange={(e) => { setFilter(e.target.value as typeof filter); setPage(1); }} className="w-44">
              <option value="all">Alle</option>
              <option value="draft">Entwürfe</option>
              <option value="published">Veröffentlicht</option>
            </AdminSelect>
            <span className="text-sm text-[var(--admin-text-muted)]">{filtered.length} Lektionen</span>
            {canEdit && !reorderable && <span className="text-xs text-[var(--admin-text-muted)]">Reihenfolge ändern: Suche und Filter leeren.</span>}
          </div>
          {message && <p className="text-sm text-[var(--admin-danger)]" role="alert">{message}</p>}

          {lessons.length === 0 ? (
            <AdminCard><p className="text-center text-sm text-[var(--admin-text-muted)]">Noch keine Lektionen — unter „Kurse A1–C1“ die Struktur anlegen.</p></AdminCard>
          ) : (
            <div className="overflow-x-auto rounded-2xl bg-[var(--admin-card)] ring-1 ring-[var(--admin-border)]">
              <table className="w-full min-w-[760px] text-left text-sm" data-testid="admin-lesson-table">
                <thead>
                  <tr className="border-b border-[var(--admin-border)] text-xs uppercase tracking-wide text-[var(--admin-text-muted)]">
                    <th className="px-4 py-2.5">#</th>
                    <th className="px-3 py-2.5">Titel</th>
                    <th className="px-3 py-2.5">Status</th>
                    <th className="px-3 py-2.5">Kompetenzen</th>
                    <th className="px-3 py-2.5">Videos</th>
                    <th className="px-3 py-2.5">Materialien</th>
                    <th className="px-3 py-2.5">Zugang</th>
                    <th className="w-32" />
                  </tr>
                </thead>
                <tbody>
                  {shown.map((l) => {
                    const index = lessons.findIndex((x) => x.id === l.id);
                    return (
                      <tr key={l.id} className="border-b border-[var(--admin-border)] last:border-0" data-testid="admin-lesson-row" data-number={l.number}>
                        <td className="px-4 py-2.5 font-semibold text-[var(--admin-text-primary)]">{l.number}</td>
                        <td className="px-3 py-2.5">
                          <p className="font-semibold text-[var(--admin-text-primary)]">{l.title}</p>
                          {l.description && <p className="line-clamp-1 text-xs text-[var(--admin-text-muted)]">{l.description}</p>}
                        </td>
                        <td className="px-3 py-2.5"><PublishBadge published={l.is_published} /></td>
                        <td className="px-3 py-2.5 text-[var(--admin-text-secondary)]">{l.competencies_published} / 10 sichtbar</td>
                        <td className="px-3 py-2.5 text-[var(--admin-text-secondary)]">{l.videos_published} / {l.videos}</td>
                        <td className="px-3 py-2.5 text-[var(--admin-text-secondary)]">{l.resources}</td>
                        <td className="px-3 py-2.5 text-xs">
                          {l.access_override === "LOCKED" ? <span className="inline-flex items-center gap-1 text-amber-500"><Lock size={12} /> gesperrt</span>
                            : l.access_override === "OPEN" ? <span className="inline-flex items-center gap-1 text-emerald-500"><Unlock size={12} /> geöffnet</span>
                            : <span className="text-[var(--admin-text-muted)]">Standard</span>}
                        </td>
                        <td className="px-2 py-2.5 text-right">
                          {reorderable && (
                            <>
                              <AdminButton size="sm" variant="ghost" aria-label="Nach oben" disabled={busy || index === 0} onClick={() => move(l, -1)} data-testid="admin-lesson-up"><ArrowUp size={13} /></AdminButton>
                              <AdminButton size="sm" variant="ghost" aria-label="Nach unten" disabled={busy || index === lessons.length - 1} onClick={() => move(l, 1)}><ArrowDown size={13} /></AdminButton>
                            </>
                          )}
                          <Link href={`/admin/kurse/lektion/${l.id}`} aria-label="Bearbeiten" data-testid="admin-lesson-edit"
                                className="ml-1 inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-[var(--admin-primary)] hover:bg-[var(--admin-hover)]">
                            <Pencil size={13} /> {canEdit ? "Bearbeiten" : "Ansehen"}
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {pages > 1 && (
            <div className="flex items-center justify-center gap-2 text-sm" data-testid="admin-lesson-pagination">
              <AdminButton size="sm" variant="secondary" disabled={current === 1} onClick={() => setPage(current - 1)}>Zurück</AdminButton>
              <span className="text-[var(--admin-text-secondary)]">Seite {current} / {pages}</span>
              <AdminButton size="sm" variant="secondary" disabled={current === pages} onClick={() => setPage(current + 1)}>Weiter</AdminButton>
            </div>
          )}
        </>
      )}
    </div>
  );
}
