"use client";

import { useCallback, useState } from "react";

/** Selected answers survive a page reload (the server keeps the timer
 * running either way). Browser storage is best-effort only — every access
 * is guarded because it can be unavailable (private mode, blocked data). */
export function usePersistedAnswers(attemptId: string, skill: string) {
  const key = `vizu-multilevel:${attemptId}:${skill}`;

  const [answers, setAnswersState] = useState<Record<string, string>>(() => {
    try {
      const raw = typeof window === "undefined" ? null : window.localStorage.getItem(key);
      return raw ? (JSON.parse(raw) as Record<string, string>) : {};
    } catch {
      return {};
    }
  });

  const select = useCallback(
    (questionId: string, optionId: string) => {
      setAnswersState((prev) => {
        const next = { ...prev, [questionId]: optionId };
        try {
          window.localStorage.setItem(key, JSON.stringify(next));
        } catch {
          /* storage unavailable — keep in memory only */
        }
        return next;
      });
    },
    [key],
  );

  const clear = useCallback(() => {
    try {
      window.localStorage.removeItem(key);
    } catch {
      /* ignore */
    }
  }, [key]);

  return { answers, select, clear };
}
