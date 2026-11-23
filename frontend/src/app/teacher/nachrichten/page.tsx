"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { MessagesSquare } from "lucide-react";

import { EmptyState, ErrorState, Loading, TeacherPageTitle } from "@/components/teacher/teacher-ui";
import { formatDateTime } from "@/features/activity/lib/format";
import { getTeacherMessages } from "@/features/teacher/services/teacher-panel.service";
import { useTranslation } from "@/lib/i18n/use-translation";

export default function TeacherMessagesPage() {
  const { t, language } = useTranslation();
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ["teacher-messages"], queryFn: getTeacherMessages, refetchInterval: 30_000 });

  return (
    <div data-testid="teacher-nachrichten">
      <TeacherPageTitle title={t("tpanel.messagesTitle")} subtitle={t("tpanel.messagesSubtitle")} />
      {isLoading && <Loading />}
      {isError && <ErrorState onRetry={() => refetch()} />}
      {data && data.length === 0 && <EmptyState text={t("tpanel.emptyGroups")} />}
      <ul className="space-y-2">
        {data?.map((g) => (
          <li key={g.group_id}>
            <Link href={`/teacher/groups/${g.group_id}?tab=chat`} className="flex items-start gap-3 rounded-2xl bg-surface-card p-4 shadow-[var(--shadow-md)] ring-1 ring-surface-border hover:bg-surface-hover" data-testid="teacher-chat">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-accent-blue/10 text-accent-blue"><MessagesSquare size={18} /></span>
              <span className="min-w-0 flex-1">
                <span className="flex items-center justify-between gap-2">
                  <span className="truncate font-semibold text-text-primary">{g.group} <span className="text-text-muted">· {g.level}</span></span>
                  {g.unread > 0 && <span className="shrink-0 rounded-full bg-accent-blue px-2 py-0.5 text-xs font-semibold text-white">{t("tpanel.unread", { n: g.unread })}</span>}
                </span>
                {g.last_message ? (
                  <span className="mt-0.5 block truncate text-sm text-text-secondary">{g.last_message.sender ? `${g.last_message.sender}: ` : ""}{g.last_message.body}
                    <span className="text-xs text-text-muted"> · {formatDateTime(g.last_message.at, language)}</span></span>
                ) : <span className="mt-0.5 block text-sm text-text-muted">{t("tpanel.emptyMessages")}</span>}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
