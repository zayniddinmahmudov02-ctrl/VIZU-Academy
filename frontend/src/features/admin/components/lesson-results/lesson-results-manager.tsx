"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";

import { AdminInput } from "@/components/admin/admin-ui";
import LessonScoreBreakdown from "@/components/lesson-player/results/lesson-score-breakdown";
import { listUsers } from "@/features/admin/services/users-service";
import { getStudentLessonScore } from "@/features/admin/services/lesson-score-service";

interface Props {
  lessonId: string;
}

/** Admin view of one student's 100-point breakdown for this lesson —
 * search for the student, pick them, see the same breakdown the student
 * themselves sees (LessonScoreBreakdown, shared component). Lets the
 * admin identify weak competencies per student per lesson. */
export default function LessonResultsManager({ lessonId }: Props) {
  const [search, setSearch] = useState("");
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);

  const { data: usersResult, isLoading: usersLoading } = useQuery({
    queryKey: ["admin-users-search", search],
    queryFn: () => listUsers({ search, page_size: 10 }),
    enabled: search.trim().length >= 2,
  });

  const { data: score, isLoading: scoreLoading } = useQuery({
    queryKey: ["admin-lesson-score", lessonId, selectedUserId],
    queryFn: () => getStudentLessonScore(lessonId, selectedUserId as string),
    enabled: !!selectedUserId,
  });

  const selectedUser = usersResult?.items.find((u) => u.id === selectedUserId);

  return (
    <div className="space-y-5">
      <div>
        <label className="mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]">
          Schüler suchen
        </label>
        <div className="relative">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--admin-text-muted)]" />
          <AdminInput
            className="pl-9"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setSelectedUserId(null);
            }}
            placeholder="Name oder E-Mail eingeben..."
          />
        </div>

        {search.trim().length >= 2 && !selectedUserId && (
          <div className="mt-2 max-h-56 space-y-1 overflow-y-auto rounded-xl bg-white/[0.02] p-2 ring-1 ring-[var(--admin-border)]">
            {usersLoading && <p className="p-2 text-xs text-[var(--admin-text-muted)]">Wird geladen...</p>}
            {!usersLoading && (usersResult?.items.length ?? 0) === 0 && (
              <p className="p-2 text-xs text-[var(--admin-text-muted)]">Keine Schüler gefunden.</p>
            )}
            {usersResult?.items.map((u) => (
              <button
                key={u.id}
                type="button"
                onClick={() => setSelectedUserId(u.id)}
                className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm text-[var(--admin-text-primary)] hover:bg-white/5"
              >
                <span>
                  {u.first_name || u.last_name ? `${u.first_name ?? ""} ${u.last_name ?? ""}`.trim() : u.username}
                </span>
                <span className="text-xs text-[var(--admin-text-muted)]">{u.email}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {selectedUser && (
        <div className="rounded-xl bg-[var(--admin-primary)]/10 px-4 py-2.5 text-sm text-[var(--admin-text-primary)]">
          Ergebnis für: <span className="font-semibold">{selectedUser.username}</span> ({selectedUser.email})
        </div>
      )}

      {selectedUserId && scoreLoading && (
        <p className="text-sm text-[var(--admin-text-secondary)]">Wird geladen...</p>
      )}

      {selectedUserId && score && (
        <div className="rounded-2xl bg-[var(--admin-card)] p-5 ring-1 ring-[var(--admin-border)]">
          <LessonScoreBreakdown score={score} />
        </div>
      )}
    </div>
  );
}
