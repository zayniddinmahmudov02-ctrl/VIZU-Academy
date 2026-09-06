import { api } from "@/src/services/api";

import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type { TeacherAssignment, TeacherCandidate } from "../types/teacher.types";

// Super-admin-only management of which courses a TEACHER-role user may see
// students for (backend/app/models/teacher_assignment.py) — the Teacher
// Panel itself (GET /teacher/students) is entirely read-only and has no
// self-service way to create these rows.
export const teacherAssignmentsApi = {
  async list(): Promise<TeacherAssignment[]> {
    const response = await api.get<TeacherAssignment[]>(ADMIN_ENDPOINTS.adminTeacherAssignments);
    return response.data;
  },
  async listCandidates(): Promise<TeacherCandidate[]> {
    const response = await api.get<TeacherCandidate[]>(ADMIN_ENDPOINTS.adminTeacherAssignmentCandidates);
    return response.data;
  },
  async create(teacherId: string, courseId: string): Promise<TeacherAssignment> {
    const response = await api.post<TeacherAssignment>(ADMIN_ENDPOINTS.adminTeacherAssignments, {
      teacher_id: teacherId,
      course_id: courseId,
    });
    return response.data;
  },
  async remove(id: string): Promise<void> {
    await api.delete(`${ADMIN_ENDPOINTS.adminTeacherAssignments}/${id}`);
  },
};
