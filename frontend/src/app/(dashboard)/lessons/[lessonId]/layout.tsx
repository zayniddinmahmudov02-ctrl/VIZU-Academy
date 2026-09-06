"use client";

import { useState } from "react";
import type { ReactNode } from "react";
import { useParams, usePathname } from "next/navigation";
import { Menu } from "lucide-react";

import Drawer from "@/components/ui/drawer";
import ProgressBar from "@/components/ui/progress-bar";
import LessonRightSidebar from "@/components/lesson-player/navigation/lesson-right-sidebar";
import { getSectionBySlug } from "@/constants/lesson-sections";
import { useSectionGate } from "@/features/lessons/hooks/use-section-gate";
import { computeSectionProgress } from "@/features/lessons/utils/section-progress";
import { useTranslation } from "@/lib/i18n/use-translation";

interface Props {
  children: ReactNode;
}

/** The old bottom horizontal LessonSectionNav is gone — all lesson
 * navigation (level -> lesson -> section) now lives in
 * LessonRightSidebar: a sticky panel on desktop/tablet (lg+), a
 * right-side Drawer on mobile (reusing the same Drawer every other
 * mobile overlay in the app already uses, not a new component). The
 * "X/Y abgeschlossen" progress bar the old nav showed is preserved —
 * once inside the sidebar itself, once as a compact mobile-only strip
 * next to the button that opens the drawer — computed via the exact
 * same computeSectionProgress() the sidebar uses, so the two can never
 * disagree. */
export default function LessonLayout({ children }: Props) {
  const { t } = useTranslation();
  const params = useParams<{ lessonId: string }>();
  const pathname = usePathname();
  const [drawerOpen, setDrawerOpen] = useState(false);

  const lessonId = params.lessonId;
  const currentSlug = pathname.split("/").pop() ?? "";
  const isValidSection = Boolean(getSectionBySlug(currentSlug));

  const { data: gate } = useSectionGate(lessonId);
  const progress = computeSectionProgress(gate);

  return (
    <div className="lg:flex lg:items-start lg:gap-6">
      <div className="min-w-0 flex-1">
        {isValidSection && (
          <div className="mb-5 flex items-center gap-3 lg:hidden">
            <button
              type="button"
              onClick={() => setDrawerOpen(true)}
              aria-label={t("header.menuOpen")}
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-surface-card text-text-secondary shadow-[var(--shadow-3d-soft)] ring-1 ring-surface-border transition-all duration-200 hover:-translate-y-px hover:text-accent-blue active:translate-y-0"
            >
              <Menu size={18} />
            </button>

            {progress.total > 0 && (
              <div className="min-w-0 flex-1">
                <div className="mb-1 flex items-center justify-between text-xs">
                  <span className="font-medium text-text-secondary">
                    {t("lessons.navProgress", { completed: progress.completed, total: progress.total })}
                  </span>
                  <span className="font-bold text-accent-blue">{progress.percentage}%</span>
                </div>
                <ProgressBar value={progress.percentage} trackClassName="h-1.5" />
              </div>
            )}
          </div>
        )}

        {children}
      </div>

      {isValidSection && (
        <>
          <aside className="hidden lg:sticky lg:top-4 lg:block lg:max-h-[calc(100vh-2rem)] lg:w-72 lg:shrink-0 lg:overflow-y-auto xl:w-80">
            <LessonRightSidebar lessonId={lessonId} currentSlug={currentSlug} />
          </aside>

          <Drawer open={drawerOpen} onOpenChange={setDrawerOpen} side="right" className="w-[88vw] max-w-sm overflow-y-auto p-4">
            <LessonRightSidebar
              lessonId={lessonId}
              currentSlug={currentSlug}
              onNavigate={() => setDrawerOpen(false)}
            />
          </Drawer>
        </>
      )}
    </div>
  );
}
