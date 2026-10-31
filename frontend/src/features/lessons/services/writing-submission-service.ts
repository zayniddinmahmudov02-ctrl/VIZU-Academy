import type { AiEvaluationResult } from "@/components/lesson-player/common/ai-evaluation-card";
import { api } from "@/lib/api";

export interface WritingOwnSubmission {
  id: string;
  writing_id: string;
  answer_text: string;
  status: "DRAFT" | "SUBMITTED" | "EVALUATING" | "GRADED" | "EVALUATION_FAILED" | "NEEDS_REVISION";
  submitted_at: string | null;
  score: number | null;
  feedback: string | null;
  reviewed_at: string | null;
  attempt_count?: number;
  ai_score?: number | null;
  evaluated_at?: string | null;
  ai_evaluation?: AiEvaluationResult | null;
  /** a teacher / admin confirmed or corrected the result */
  teacher_reviewed?: boolean;
}

export interface WritingEvaluationRun {
  id: string;
  source: "AI" | "MANUAL_OVERRIDE";
  status: "SUCCEEDED" | "FAILED";
  score: number | null;
  result: AiEvaluationResult | null;
  reason: string | null;
  error: string | null;
  created_at: string;
}

export interface WritingVersion {
  attempt_number: number;
  answer_text: string;
  word_count: number;
  submitted_at: string;
  evaluations: WritingEvaluationRun[];
}

/** Every version the student submitted (exact text), newest first, with each analysis / teacher decision. */
export async function getMyWritingHistory(writingId: string): Promise<{ versions: WritingVersion[] }> {
  return api<{ versions: WritingVersion[] }>(`/api/v1/writings/${writingId}/submissions/me/history`);
}

export async function getMyWritingSubmission(writingId: string): Promise<WritingOwnSubmission | null> {
  return api<WritingOwnSubmission | null>(`/api/v1/writings/${writingId}/submissions/me`);
}

export async function submitWriting(
  writingId: string,
  answerText: string,
  submitFinal: boolean,
): Promise<WritingOwnSubmission> {
  return api<WritingOwnSubmission>(`/api/v1/writings/${writingId}/submissions`, {
    method: "POST",
    body: JSON.stringify({ answer_text: answerText, submit: submitFinal }),
  });
}

/** Retry after EVALUATION_FAILED (the text is kept on the server). */
export async function retryWritingEvaluation(writingId: string): Promise<WritingOwnSubmission> {
  return api<WritingOwnSubmission>(`/api/v1/writings/${writingId}/submissions/me/evaluate`, { method: "POST" });
}
