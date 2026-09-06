import { api } from "@/lib/api";

export interface LessonHomework {
  id: string;
  lesson_id: string;
  title: string;
  description: string;
  max_score: number;
  is_published: boolean;
}

export interface HomeworkSubmission {
  id: string;
  homework_id: string;
  text_content: string;
  status: "SUBMITTED" | "GRADED" | "NEEDS_REVISION";
  submitted_at: string;
  score: number | null;
  feedback: string | null;
  reviewed_at: string | null;
}

export async function getLessonHomework(lessonId: string): Promise<LessonHomework[]> {
  return api<LessonHomework[]>(`/api/v1/homeworks/lesson/${lessonId}`);
}

export async function getMyHomeworkSubmission(homeworkId: string): Promise<HomeworkSubmission | null> {
  return api<HomeworkSubmission | null>(`/api/v1/homeworks/${homeworkId}/submissions/me`);
}

export async function submitHomework(homeworkId: string, textContent: string): Promise<HomeworkSubmission> {
  return api<HomeworkSubmission>(`/api/v1/homeworks/${homeworkId}/submissions`, {
    method: "POST",
    body: JSON.stringify({ text_content: textContent }),
  });
}
