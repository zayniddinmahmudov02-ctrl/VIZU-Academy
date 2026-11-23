"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { EmptyState, ErrorState, Loading, Panel, TeacherPageTitle } from "@/components/teacher/teacher-ui";
import { formatDateTime } from "@/features/activity/lib/format";
import type { VideoLesson } from "@/features/teacher/panel-types";
import { getTeacherVideoLessons } from "@/features/teacher/services/teacher-panel.service";
import { useTranslation } from "@/lib/i18n/use-translation";

function Rows({ rows, empty, when }: { rows: VideoLesson[]; empty: string; when: (r: VideoLesson) => string | null }) {
  const { t } = useTranslation();
  if (!rows.length) return <EmptyState text={empty} />;
  return (
    <ul className="space-y-2">
      {rows.map((r) => (
        <li key={r.id} className="flex flex-wrap items-center justify-between gap-2 rounded-xl p-2 ring-1 ring-surface-border">
          <span className="min-w-0"><span className="block truncate text-sm font-medium text-text-primary">{r.title}</span>
            <span className="block text-xs text-text-muted">{r.group} · {when(r) ?? "—"}</span></span>
          <Link href={`/teacher/groups/${r.group_id}?tab=video`} className="text-sm font-medium text-accent-blue">{t("tpanel.toGroup")}</Link>
        </li>
      ))}
    </ul>
  );
}

export default function TeacherLessonsPage() {
  const { t, language } = useTranslation();
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ["teacher-video-lessons"], queryFn: getTeacherVideoLessons, refetchInterval: 60_000 });

  return (
    <div data-testid="teacher-unterricht">
      <TeacherPageTitle title={t("tpanel.lessonsTitle")} subtitle={t("tpanel.lessonsSubtitle")} />
      {isLoading && <Loading />}
      {isError && <ErrorState onRetry={() => refetch()} />}
      {data && (
        <div className="space-y-4">
          {data.groups.length === 0 ? <EmptyState text={t("tpanel.emptyGroups")} /> : (
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="text-text-secondary">{t("tpanel.planInGroup")}:</span>
              {data.groups.map((g) => <Link key={g.id} href={`/teacher/groups/${g.id}?tab=video`} className="rounded-full bg-accent-blue/10 px-3 py-1 font-medium text-accent-blue">{g.name}</Link>)}
            </div>
          )}
          {data.live.length > 0 && <Panel title={t("tpanel.live")}><Rows rows={data.live} empty="" when={(r) => formatDateTime(r.started_at, language)} /></Panel>}
          <Panel title={t("tpanel.planned")}><Rows rows={data.upcoming} empty={t("tpanel.emptyLessons")} when={(r) => formatDateTime(r.scheduled_at, language)} /></Panel>
          <Panel title={t("tpanel.past")}><Rows rows={data.past} empty={t("tpanel.emptyActivity")} when={(r) => formatDateTime(r.started_at ?? r.ended_at, language)} /></Panel>
        </div>
      )}
    </div>
  );
}
