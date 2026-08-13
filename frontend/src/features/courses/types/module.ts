// Mirrors backend/app/schemas/module/schema.py::ModuleResponse.
export interface CourseModule {
  id: string;
  course_id: string;
  number: number;
  title: string;
  description: string | null;
  order_index: number;
  is_active: boolean;
}
