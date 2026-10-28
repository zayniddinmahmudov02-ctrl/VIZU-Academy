"use client";

import { useState } from "react";
import Link from "next/link";
import { keepPreviousData, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Users, UsersRound } from "lucide-react";

import PageHeader from "@/components/dashboard/page-header";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import { createGroup, getTeachingGroups, LEVELS } from "../groups-service";
import GroupForm, { CodeReveal } from "./group-form";
import { card, ErrorBox, fmtDate, input, LevelPill, Loading, primaryBtn, secondaryBtn, StatusPill } from "./ui";

/** Teacher → Gruppen: own groups (server-side search / filters / pages) and creating one. */
export default function TeacherGroups() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const [filters, setFilters] = useState<{ search?: string; level?: string; status?: string; page: number }>({ page: 1 });
  const [creating, setCreating] = useState(false);
  const [created, setCreated] = useState<{ id: string; code: string } | null>(null);
  const list = useQuery({ queryKey: ["groups", "teaching", filters], queryFn: () => getTeachingGroups(filters), placeholderData: keepPreviousData });
  const set = (p: Partial<typeof filters>) => setFilters((f) => ({ ...f, ...p, page: p.page ?? 1 }));
  const pages = list.data ? Math.max(1, Math.ceil(list.data.total / list.data.page_size)) : 1;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <PageHeader icon={UsersRound} titleKey="groups.title" subtitleKey="groups.teacherSubtitle" gradient="from-accent-blue to-purple-600" />
        {!creating && <button type="button" className={primaryBtn} onClick={() => { setCreating(true); setCreated(null); }} data-testid="new-group"><Plus size={16} /> {t("groups.newGroup")}</button>}
      </div>

      {created && (
        <div className="space-y-2">
          <CodeReveal code={created.code} onClose={() => setCreated(null)} />
          <Link href={`/teacher/groups/${created.id}`} className="text-sm font-semibold text-accent-blue">{t("groups.open")} →</Link>
        </div>
      )}
      {creating && (
        <GroupForm onCancel={() => setCreating(false)} onSubmit={async (data) => {
          const res = await createGroup(data);
          setCreating(false);
          setCreated({ id: res.group.id, code: res.code });
          await qc.invalidateQueries({ queryKey: ["groups", "teaching"] });
        }} />
      )}

      <div className={cn(card, "grid gap-3 p-4 sm:grid-cols-3")}>
        <input className={input} placeholder={t("groups.search")} value={filters.search ?? ""} onChange={(e) => set({ search: e.target.value || undefined })} />
        <select className={input} value={filters.level ?? ""} onChange={(e) => set({ level: e.target.value || undefined })}>
          <option value="">{t("groups.allLevels")}</option>{LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
        </select>
        <select className={input} value={filters.status ?? ""} onChange={(e) => set({ status: e.target.value || undefined })}>
          <option value="">{t("groups.allStatuses")}</option>
          {["active", "paused", "archived", "blocked"].map((s) => <option key={s} value={s}>{t(`groups.status_${s}`)}</option>)}
        </select>
      </div>

      {list.isLoading ? <Loading /> : list.isError ? <ErrorBox error={list.error} onRetry={() => list.refetch()} /> : (list.data?.items ?? []).length === 0 ? (
        <p className={cn(card, "p-8 text-center text-sm text-text-muted")}>{t("groups.noTeachingGroups")}</p>
      ) : (
        <div className={cn(card, "overflow-x-auto")}>
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="text-[11px] uppercase tracking-wide text-text-muted">
              <tr className="border-b border-surface-border">
                {[t("groups.name"), t("groups.level"), t("groups.students"), t("groups.code"), t("groups.status"), t("groups.startDate"), t("groups.lastActivity")].map((h) => <th key={h} className="px-4 py-3">{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {list.data!.items.map((g) => (
                <tr key={g.id} className="border-b border-surface-border last:border-0 hover:bg-surface-hover/50">
                  <td className="px-4 py-3"><Link href={`/teacher/groups/${g.id}`} className="font-semibold text-text-primary hover:text-accent-blue">{g.name}</Link>
                    <p className="text-xs text-text-muted">{g.courses.map((c) => c.title).join(", ") || t("groups.noCourses")}</p></td>
                  <td className="px-4 py-3"><LevelPill level={g.level} /></td>
                  <td className="px-4 py-3 text-text-secondary"><span className="inline-flex items-center gap-1"><Users size={13} /> {g.student_count}{g.capacity ? `/${g.capacity}` : ""}</span></td>
                  <td className="px-4 py-3 text-xs text-text-secondary">{g.code ? (g.code.usable ? t("groups.codeUsable") : t("groups.codeNotUsable")) : t("groups.noCode")}</td>
                  <td className="px-4 py-3"><StatusPill status={g.status} /></td>
                  <td className="px-4 py-3 text-xs text-text-secondary">{fmtDate(g.start_date)}</td>
                  <td className="px-4 py-3 text-xs text-text-secondary">{fmtDate(g.last_activity_at, true)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {pages > 1 && (
            <div className="flex items-center gap-2 p-3 text-sm text-text-secondary">
              <button type="button" className={secondaryBtn} disabled={filters.page <= 1} onClick={() => set({ page: filters.page - 1 })}>←</button>
              {filters.page} / {pages}
              <button type="button" className={secondaryBtn} disabled={filters.page >= pages} onClick={() => set({ page: filters.page + 1 })}>→</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
