"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, LogOut } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import { getGroup, getMembers, getMyProgress, leaveGroup } from "../groups-service";
import Announcements from "./announcements";
import GroupChat from "./group-chat";
import ProgressDetail from "./progress-detail";
import { card, ErrorBox, fmtDate, LevelPill, Loading, Tabs, TaskBadge } from "./ui";

type Tab = "overview" | "chat" | "announcements" | "tasks" | "progress" | "members";
const TABS: Tab[] = ["overview", "chat", "announcements", "tasks", "progress", "members"];
const LABEL: Record<Tab, string> = { overview: "tabOverview", chat: "tabChat", announcements: "tabAnnouncements", tasks: "tabTasks", progress: "tabProgress", members: "tabMembers" };

/** A student's view of one group. Everything is loaded through
 *  membership-checked endpoints; a non-member gets "not found". */
export default function StudentGroupView({ groupId }: { groupId: string }) {
  const { t } = useTranslation();
  const router = useRouter();
  const qc = useQueryClient();
  const params = useSearchParams();
  const initial = params.get("tab") as Tab | null;
  const [tab, setTab] = useState<Tab>(initial && TABS.includes(initial) ? initial : "overview");
  const group = useQuery({ queryKey: ["groups", groupId], queryFn: () => getGroup(groupId), retry: false });
  const progress = useQuery({ queryKey: ["groups", groupId, "me"], queryFn: () => getMyProgress(groupId), enabled: group.isSuccess && (tab === "tasks" || tab === "progress" || tab === "overview") });
  const members = useQuery({ queryKey: ["groups", groupId, "members"], queryFn: () => getMembers(groupId), enabled: group.isSuccess && tab === "members" });

  if (group.isLoading) return <Loading />;
  if (group.isError || !group.data) return <ErrorBox error={group.error} />;
  const g = group.data;

  async function leave() {
    if (!window.confirm(t("groups.leaveConfirm"))) return;
    await leaveGroup(groupId);
    await qc.invalidateQueries({ queryKey: ["groups", "my"] });
    router.push("/groups");
  }

  return (
    <div className="space-y-5">
      <Link href="/groups" className="inline-flex items-center gap-1 text-sm font-semibold text-text-secondary hover:text-text-primary"><ArrowLeft size={14} /> {t("groups.back")}</Link>
      <div className={cn(card, "flex flex-col gap-2 p-5 sm:flex-row sm:items-start sm:justify-between")}>
        <div className="min-w-0">
          <h1 className="text-xl font-bold text-text-primary">{g.name}</h1>
          <p className="text-sm text-text-secondary">{t("groups.teacher")}: {g.teacher.name} · {g.student_count} {t("groups.members")}</p>
          {g.description && <p className="mt-1 whitespace-pre-wrap text-sm text-text-muted">{g.description}</p>}
        </div>
        <LevelPill level={g.level} />
      </div>

      <Tabs tabs={TABS.map((id) => ({ id, label: t(`groups.${LABEL[id]}`), badge: id === "chat" ? g.viewer.unread : undefined }))} active={tab} onChange={setTab} />

      {tab === "overview" && (
        <div className="grid gap-4 md:grid-cols-2">
          <div className={cn(card, "space-y-1 p-5 text-sm")}>
            <p className="font-bold text-text-primary">{t("groups.courses")}</p>
            {g.courses.length ? g.courses.map((c) => <p key={c.id} className="text-text-secondary">{c.title} ({c.level})</p>) : <p className="text-text-muted">{t("groups.noCourses")}</p>}
            <Link href="/kurse" className="inline-block pt-2 text-sm font-semibold text-accent-blue">{t("sidebar.courses")} →</Link>
          </div>
          <div className={cn(card, "space-y-2 p-5")}>
            <p className="text-sm font-bold text-text-primary">{t("groups.tabTasks")}</p>
            {progress.data?.tasks.filter((x) => !["completed", "completed_late"].includes(x.status)).slice(0, 5).map((x) => (
              <div key={x.id} className="flex items-center justify-between gap-2 text-sm">
                <span className="truncate text-text-secondary">{x.title} {x.due_at && <span className="text-xs text-text-muted">· {fmtDate(x.due_at, true)}</span>}</span>
                <TaskBadge status={x.status} />
              </div>
            ))}
            {progress.data && progress.data.tasks.length === 0 && <p className="text-sm text-text-muted">{t("groups.noTasks")}</p>}
          </div>
        </div>
      )}
      {tab === "chat" && <GroupChat groupId={groupId} onRead={() => qc.invalidateQueries({ queryKey: ["groups", "my"] })} />}
      {tab === "announcements" && <Announcements groupId={groupId} manager={false} />}
      {(tab === "tasks" || tab === "progress") && (
        progress.isLoading ? <Loading /> : progress.isError ? <ErrorBox error={progress.error} onRetry={() => progress.refetch()} /> : progress.data ? (
          tab === "tasks" ? (
            <ul className="space-y-2">
              {progress.data.tasks.length === 0 && <p className={cn(card, "p-6 text-center text-sm text-text-muted")}>{t("groups.noTasks")}</p>}
              {progress.data.tasks.map((x) => (
                <li key={x.id} className={cn(card, "flex flex-col gap-2 p-4 sm:flex-row sm:items-center sm:justify-between")}>
                  <div className="min-w-0">
                    <p className="text-sm font-bold text-text-primary">{x.title}</p>
                    <p className="text-xs text-text-muted">{x.module} · {x.lesson_title} · {x.due_at ? `${t("groups.due")}: ${fmtDate(x.due_at, true)}` : t("groups.noDue")}</p>
                    {x.note && <p className="mt-1 text-xs text-text-secondary">{x.note}</p>}
                  </div>
                  <TaskBadge status={x.status} />
                </li>
              ))}
            </ul>
          ) : <ProgressDetail detail={progress.data} />
        ) : null
      )}
      {tab === "members" && (
        members.isLoading ? <Loading /> : (
          <ul className={cn(card, "divide-y divide-surface-border")}>
            {(members.data ?? []).map((m) => (
              <li key={m.user_id} className="flex items-center justify-between gap-2 px-5 py-3 text-sm">
                <span className="font-semibold text-text-primary">{m.name}</span>
                {m.role === "teacher" && <span className="text-xs font-semibold text-accent-blue">{t("groups.teacher")}</span>}
              </li>
            ))}
          </ul>
        )
      )}

      <button type="button" onClick={leave} className="inline-flex items-center gap-1.5 text-xs font-semibold text-text-muted hover:text-danger">
        <LogOut size={13} /> {t("groups.leave")}
      </button>
    </div>
  );
}
