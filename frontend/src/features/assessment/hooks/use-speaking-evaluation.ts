"use client";

import { useState } from "react";

import { evaluateSpeaking } from "../services/assessment.service";
import type { Evaluation, SpeakingEvaluationRequest } from "../types/assessment";

interface UseSpeakingEvaluationResult {
  result: Evaluation | null;
  loading: boolean;
  /** A translation key (resolve with `t()`), not display text. */
  error: string | null;
  evaluate: (payload: SpeakingEvaluationRequest) => Promise<void>;
  reset: () => void;
}

export function useSpeakingEvaluation(): UseSpeakingEvaluationResult {
  const [result, setResult] = useState<Evaluation | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  async function evaluate(payload: SpeakingEvaluationRequest) {
    try {
      setLoading(true);
      setError(null);

      const data = await evaluateSpeaking(payload);
      setResult(data);
    } catch (err) {
      console.warn("Speaking evaluation failed:", err);
      setError("lessons.writingEvaluationError");
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setResult(null);
    setError(null);
  }

  return { result, loading, error, evaluate, reset };
}
