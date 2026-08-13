import { api } from "@/src/services/api";
import { Course } from "../types/course";
import { CourseModule } from "../types/module";

export async function getCourses(): Promise<Course[]> {
  // /api/v1/courses, not bare /courses — that path is also the Next.js
  // course-listing page, and the production nginx gateway reserves it for
  // the frontend. See backend/app/main.py's courses_router mount.
  const response = await api.get<Course[]>("/api/v1/courses");
  return response.data;
}

// Public — no auth required (GET /modules has none). Every level currently
// has exactly one wrapping Module (see backend/app/scripts/seed_courses.py),
// so fetching the small full list and filtering client-side by course_id
// is simpler than adding a new filtered endpoint for what's a handful of
// rows today.
export async function getModules(): Promise<CourseModule[]> {
  const response = await api.get<CourseModule[]>("/api/v1/modules");
  return response.data;
}