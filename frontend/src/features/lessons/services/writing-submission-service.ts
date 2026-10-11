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
