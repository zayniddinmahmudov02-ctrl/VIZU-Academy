// Mirrors backend/app/schemas/course/schema.py::CourseResponse exactly.
export interface Course {
  id: string;
  language_id: string;
  level: string;
  title: string;
  description: string | null;
  order_index: number;
  is_active: boolean;
}
