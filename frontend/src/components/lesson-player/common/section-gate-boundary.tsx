"use client";

import type { ReactNode } from "react";

import Loading from "@/components/common/loading";
import { SECTION_GATE_KEYS, getSectionBySlug } from "@/constants/lesson-sections";
import { useSectionGate } from "@/features/lessons/hooks/use-section-gate";
import { useTranslation } from "@/lib/i18n/use-translation";

import SectionLockedCard from "./section-locked-card";

interface Props {
  lessonId: string;
  /** The URL slug only — not the LessonSectionMeta object itself. That
   * object's `icon` field is a component reference (a function), and
   * this component is rendered from a Server Component parent
   * (app/(dashboard)/lessons/[lessonId]/[section]/page.tsx); a function
   * can't cross the server->client props boundary ("Functions cannot be
   * passed directly to Client Components..."). lesson-sections.ts is a
   * plain module with no "use client"/"use server" of its own, so this
   * Client Component looks the meta up for itself from the one
   * serializable field (the slug) instead of receiving it as a prop. */
  slug: string;
  children: ReactNode;
}

/** Central, single gate check for every section route — real sequential
 * unlocking (server-computed, see backend/app/services/lesson_progress/
 * section_gate.py) instead of a lock-check duplicated inside each
 * section component. Sections with no gate key (video's own completion
 * still shows via the nav checkmark but nothing sequences before it;
 * homework/results have no completion concept at all) always render
 * their children. */
export default function SectionGateBoundary({ lessonId, slug, children }: Props) {
  const { t } = useTranslation();
  const meta = getSectionBySlug(slug);
  const gateKey = meta ? SECTION_GATE_KEYS[meta.type] : null;
  const { data: gate, isLoading } = useSectionGate(lessonId);

  if (!meta || !gateKey) {
    return <>{children}</>;
  }

  if (isLoading || !gate) {
    return <Loading />;
  }

  if (!gate[gateKey].unlocked) {
    return <SectionLockedCard title={t(meta.titleKey)} icon={meta.icon} />;
  }

  return <>{children}</>;
}
