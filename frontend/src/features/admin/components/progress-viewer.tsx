import { CheckCircle2, Circle } from "lucide-react";

import type { UserProgress } from "../types/user";

const SKILLS: { key: keyof UserProgress["lessons"][number]; label: string }[] = [
  { key: "videoCompleted", label: "Video" },
  { key: "grammarCompleted", label: "Grammatik" },
  { key: "readingCompleted", label: "Lesen" },
  { key: "listeningCompleted", label: "Hören" },
  { key: "writingCompleted", label: "Schreiben" },
  { key: "speakingCompleted", label: "Sprechen" },
  { key: "quizCompleted", label: "Quiz" },
];

export default function ProgressViewer({ progress }: { progress: UserProgress }) {
  return (
    <div className="admin-glass rounded-2xl p-5">
      <p className="mb-4 text-xs font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">Learning Progress</p>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-xl bg-white/[0.03] p-3 text-center">
          <p className="text-lg font-bold text-white">{progress.totalLessonsCompleted}</p>
          <p className="text-[10px] uppercase tracking-wide text-[var(--admin-text-muted)]">Lessons done</p>
        </div>
        <div className="rounded-xl bg-white/[0.03] p-3 text-center">
          <p className="text-lg font-bold text-white">{progress.totalLessonsStarted}</p>
          <p className="text-[10px] uppercase tracking-wide text-[var(--admin-text-muted)]">Lessons started</p>
        </div>
        <div className="rounded-xl bg-white/[0.03] p-3 text-center">
          <p className="text-lg font-bold text-white">{progress.totalExperience}</p>
          <p className="text-[10px] uppercase tracking-wide text-[var(--admin-text-muted)]">Experience</p>
        </div>
        <div className="rounded-xl bg-white/[0.03] p-3 text-center">
          <p className="text-lg font-bold text-white">{progress.longestStreakDays}d</p>
          <p className="text-[10px] uppercase tracking-wide text-[var(--admin-text-muted)]">Best streak</p>
        </div>
      </div>

      <div className="mt-5 max-h-80 space-y-2 overflow-y-auto">
        {progress.lessons.length === 0 ? (
          <p className="py-6 text-center text-xs text-[var(--admin-text-muted)]">No lesson activity yet.</p>
        ) : (
          progress.lessons.map((lesson) => (
            <div key={lesson.lessonId} className="rounded-xl bg-white/[0.03] p-3">
              <div className="flex items-center justify-between">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-white">{lesson.lessonTitle}</p>
                  <p className="truncate text-[11px] text-[var(--admin-text-muted)]">{lesson.courseTitle}</p>
                </div>
                <span className="shrink-0 rounded-full bg-white/5 px-2 py-0.5 text-[11px] font-semibold text-[var(--admin-text-secondary)]">
                  {lesson.totalScore} pts
                </span>
              </div>
              <div className="mt-2 flex flex-wrap gap-2">
                {SKILLS.map((skill) => {
                  const done = Boolean(lesson[skill.key]);
                  return (
                    <span key={skill.key} className={`flex items-center gap-1 text-[10px] ${done ? "text-[#22c55e]" : "text-[var(--admin-text-muted)]"}`}>
                      {done ? <CheckCircle2 size={11} /> : <Circle size={11} />}
                      {skill.label}
                    </span>
                  );
                })}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
