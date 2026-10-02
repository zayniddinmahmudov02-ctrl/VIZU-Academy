"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { nextStepPath, stepPath } from "../constants/skills";
import { getVizuMultilevelAttemptState, startVizuMultilevelSection } from "../services/vizu-multilevel-service";
import type { VizuMultilevelSkill } from "../types/vizu-multilevel.types";

export type SectionGate =
  | { status: "loading" }
  | { status: "ready"; secondsRemaining: number }
  | { status: "error" };

/** Like SectionGate, plus "submitted" (only from useVizuMultilevelSectionOrSubmitted). */
export type SectionGateOrSubmitted = SectionGate | { status: "submitted" };

/** Opens a competency on the SERVER: stamps its 20-minute window once and
 * returns the seconds left, computed by the backend's clock. A reload gets
 * the same deadline back (never a fresh timer). If the competency was
 * already finished, or an earlier one is still open, the student is sent
 * to the step they actually belong on. */
export function useVizuMultilevelSection(attemptId: string, skill: VizuMultilevelSkill): SectionGate {
  return useSectionGate(attemptId, skill, false) as SectionGate;
}

/** Same, but a competency that is already submitted stays on its page
 * (status "submitted") instead of redirecting — used by Schreiben to show
 * its evaluation/result after a reload. */
export function useVizuMultilevelSectionOrSubmitted(attemptId: string, skill: VizuMultilevelSkill): SectionGateOrSubmitted {
  return useSectionGate(attemptId, skill, true);
}

function useSectionGate(attemptId: string, skill: VizuMultilevelSkill, stayIfSubmitted: boolean): SectionGateOrSubmitted {
  const router = useRouter();
  const [gate, setGate] = useState<SectionGateOrSubmitted>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;

    async function open() {
      try {
        const section = await startVizuMultilevelSection(attemptId, skill);
        if (cancelled) return;
        if (section.submitted) {
          if (stayIfSubmitted) {
            setGate({ status: "submitted" });
            return;
          }
          router.replace(nextStepPath(attemptId, skill));
          return;
        }
        setGate({ status: "ready", secondsRemaining: section.seconds_remaining ?? section.duration_seconds });
      } catch (error) {
        if (cancelled) return;
        const status = (error as { response?: { status?: number } }).response?.status;
        if (status === 409) {
          try {
            const state = await getVizuMultilevelAttemptState(attemptId);
            if (cancelled) return;
            router.replace(stepPath(attemptId, state.next_skill ?? "natijalar"));
            return;
          } catch {
            /* fall through to the error state */
          }
        }
        if (!cancelled) setGate({ status: "error" });
      }
    }

    void open();
    return () => {
      cancelled = true;
    };
  }, [attemptId, skill, router, stayIfSubmitted]);

  return gate;
}

/** True for an HTTP 409 (flow violation: already submitted / time up). */
export function isConflict(error: unknown): boolean {
  return (error as { response?: { status?: number } }).response?.status === 409;
}

/** The machine-readable code of a 409 flow error (e.g. MIN_ANSWERS_REQUIRED). */
export function apiErrorCode(error: unknown): string | undefined {
  const message = (error as { response?: { data?: { message?: unknown } } }).response?.data?.message;
  return typeof message === "string" ? message : undefined;
}

/** Minimum answered items per competency: 5, or all if there are fewer. */
export function minAnswersRequired(total: number): number {
  return Math.min(5, Math.max(total, 0));
}
