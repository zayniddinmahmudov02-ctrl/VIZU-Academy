"use client";

import { useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { keepPreviousData, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Loader2, Trash2 } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import {
  changeCode, deleteTask, getAuditLog, getDashboard, getGroup, getGroupLessons, getMembers, getStudents, getTaskBoard,
  regenerateCode, saveTask, setChatMode, updateGroup, updateMember, type ChatMode, type GroupDetail,
} from "../groups-service";
import Announcements from "./announcements";
import GroupChat from "./group-chat";
import GroupForm, { CodeReveal } from "./group-form";
import { card, ErrorBox, fmtDate, input, LevelPill, Loading, primaryBtn, secondaryBtn, Stat, StatusPill, Tabs, TaskBadge, textarea, useErrorText } from "./ui";

type Tab = "overview" | "chat" | "announcements" | "tasks" | "students" | "settings" | "audit";
const TABS: Tab[] = ["overview", "chat", "announcements", "tasks", "students", "settings", "audit"];
const LABEL: Record<Tab, string> = { overview: "tabOverview", chat: "tabChat", announcements: "tabAnnouncements", tasks: "tabTasks", students: "tabStudents", settings: "tabSettings", audit: "tabAudit" };

function Overview({ groupId }: { groupId: string }) {
  const { t } = useTranslation();
  const d = useQuery({ queryKey: ["groups", groupId, "dashboard"], queryFn: () => getDashboard(groupId) });
  if (d.isLoading) return <Loading />;
  if (d.isError || !d.data) return <ErrorBox error={d.error} onRetry={() => d.refetch()} />;
  const x = d.data;
  const num = (v: number | null) => (v == null ? "—" : v);
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4" data-testid="group-dashboard">
      <Stat label={t("groups.d_students")} value={x.students} />
      <Stat label={t("groups.d_active")} value={x.active_students} />
      <Stat label={t("groups.d_progress")} value={x.overall_progress == null ? "—" : `${x.overall_progress}%`} />
      <Stat label={t("groups.d_lastActivity")} value={<span className="text-base">{fmtDate(x.last_activity_at, true)}</span>} />
      <Stat label={t("groups.d_completedAll")} value={num(x.students_completed_all_lessons)} />
      <Stat label={t("groups.d_submittedAll")} value={num(x.students_submitted_all_tasks)} />
      <Stat label={t("groups.d_submitted")} value={x.tasks_submitted} tone="ok" />
      <Stat label={t("groups.d_missing")} value={x.tasks_missing} />
      <Stat label={t("groups.d_overdue")} value={x.tasks_overdue} tone={x.tasks_overdue ? "danger" : undefined} />
      <Stat label={t("groups.d_underReview")} value={x.tasks_under_review} tone={x.tasks_under_review ? "warn" : undefined} />
      <Stat label={t("groups.d_awaiting")} value={x.awaiting_teacher_review} tone={x.awaiting_teacher_review ? "warn" : undefined} />
      <Stat label={t("groups.d_avgScore")} value={num(x.average_lesson_score)} />
      <Stat label={t("groups.d_avgGrade")} value={num(x.average_grade)} />
    </div>
  );
}

