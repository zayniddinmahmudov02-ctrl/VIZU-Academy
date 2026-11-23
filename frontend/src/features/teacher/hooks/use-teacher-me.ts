"use client";

import { useQuery } from "@tanstack/react-query";

import { getTeacherMe } from "../services/teacher-panel.service";

export const TEACHER_ME_KEY = ["teacher-me"] as const;

/** The teacher's own permissions (Kontroll yes / no) — the server checks them again on every Kontroll request. */
export function useTeacherMe() {
  return useQuery({ queryKey: TEACHER_ME_KEY, queryFn: getTeacherMe, staleTime: 60_000 });
}
