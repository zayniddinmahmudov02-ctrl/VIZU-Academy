import { api } from "@/src/services/api";
import { Course } from "../types/course";

export async function getCourses(): Promise<Course[]> {
  // /api/v1/courses, not bare /courses — that path is also the Next.js
  // course-listing page, and the production nginx gateway reserves it for
  // the frontend. See backend/app/main.py's courses_router mount.
  const response = await api.get<Course[]>("/api/v1/courses");
  return response.data;
}