function TasksTab({ groupId, canEdit }: { groupId: string; canEdit: boolean }) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const errorText = useErrorText();
  const board = useQuery({ queryKey: ["groups", groupId, "tasks"], queryFn: () => getTaskBoard(groupId) });
  const lessons = useQuery({ queryKey: ["groups", groupId, "lessons"], queryFn: () => getGroupLessons(groupId), enabled: canEdit });
  const [form, setForm] = useState({ lesson_id: "", title: "", note: "", due_at: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState<string | null>(null);

  async function run(fn: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await fn();
      await qc.invalidateQueries({ queryKey: ["groups", groupId] });
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      {canEdit && (
        <form className={cn(card, "grid gap-3 p-5 sm:grid-cols-2")} onSubmit={(e) => {
          e.preventDefault();
          run(async () => {
            await saveTask(groupId, { lesson_id: form.lesson_id, title: form.title || null, note: form.note || null, due_at: form.due_at ? new Date(form.due_at).toISOString() : null });
            setForm({ lesson_id: "", title: "", note: "", due_at: "" });
          });
        }}>
          <p className="text-sm font-bold text-text-primary sm:col-span-2">{t("groups.addTask")}</p>
          {(lessons.data ?? []).length === 0 && !lessons.isLoading ? <p className="text-sm text-text-muted sm:col-span-2">{t("groups.noLessons")}</p> : (
            <>
              <select className={input} value={form.lesson_id} required onChange={(e) => setForm({ ...form, lesson_id: e.target.value })} aria-label={t("groups.lesson")}>
                <option value="">— {t("groups.lesson")} —</option>
                {(lessons.data ?? []).map((l) => <option key={l.id} value={l.id}>{l.level} · {l.module} · {l.number}. {l.title}{l.task ? " ✓" : ""}</option>)}
              </select>
              <input type="datetime-local" className={input} value={form.due_at} onChange={(e) => setForm({ ...form, due_at: e.target.value })} aria-label={t("groups.due")} />
              <input className={input} placeholder={t("groups.taskTitle")} maxLength={200} value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
              <textarea className={textarea} rows={1} placeholder={t("groups.note")} maxLength={2000} value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} />
              <div className="flex justify-end sm:col-span-2"><button type="submit" className={primaryBtn} disabled={busy || !form.lesson_id}>{t("groups.assign")}</button></div>
            </>
          )}
          {error && <p role="alert" className="text-sm text-danger sm:col-span-2">{error}</p>}
        </form>
      )}

      {board.isLoading ? <Loading /> : board.isError ? <ErrorBox error={board.error} onRetry={() => board.refetch()} /> : (board.data?.tasks ?? []).length === 0 ? (
        <p className={cn(card, "p-6 text-center text-sm text-text-muted")}>{t("groups.noTasks")}</p>
      ) : (
        <ul className="space-y-3">
          {board.data!.tasks.map((task) => (
            <li key={task.id} className={cn(card, "p-4")}>
              <div className="flex flex-wrap items-start justify-between gap-2">
                <button type="button" className="min-w-0 text-left" onClick={() => setOpen(open === task.id ? null : task.id)} aria-expanded={open === task.id}>
                  <p className="text-sm font-bold text-text-primary">{task.title}</p>
                  <p className="text-xs text-text-muted">{task.module} · {task.lesson_title} · {task.due_at ? `${t("groups.due")}: ${fmtDate(task.due_at, true)}` : t("groups.noDue")}</p>
                </button>
                <div className="flex items-center gap-2">
                  {Object.entries(task.counts).map(([s, n]) => <span key={s} className="text-xs text-text-secondary"><TaskBadge status={s as never} /> {n}</span>)}
                  {canEdit && <button type="button" className="rounded-lg p-2 text-text-muted hover:text-danger" aria-label={t("groups.deleteTask")} title={t("groups.deleteTask")}
                                      disabled={busy} onClick={() => window.confirm(t("groups.deleteTask") + "?") && run(() => deleteTask(groupId, task.id))}><Trash2 size={15} /></button>}
                </div>
              </div>
              {open === task.id && (
                <ul className="mt-3 divide-y divide-surface-border rounded-xl bg-surface-hover/50">
                  {task.students.map((s) => (
                    <li key={s.user_id} className="flex items-center justify-between gap-2 px-3 py-2 text-sm">
                      <Link href={`/teacher/groups/${groupId}/students/${s.user_id}`} className="font-semibold text-text-primary hover:text-accent-blue">{s.name}</Link>
                      <TaskBadge status={s.status} />
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function StudentsTab({ groupId }: { groupId: string }) {
  const { t } = useTranslation();
  const [f, setF] = useState({ filter: "all", sort: "name", search: "", page: 1 });
  const list = useQuery({ queryKey: ["groups", groupId, "students", f], queryFn: () => getStudents(groupId, f), placeholderData: keepPreviousData });
  const pages = list.data ? Math.max(1, Math.ceil(list.data.total / list.data.page_size)) : 1;
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-1.5">
        {["all", "active", "inactive", "missing", "overdue", "awaiting_review"].map((k) => (
          <button key={k} type="button" onClick={() => setF({ ...f, filter: k, page: 1 })}
                  className={cn("rounded-lg px-3 py-1.5 text-xs font-semibold ring-1", f.filter === k ? "bg-accent-blue text-white ring-accent-blue" : "text-text-secondary ring-surface-border")}>
            {t(`groups.f_${k}`)}
          </button>
        ))}
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        <input className={input} placeholder={t("groups.search")} value={f.search} onChange={(e) => setF({ ...f, search: e.target.value, page: 1 })} />
        <select className={input} value={f.sort} onChange={(e) => setF({ ...f, sort: e.target.value })}>
          {["name", "progress", "progress_asc", "last_activity"].map((s) => <option key={s} value={s}>{t(`groups.sort_${s}`)}</option>)}
        </select>
      </div>
      {list.isLoading ? <Loading /> : list.isError ? <ErrorBox error={list.error} onRetry={() => list.refetch()} /> : (list.data?.items ?? []).length === 0 ? (
        <p className={cn(card, "p-6 text-center text-sm text-text-muted")}>{t("groups.noStudents")}</p>
      ) : (
        <div className={cn(card, "overflow-x-auto")}>
          <table className="w-full min-w-[820px] text-left text-sm" data-testid="students-table">
            <thead className="text-[11px] uppercase tracking-wide text-text-muted">
              <tr className="border-b border-surface-border">
                {[t("groups.col_student"), t("groups.lastActivity"), t("groups.col_lessons"), t("groups.d_submitted"), t("groups.d_missing"), t("groups.d_overdue"), t("groups.d_underReview"), t("groups.col_grade"), t("groups.progress")].map((h) => <th key={h} className="px-3 py-2.5">{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {list.data!.items.map((r) => (
                <tr key={r.user_id} className="border-b border-surface-border last:border-0 hover:bg-surface-hover/50">
                  <td className="px-3 py-2.5"><Link href={`/teacher/groups/${groupId}/students/${r.user_id}`} className="font-semibold text-text-primary hover:text-accent-blue">{r.name}</Link>
                    <p className="text-xs text-text-muted">{r.email}</p></td>
                  <td className="px-3 py-2.5 text-xs text-text-secondary">{r.last_activity_at ? fmtDate(r.last_activity_at, true) : t("groups.never")}</td>
                  <td className="px-3 py-2.5 text-text-secondary">{r.lessons_completed}/{r.lessons_total}</td>
                  <td className="px-3 py-2.5 text-text-secondary">{r.tasks_submitted}/{r.tasks_total}</td>
                  <td className="px-3 py-2.5 text-text-secondary">{r.tasks_missing}</td>
                  <td className={cn("px-3 py-2.5", r.tasks_overdue ? "font-bold text-danger" : "text-text-secondary")}>{r.tasks_overdue}</td>
                  <td className={cn("px-3 py-2.5", r.awaiting_review ? "font-bold text-amber-600" : "text-text-secondary")}>{r.awaiting_review}</td>
                  <td className="px-3 py-2.5 text-text-secondary">{r.average_grade ?? "—"}</td>
                  <td className="px-3 py-2.5 text-text-secondary">{r.progress == null ? "—" : `${r.progress}%`}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {pages > 1 && (
            <div className="flex items-center gap-2 p-3 text-sm text-text-secondary">
              <button type="button" className={secondaryBtn} disabled={f.page <= 1} onClick={() => setF({ ...f, page: f.page - 1 })}>←</button>
              {f.page} / {pages}
              <button type="button" className={secondaryBtn} disabled={f.page >= pages} onClick={() => setF({ ...f, page: f.page + 1 })}>→</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function SettingsTab({ group, onChanged }: { group: GroupDetail; onChanged: () => Promise<unknown> }) {
  const { t } = useTranslation();
  const errorText = useErrorText();
  const members = useQuery({ queryKey: ["groups", group.id, "members"], queryFn: () => getMembers(group.id) });
  const [code, setCode] = useState<string | null>(null);
  const [expires, setExpires] = useState("");
  const [maxUses, setMaxUses] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const blocked = group.status === "blocked";

  async function run(fn: () => Promise<unknown>, ok = t("groups.saved")) {
    setBusy(true);
    setMsg(null);
    try {
      await fn();
      await onChanged();
      await members.refetch();
      setMsg({ ok: true, text: ok });
    } catch (err) {
      setMsg({ ok: false, text: errorText(err) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <GroupForm key={group.id + group.status} group={group} onSubmit={async (data) => { await updateGroup(group.id, data); await onChanged(); setMsg({ ok: true, text: t("groups.saved") }); }} />

      <div className={cn(card, "space-y-3 p-5")} data-testid="code-settings">
        <p className="text-base font-bold text-text-primary">{t("groups.code")}</p>
        {code && <CodeReveal code={code} onClose={() => setCode(null)} />}
        {group.code ? (
          <p className="text-sm text-text-secondary">
            {group.code.usable ? t("groups.codeUsable") : t("groups.codeNotUsable")} · {t("groups.uses", { n: group.code.use_count })}{group.code.max_uses ? `/${group.code.max_uses}` : ""}
            {group.code.expires_at && <> · {t("groups.expiresAt")}: {fmtDate(group.code.expires_at, true)}</>}
          </p>
        ) : <p className="text-sm text-text-muted">{t("groups.noCode")}</p>}
        <div className="grid gap-2 sm:grid-cols-3">
          <input type="datetime-local" className={input} value={expires} onChange={(e) => setExpires(e.target.value)} aria-label={t("groups.expiresAt")} title={t("groups.expiresAt")} />
          <input type="number" min={1} className={input} value={maxUses} placeholder={t("groups.maxUses")} onChange={(e) => setMaxUses(e.target.value)} />
          <button type="button" className={primaryBtn} disabled={busy || blocked}
                  onClick={() => window.confirm(t("groups.newCodeHint")) && run(async () => {
                    const res = await regenerateCode(group.id, { expires_at: expires ? new Date(expires).toISOString() : null, max_uses: maxUses ? Number(maxUses) : null });
                    setCode(res.code);
                  })}>{t("groups.newCode")}</button>
        </div>
        {group.code && (
          <div className="flex flex-wrap gap-2">
            <button type="button" className={secondaryBtn} disabled={busy || blocked} onClick={() => run(() => changeCode(group.id, { paused: group.code!.status !== "paused" }))}>
              {group.code.status === "paused" ? t("groups.resumeCode") : t("groups.pauseCode")}
            </button>
            <button type="button" className={secondaryBtn} disabled={busy || blocked} onClick={() => window.confirm(t("groups.revokeCode") + "?") && run(() => changeCode(group.id, { revoke: true }))}>
              {t("groups.revokeCode")}
            </button>
          </div>
        )}
      </div>

      <div className={cn(card, "space-y-3 p-5")}>
        <p className="text-base font-bold text-text-primary">{t("groups.chatMode")}</p>
        <div className="flex flex-wrap gap-2">
          {(["open", "teacher_only", "closed"] as ChatMode[]).map((m) => (
            <button key={m} type="button" disabled={busy || blocked} onClick={() => run(() => setChatMode(group.id, m))}
                    className={cn("rounded-xl px-3 py-2 text-sm font-semibold ring-1", group.chat_mode === m ? "bg-accent-blue text-white ring-accent-blue" : "text-text-secondary ring-surface-border")}>
              {t(`groups.chat_${m}`)}
            </button>
          ))}
        </div>
      </div>

      <div className={cn(card, "p-5")}>
        <p className="mb-3 text-base font-bold text-text-primary">{t("groups.members")}</p>
        {members.isLoading ? <Loader2 className="animate-spin text-text-muted" /> : (
          <ul className="divide-y divide-surface-border">
            {(members.data ?? []).filter((m) => m.role === "student").map((m) => (
              <li key={m.user_id} className="flex flex-col gap-2 py-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-text-primary">{m.name} {m.status !== "active" && <span className="text-xs font-normal text-text-muted">({t(`groups.memberStatus_${m.status}`)})</span>}</p>
                  <p className="text-xs text-text-muted">{m.email} · {fmtDate(m.joined_at)}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {m.status === "active" ? (
                    <>
                      <button type="button" className={secondaryBtn} disabled={busy || blocked} onClick={() => run(() => updateMember(group.id, m.user_id, { can_post: !m.can_post }))}>
                        {m.can_post ? t("groups.mute") : t("groups.unmute")}
                      </button>
                      <button type="button" className={secondaryBtn} disabled={busy || blocked} onClick={() => window.confirm(t("groups.removeConfirm")) && run(() => updateMember(group.id, m.user_id, { remove: true }))}>
                        {t("groups.removeMember")}
                      </button>
                    </>
                  ) : m.status === "removed" ? (
                    <button type="button" className={secondaryBtn} disabled={busy || blocked} onClick={() => run(() => updateMember(group.id, m.user_id, { restore: true }))}>{t("groups.restoreMember")}</button>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
      {msg && <p role="status" className={cn("text-sm", msg.ok ? "text-success" : "text-danger")}>{msg.text}</p>}
    </div>
  );
}

function AuditTab({ groupId }: { groupId: string }) {
  const { t } = useTranslation();
  const [page, setPage] = useState(1);
  const log = useQuery({ queryKey: ["groups", groupId, "audit", page], queryFn: () => getAuditLog(groupId, page), placeholderData: keepPreviousData });
  if (log.isLoading) return <Loading />;
  if (log.isError || !log.data) return <ErrorBox error={log.error} />;
  const pages = Math.max(1, Math.ceil(log.data.total / log.data.page_size));
  return (
    <div className={cn(card, "p-4")}>
      <ul className="divide-y divide-surface-border text-sm">
        {log.data.items.map((r) => (
          <li key={r.id} className="flex flex-wrap gap-x-3 py-2">
            <span className="text-xs text-text-muted">{fmtDate(r.created_at, true)}</span>
            <span className="font-mono text-xs font-semibold text-text-primary">{r.action}</span>
            <span className="text-xs text-text-secondary">{r.actor ?? "—"}</span>
          </li>
        ))}
      </ul>
      {pages > 1 && (
        <div className="mt-2 flex items-center gap-2 text-sm text-text-secondary">
          <button type="button" className={secondaryBtn} disabled={page <= 1} onClick={() => setPage(page - 1)}>←</button>{page} / {pages}
          <button type="button" className={secondaryBtn} disabled={page >= pages} onClick={() => setPage(page + 1)}>→</button>
        </div>
      )}
      {log.data.items.length === 0 && <p className="text-sm text-text-muted">{t("groups.noData")}</p>}
    </div>
  );
}

/** Teacher view of one group (also reached by a SUPER_ADMIN). */
export default function TeacherGroupView({ groupId }: { groupId: string }) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const params = useSearchParams();
  const initial = params.get("tab") as Tab | null;
  const [tab, setTab] = useState<Tab>(initial && TABS.includes(initial) ? initial : "overview");
  const group = useQuery({ queryKey: ["groups", groupId], queryFn: () => getGroup(groupId), retry: false });

  if (group.isLoading) return <Loading />;
  if (group.isError || !group.data) return <ErrorBox error={group.error} />;
  const g = group.data;
  const canEdit = g.status !== "blocked";

  return (
    <div className="space-y-5">
      <Link href="/teacher/groups" className="inline-flex items-center gap-1 text-sm font-semibold text-text-secondary hover:text-text-primary"><ArrowLeft size={14} /> {t("groups.back")}</Link>
      <div className={cn(card, "flex flex-col gap-2 p-5 sm:flex-row sm:items-start sm:justify-between")}>
        <div className="min-w-0">
          <h1 className="text-xl font-bold text-text-primary">{g.name}</h1>
          <p className="text-sm text-text-secondary">{t("groups.teacher")}: {g.teacher.name} · {g.student_count}{g.capacity ? `/${g.capacity}` : ""} {t("groups.students")} · {g.courses.map((c) => c.title).join(", ") || t("groups.noCourses")}</p>
        </div>
        <div className="flex gap-2"><StatusPill status={g.status} /><LevelPill level={g.level} /></div>
      </div>

      <Tabs tabs={TABS.map((id) => ({ id, label: t(`groups.${LABEL[id]}`), badge: id === "chat" ? g.viewer.unread : undefined }))} active={tab} onChange={setTab} />

      {tab === "overview" && <Overview groupId={groupId} />}
      {tab === "chat" && <GroupChat groupId={groupId} onRead={() => qc.invalidateQueries({ queryKey: ["groups", groupId] })} />}
      {tab === "announcements" && <Announcements groupId={groupId} manager={canEdit} />}
      {tab === "tasks" && <TasksTab groupId={groupId} canEdit={canEdit} />}
      {tab === "students" && <StudentsTab groupId={groupId} />}
      {tab === "settings" && <SettingsTab group={g} onChanged={() => qc.invalidateQueries({ queryKey: ["groups", groupId] })} />}
      {tab === "audit" && <AuditTab groupId={groupId} />}
    </div>
  );
}
