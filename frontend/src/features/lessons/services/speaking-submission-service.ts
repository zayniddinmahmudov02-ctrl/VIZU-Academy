import { api } from "@/src/services/api";

export interface SpeakingOwnSubmission {
  id: string;
  speaking_id: string;
  filename: string | null;
  content_type: string | null;
  duration_seconds: number | null;
  status: "SUBMITTED" | "GRADED" | "NEEDS_REVISION";
  submitted_at: string | null;
  score: number | null;
  feedback: string | null;
  reviewed_at: string | null;
}

export async function getMySpeakingSubmission(speakingId: string): Promise<SpeakingOwnSubmission | null> {
  const response = await api.get<SpeakingOwnSubmission | null>(`/api/v1/speakings/${speakingId}/submissions/me`);
  return response.data;
}

export async function submitSpeakingRecording(
  speakingId: string,
  file: Blob,
  durationSeconds: number,
  extension: string,
): Promise<SpeakingOwnSubmission> {
  const formData = new FormData();
  formData.append("file", file, `recording.${extension}`);
  formData.append("duration_seconds", String(Math.round(durationSeconds)));
  const response = await api.post<SpeakingOwnSubmission>(
    `/api/v1/speakings/${speakingId}/submissions`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return response.data;
}

// Never a public URL — permission (owner student / assigned teacher /
// admin) is re-checked server-side on every request.
export async function getSpeakingSubmissionAudioBlobUrl(submissionId: string): Promise<string> {
  const response = await api.get(`/api/v1/speakings/submissions/${submissionId}/audio`, {
    responseType: "blob",
  });
  return URL.createObjectURL(response.data as Blob);
}
