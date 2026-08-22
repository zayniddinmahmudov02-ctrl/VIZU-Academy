"use client";

import { Lock } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import LessonSection from "./lesson-section";

interface Props {
  title: string;
  icon: LucideIcon;
}

/** Shared locked-section view — one card, reused by SectionGateBoundary
 * for every gated section instead of each section component building
 * its own (this pattern was originally built inline in
 * vocabulary-quiz-section.tsx; generalized here so it isn't duplicated
 * per section). The real, unbypassable gate is always server-side (see
 * backend/app/services/lesson_progress/section_gate.py and its call
 * sites in grading_service.py / attempt_service.py / writing_service.py
 * / speaking_service.py) — this card is UX only. */
export default function SectionLockedCard({ title, icon }: Props) {
  return (
    <LessonSection title={title} description="Gesperrt" icon={icon}>
      <div className="rounded-2xl bg-surface-hover p-8 text-center ring-1 ring-surface-border">
        <Lock className="mx-auto text-text-muted" size={28} />
        <p className="mt-3 text-sm font-medium text-text-primary">
          🔒 {title} — Schließe zuerst den vorherigen Abschnitt ab.
        </p>
      </div>
    </LessonSection>
  );
}
