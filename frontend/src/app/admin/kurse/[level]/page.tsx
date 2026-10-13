"use client";

import { useParams } from "next/navigation";

import LevelLessons from "@/features/admin/components/lms-course/level-lessons";

export default function AdminKursLevelPage() {
  const { level } = useParams<{ level: string }>();
  return <LevelLessons level={level} />;
}
