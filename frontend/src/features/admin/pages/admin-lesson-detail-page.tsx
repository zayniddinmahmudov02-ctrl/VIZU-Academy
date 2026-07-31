"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { getLesson } from "../services/lessons-service";
import { LESSON_ACTIVITY_CONFIGS } from "../config/lesson-activity-configs";
import LessonActivityPanel from "../components/lesson-activity-panel";
import AdminLoading from "../components/admin-loading";
import type { AdminLessonItem } from "../types/lesson";

export default function AdminLessonDetailPage({ lessonId }: { lessonId: string }) {
  const router = useRouter();
  const [lesson, setLesson] = useState<AdminLessonItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(LESSON_ACTIVITY_CONFIGS[0].type);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    getLesson(lessonId)
      .then((data) => {
        if (isMounted) setLesson(data);
      })
      .catch((err) => console.warn("Failed to load lesson:", err))
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [lessonId]);

  const activeConfig = LESSON_ACTIVITY_CONFIGS.find((c) => c.type === activeTab) ?? LESSON_ACTIVITY_CONFIGS[0];

  if (loading) return <AdminLoading />;

  return (
    <div className="space-y-6">
      <div className="admin-glass flex flex-wrap items-center gap-4 rounded-2xl p-6">
        <button
          type="button"
          onClick={() => router.push("/admin/lessons")}
          aria-label="Back to lessons"
          className="rounded-xl border border-[var(--admin-border)] p-2 text-[var(--admin-text-secondary)] transition-colors hover:bg-white/5 hover:text-white"
        >
          <ArrowLeft size={16} />
        </button>
        <div>
          <h1 className="text-lg font-bold text-white">
            {lesson ? `${lesson.number}. ${lesson.title}` : "Lesson"}
          </h1>
          <p className="text-xs text-[var(--admin-text-muted)]">
            Video is managed on the Videos page — manage this lesson&apos;s remaining activities below.
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 rounded-2xl bg-white/[0.02] p-2">
        {LESSON_ACTIVITY_CONFIGS.map((config) => (
          <button
            key={config.type}
            type="button"
            onClick={() => setActiveTab(config.type)}
            className={`rounded-xl px-4 py-2 text-xs font-semibold transition-colors ${
              activeTab === config.type
                ? "bg-[var(--admin-primary)] text-white"
                : "text-[var(--admin-text-secondary)] hover:bg-white/5 hover:text-white"
            }`}
          >
            {config.label}
          </button>
        ))}
      </div>

      <LessonActivityPanel key={activeConfig.type} lessonId={lessonId} config={activeConfig} />
    </div>
  );
}
