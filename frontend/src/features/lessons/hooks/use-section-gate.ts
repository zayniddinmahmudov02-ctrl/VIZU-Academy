"use client";

import { useQuery } from "@tanstack/react-query";

import { getSectionGate } from "../services/section-gate-service";

/** Refetches on window focus (default) plus a short poll while mounted —
 * cheap (one query) and means completing a section (e.g. submitting the
 * Grammatik Quiz in another tab-managed flow) unlocks the next one
 * without the student needing to manually refresh, per the "auto-open
 * next section" requirement. Call `refetch`/invalidate the
 * ["section-gate", lessonId] key right after any completion action for
 * an instant update instead of waiting on the poll. */
export function useSectionGate(lessonId: string) {
  return useQuery({
    queryKey: ["section-gate", lessonId],
    queryFn: () => getSectionGate(lessonId),
    enabled: !!lessonId,
    refetchInterval: 15000,
  });
}
