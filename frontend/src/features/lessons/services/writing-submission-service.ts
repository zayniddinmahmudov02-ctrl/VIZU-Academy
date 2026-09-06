import { api } from "@/lib/api";

export interface WritingOwnSubmission {
  id: string;
  writing_id: string;
  answer_text: string;
  status: "DRAFT" | "SUBMITTED" | "GRADED" | "NEEDS_REVISION";
  submitted_at: string | null;
  score: number | null;
  feedback: string | null;
  reviewed_at: string | null;
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
