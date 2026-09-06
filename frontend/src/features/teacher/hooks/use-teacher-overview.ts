"use client";

import { useQuery } from "@tanstack/react-query";

import { getTeacherOverview } from "../services/teacher.service";

export function useTeacherOverview() {
  return useQuery({
    queryKey: ["teacher-overview"],
    queryFn: getTeacherOverview,
  });
}
