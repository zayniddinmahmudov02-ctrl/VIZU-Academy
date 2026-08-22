"use client";

import type { ReactNode } from "react";

import Loading from "@/components/common/loading";
import { SECTION_GATE_KEYS, type LessonSectionMeta } from "@/constants/lesson-sections";
import { useSectionGate } from "@/features/lessons/hooks/use-section-gate";
import { useTranslation } from "@/lib/i18n/use-translation";

import SectionLockedCard from "./section-locked-card";

interface Props {
  lessonId: string;
  meta: LessonSectionMeta;
  children: ReactNode;
}

/** Central, single gate check for every section route — real sequential
 * unlocking (server-computed, see backend/app/services/lesson_progress/
 * section_gate.py) instead of a lock-check duplicated inside each
 * section component. Sections with no gate key (video's own completion
 * still shows via the nav checkmark but nothing sequences before it;
 * homework/results have no completion concept at all) always render
 * their children. */
export default function SectionGateBoundary({ lessonId, meta, children }: Props) {
  const { t } = useTranslation();
  const gateKey = SECTION_GATE_KEYS[meta.type];
  const { data: gate, isLoading } = useSectionGate(lessonId);

  if (!gateKey) {
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
