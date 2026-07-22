import { api } from "@/services/api";

import type {
  Evaluation,
  SpeakingEvaluationRequest,
  WritingEvaluationRequest,
} from "../types/assessment";

/**
 * AI evaluation endpoints.
 *
 * BACKEND TODO: these routes do not exist yet. `AIWritingService.check(text)`
 * (app/services/ai/writing/service.py) exists but is not wired to a router and
 * returns raw model text. A structured endpoint must be added, e.g.
 *   POST /writings/evaluate  -> Evaluation (JSON)
 *   POST /speakings/evaluate -> Evaluation (JSON)
 * matching the existing `/writings` router prefix.
 */
const ENDPOINTS = {
  writing: "/writings/evaluate",
  speaking: "/speakings/evaluate",
} as const;

export async function evaluateWriting(
  payload: WritingEvaluationRequest,
): Promise<Evaluation> {
  const response = await api.post<Evaluation>(ENDPOINTS.writing, payload);
  return response.data;
}

export async function evaluateSpeaking(
  payload: SpeakingEvaluationRequest,
): Promise<Evaluation> {
  const response = await api.post<Evaluation>(ENDPOINTS.speaking, payload);
  return response.data;
}
