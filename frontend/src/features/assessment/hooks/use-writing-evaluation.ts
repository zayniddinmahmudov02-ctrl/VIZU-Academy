"use client";

import { useState } from "react";

import { evaluateWriting } from "../services/assessment.service";
import type { Evaluation, WritingEvaluationRequest } from "../types/assessment";

interface UseWritingEvaluationResult {
  result: Evaluation | null;
  loading: boolean;
  /** A translation key (resolve with `t()`), not display text. */
  error: string | null;
  evaluate: (payload: WritingEvaluationRequest) => Promise<void>;
  reset: () => void;
}

export function useWritingEvaluation(): UseWritingEvaluationResult {
  const [result, setResult] = useState<Evaluation | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  async function evaluate(payload: WritingEvaluationRequest) {
    try {
      setLoading(true);
      setError(null);

      const data = await evaluateWriting(payload);
      setResult(data);
    } catch (err) {
      console.warn("Writing evaluation failed:", err);
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
