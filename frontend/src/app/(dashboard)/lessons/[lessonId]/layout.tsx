"use client";

import { useEffect } from "react";
import type { ReactNode } from "react";
import { useParams, usePathname } from "next/navigation";

import LessonSectionNav from "@/components/lesson-player/navigation/lesson-section-nav";
import { getSectionBySlug } from "@/constants/lesson-sections";
import { useLessonProgressStore } from "@/store/lesson-progress-store";

interface Props {
  children: ReactNode;
}

export default function LessonLayout({ children }: Props) {
  const params = useParams<{ lessonId: string }>();
  const pathname = usePathname();

  useEffect(() => {
    useLessonProgressStore.persist.rehydrate();
  }, []);

  const lessonId = params.lessonId;
  const currentSlug = pathname.split("/").pop() ?? "";
  const isValidSection = Boolean(getSectionBySlug(currentSlug));

  return (
    <div className="space-y-8">
      {children}

      {isValidSection && <LessonSectionNav lessonId={lessonId} currentSlug={currentSlug} />}
    </div>
  );
}
