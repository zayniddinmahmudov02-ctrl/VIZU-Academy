"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Award,
  BookOpen,
  ClipboardCheck,
  FileText,
  FolderOpen,
  Gauge,
  Headphones,
  HelpCircle,
  Layers3,
  Mic,
  PenLine,
  SpellCheck,
  UserCheck,
  Users,
  Video,
  type LucideIcon,
} from "lucide-react";

import { AdminCard, AdminPageHeader } from "@/components/admin/admin-ui";
import {
  getLanguage,
  getLanguageStatistics,
} from "@/features/admin/services/language-management-service";
import type { LanguageStatistics } from "@/features/admin/types/language.types";

const STAT_DEFS: { key: keyof LanguageStatistics; label: string; icon: LucideIcon }[] = [
  { key: "learners", label: "Learners", icon: Users },
  { key: "active_learners", label: "Active Learners", icon: UserCheck },
  { key: "levels", label: "Levels", icon: Gauge },
  { key: "modules", label: "Modules", icon: Layers3 },
  { key: "lessons", label: "Lessons", icon: BookOpen },
  { key: "videos", label: "Videos", icon: Video },
  { key: "vocabulary", label: "Vocabulary", icon: SpellCheck },
  { key: "grammar", label: "Grammar", icon: FileText },
  { key: "reading", label: "Reading", icon: BookOpen },
  { key: "listening", label: "Listening", icon: Headphones },
  { key: "writing", label: "Writing", icon: PenLine },
  { key: "speaking", label: "Speaking", icon: Mic },
  { key: "homework", label: "Homework", icon: FolderOpen },
  { key: "quiz", label: "Quiz", icon: HelpCircle },
  { key: "mock_tests", label: "Mock Tests", icon: ClipboardCheck },
  { key: "certificates", label: "Certificates", icon: Award },
];

export default function LanguageDashboardPage() {
  const { id } = useParams<{ id: string }>();

  const { data: language } = useQuery({ queryKey: ["language", id], queryFn: () => getLanguage(id) });
  const { data: stats, isLoading, isError } = useQuery({
    queryKey: ["language-statistics", id],
    queryFn: () => getLanguageStatistics(id),
  });

  return (
    <div>
      <Link
        href="/admin/languages"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--admin-text-muted)] hover:text-[var(--admin-text-primary)]"
      >
        ← Languages
      </Link>

      <AdminPageHeader
        title={`Dashboard — ${language?.name ?? ""}`}
        description="Live-Statistiken direkt aus PostgreSQL."
      />

      {isError && (
        <AdminCard>
          <p className="text-sm text-[var(--admin-danger)]">Statistiken konnten nicht geladen werden.</p>
        </AdminCard>
      )}

      {isLoading && <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>}

      {stats && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {STAT_DEFS.map((def) => {
            const Icon = def.icon;
            return (
              <AdminCard key={def.key} className="flex items-center gap-3.5">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[var(--admin-primary)]/15 text-[var(--admin-primary)]">
                  <Icon size={19} />
                </div>
                <div className="min-w-0">
                  <p className="truncate text-[11px] font-medium uppercase tracking-wide text-[var(--admin-text-muted)]">
                    {def.label}
                  </p>
                  <p className="mt-0.5 text-lg font-bold text-[var(--admin-text-primary)]">{stats[def.key]}</p>
                </div>
              </AdminCard>
            );
          })}
        </div>
      )}
    </div>
  );
}
