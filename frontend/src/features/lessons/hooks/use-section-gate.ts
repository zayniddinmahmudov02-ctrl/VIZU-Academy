"use client";

import { useQuery } from "@tanstack/react-query";

import { getSectionGate } from "../services/section-gate-service";

/** Per-section completion state for progress checkmarks (nav, results,
 * admin per-student view) — sections are independently accessible, this
 * is display-only. Refetches on window focus (default) plus a short poll
 * while mounted so a completion made in another tab shows up here too.
 * Call `refetch`/invalidate the ["section-gate", lessonId] key right
 * after any completion action for an instant update instead of waiting
 * on the poll. */
export function useSectionGate(lessonId: string) {
  return useQuery({
    queryKey: ["section-gate", lessonId],
    queryFn: () => getSectionGate(lessonId),
    enabled: !!lessonId,
    refetchInterval: 15000,
  });
}
