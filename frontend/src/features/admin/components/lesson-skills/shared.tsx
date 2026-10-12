"use client";

import type { ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { getLessonSkillsOverview } from "@/features/admin/services/lesson-skills-admin-service";

export const overviewKey = (lessonId: string) => ["admin-lesson-skills", lessonId];

/** The lesson's Lesen / Hören / Schreiben / Sprechen content incl. answer
 * keys (admin only) — one query shared by every tab of the lesson editor. */
export function useLessonSkillsOverview(lessonId: string) {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: overviewKey(lessonId), queryFn: () => getLessonSkillsOverview(lessonId) });
  const refresh = () => queryClient.invalidateQueries({ queryKey: overviewKey(lessonId) });
  return { ...query, refresh };
}

/** Default Schreiben / Sprechen rubric of the lesson's level (A1-C1) — the
 * server applies it when a task has no own rubric. */
export function useLevelDefaultRubric(lessonId: string | undefined, kind: "writing" | "speaking") {
  const { data } = useQuery({
    queryKey: overviewKey(lessonId ?? ""),
    queryFn: () => getLessonSkillsOverview(lessonId as string),
    enabled: !!lessonId,
  });
  return { level: data?.lesson.level ?? null, rubric: data?.default_rubrics?.[kind] ?? null };
}

export function PublishBadge({ published }: { published: boolean }) {
  return (
    <span
      className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
        published ? "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]" : "bg-white/5 text-[var(--admin-text-muted)]"
      }`}
    >
      {published ? "Veröffentlicht" : "Verborgen"}
    </span>
  );
}

export function ItemCard({ title, meta, badge, actions, children, testId }: {
  title: string;
  meta?: ReactNode;
  badge?: ReactNode;
  actions: ReactNode;
  children?: ReactNode;
  testId?: string;
}) {
  return (
    <div className="space-y-3 rounded-2xl bg-[var(--admin-card)] p-4 shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-border)] sm:p-5" data-testid={testId}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-base font-bold text-[var(--admin-text-primary)]">{title}</h3>
            {badge}
          </div>
          {meta && <div className="mt-1 text-xs text-[var(--admin-text-muted)]">{meta}</div>}
        </div>
        <div className="flex flex-wrap gap-1.5">{actions}</div>
      </div>
      {children}
    </div>
  );
}

/** Plain text (blank line = new paragraph) <-> the simple HTML stored for a
 * Lesen text. The backend sanitizes again (app/core/utils/safe_html.py). */
export function textToHtml(text: string): string {
  const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  return text
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter(Boolean)
    .map((p) => `<p>${esc(p).replace(/\n/g, "<br>")}</p>`)
    .join("");
}

export function htmlToText(html: string): string {
  if (typeof window === "undefined") return html;
  const doc = new DOMParser().parseFromString(
    html.replace(/<br\s*\/?>/gi, "\n").replace(/<\/(p|li|h3|h4|blockquote)>/gi, "\n\n"),
    "text/html",
  );
  return (doc.body.textContent ?? "").replace(/\n{3,}/g, "\n\n").trim();
}
