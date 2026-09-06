"use client";

import { useQuery } from "@tanstack/react-query";

import { getTeacherStudents } from "../services/teacher.service";

export function useTeacherStudents() {
  return useQuery({
    queryKey: ["teacher-students"],
    queryFn: getTeacherStudents,
  });
}
