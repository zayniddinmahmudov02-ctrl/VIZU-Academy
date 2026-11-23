"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";

import { EmptyState, ErrorState, fieldClass, Loading, Pager, Panel, StudentStatusBadge, TeacherPageTitle } from "@/components/teacher/teacher-ui";
import { formatDate, formatDateTime } from "@/features/activity/lib/format";
import type { RosterFilters } from "@/features/teacher/panel-types";
import { getRoster } from "@/features/teacher/services/teacher-panel.service";
import { useTranslation } from "@/lib/i18n/use-translation";

const LEVELS = ["A1", "A2", "B1", "B2", "C1"];

export default function TeacherStudentsPage() {
  const { t, language } = useTranslation();
  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");
  const [filters, setFilters] = useState<RosterFilters>({ page: 1, page_size: 25 });

  useEffect(() => {
    const id = window.setTimeout(() => setDebounced(search.trim()), 300);
    return () => window.clearTimeout(id);
  }, [search]);

  const params = { ...filters, search: debounced || undefined };
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ["teacher-roster", params], queryFn: () => getRoster(params), placeholderData: keepPreviousData });
  const set = (patch: RosterFilters) => setFilters((f) => ({ ...f, ...patch, page: patch.page ?? 1 }));
  const filtered = !!(debounced || filters.group_id || filters.course_id || filters.level || filters.status || filters.activity || filters.registered_from || filters.registered_to);

  return (
    <div data-testid="teacher-students">
      <TeacherPageTitle title={t("tpanel.studentsTitle")} subtitle={t("tpanel.studentsSubtitle")} />
      <Panel>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          <label className="relative sm:col-span-2">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input value={search} onChange={(e) => { setSearch(e.target.value); set({}); }} placeholder={t("tpanel.searchStudents")} aria-label={t("tpanel.search")}
                   className={`${fieldClass} w-full pl-9`} data-testid="roster-search" />
          </label>
          <select aria-label={t("tpanel.filterGroup")} value={filters.group_id ?? ""} onChange={(e) => set({ group_id: e.target.value || undefined })} className={fieldClass} data-testid="roster-group">
            <option value="">{t("tpanel.filterGroup")}: {t("tpanel.all")}</option>
            {data?.filters.groups.map((g) => <option key={g.id} value={g.id}>{g.name} ({g.level})</option>)}
          </select>
          <select aria-label={t("tpanel.filterCourse")} value={filters.course_id ?? ""} onChange={(e) => set({ course_id: e.target.value || undefined })} className={fieldClass} data-testid="roster-course">
            <option value="">{t("tpanel.filterCourse")}: {t("tpanel.all")}</option>
            {data?.filters.courses.map((c) => <option key={c.id} value={c.id}>{c.level} · {c.title}</option>)}
          </select>
          <select aria-label={t("tpanel.filterLevel")} value={filters.level ?? ""} onChange={(e) => set({ level: e.target.value || undefined })} className={fieldClass} data-testid="roster-level">
            <option value="">{t("tpanel.filterLevel")}: {t("tpanel.all")}</option>
            {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
          <select aria-label={t("tpanel.filterStatus")} value={filters.status ?? ""} onChange={(e) => set({ status: e.target.value || undefined })} className={fieldClass} data-testid="roster-status">
            <option value="">{t("tpanel.filterStatus")}: {t("tpanel.all")}</option>
            {["active", "inactive", "blocked"].map((s) => <option key={s} value={s}>{t(`tpanel.status_${s}`)}</option>)}
          </select>
          <select aria-label={t("tpanel.filterActivity")} value={filters.activity ?? ""} onChange={(e) => set({ activity: e.target.value || undefined })} className={fieldClass} data-testid="roster-activity">
            <option value="">{t("tpanel.filterActivity")}: {t("tpanel.all")}</option>
            <option value="7d">{t("tpanel.act7d")}</option>
            <option value="30d">{t("tpanel.act30d")}</option>
            <option value="inactive">{t("tpanel.actInactive")}</option>
            <option value="never">{t("tpanel.actNever")}</option>
          </select>
          <label className="flex items-center gap-2 text-xs text-text-muted">{t("tpanel.filterFrom")}
            <input type="date" value={filters.registered_from ?? ""} onChange={(e) => set({ registered_from: e.target.value || undefined })} className={`${fieldClass} min-w-0 flex-1`} />
          </label>
          <label className="flex items-center gap-2 text-xs text-text-muted">{t("tpanel.filterTo")}
            <input type="date" value={filters.registered_to ?? ""} onChange={(e) => set({ registered_to: e.target.value || undefined })} className={`${fieldClass} min-w-0 flex-1`} />
          </label>
        </div>
        {filtered && (
          <button type="button" className="mt-2 text-sm font-medium text-accent-blue" onClick={() => { setSearch(""); setFilters({ page: 1, page_size: 25 }); }}>{t("tpanel.resetFilters")}</button>
        )}

        <div className="mt-4">
          {isLoading && <Loading />}
          {isError && <ErrorState onRetry={() => refetch()} />}
          {data && data.items.length === 0 && <EmptyState text={filtered ? t("tpanel.emptyFilter") : t("tpanel.emptyStudents")} testId="roster-empty" />}
          {data && data.items.length > 0 && (
            <>
              <div className="hidden overflow-x-auto md:block">
                <table className="w-full text-left text-sm" data-testid="roster-table">
                  <thead>
                    <tr className="text-xs text-text-muted">
                      {["colId", "colName", "colEmail", "colGroup", "colCourse", "colLevel", "colRegistered", "colStatus", "colLastActivity"].map((k) => (
                        <th key={k} className="pb-2 pr-3 font-medium">{t(`tpanel.${k}`)}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="text-text-secondary">
                    {data.items.map((s) => (
                      <tr key={s.id} className="border-t border-surface-border align-top" data-testid="roster-row">
                        <td className="py-2 pr-3 font-mono text-xs" title={s.id}>{s.id.slice(0, 8)}</td>
                        <td className="py-2 pr-3"><Link href={`/teacher/students/${s.id}`} className="font-medium text-text-primary hover:text-accent-blue">{s.name}</Link></td>
                        <td className="max-w-[14rem] truncate py-2 pr-3">{s.email}</td>
                        <td className="py-2 pr-3">{s.groups.map((g) => <span key={g.id} className="mb-1 mr-1 inline-block rounded-full bg-surface-hover px-2 py-0.5 text-xs">{g.name}</span>)}{!s.groups.length && "—"}</td>
                        <td className="py-2 pr-3 text-xs">{s.courses.map((c) => c.title).join(", ") || "—"}</td>
                        <td className="py-2 pr-3">{s.levels.join(", ") || "—"}</td>
                        <td className="py-2 pr-3 whitespace-nowrap">{formatDate(s.registered_at, language)}</td>
                        <td className="py-2 pr-3"><StudentStatusBadge status={s.status} /></td>
                        <td className="py-2 pr-3 whitespace-nowrap text-xs">{s.last_activity_at ? formatDateTime(s.last_activity_at, language) : t("tpanel.never")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <ul className="space-y-2 md:hidden">
                {data.items.map((s) => (
                  <li key={s.id}>
                    <Link href={`/teacher/students/${s.id}`} className="block rounded-xl p-3 ring-1 ring-surface-border hover:bg-surface-hover" data-testid="roster-card">
                      <span className="flex items-center justify-between gap-2"><span className="truncate font-medium text-text-primary">{s.name}</span><StudentStatusBadge status={s.status} /></span>
                      <span className="block truncate text-xs text-text-muted">{s.email}</span>
                      <span className="mt-1 block text-xs text-text-secondary">{s.groups.map((g) => g.name).join(", ") || "—"} · {s.levels.join(", ")}</span>
                      <span className="block text-xs text-text-muted">{t("tpanel.colLastActivity")}: {s.last_activity_at ? formatDateTime(s.last_activity_at, language) : t("tpanel.never")}</span>
                    </Link>
                  </li>
                ))}
              </ul>
              <Pager page={data.page} pageSize={data.page_size} total={data.total} onPage={(page) => setFilters((f) => ({ ...f, page }))} />
            </>
          )}
        </div>
      </Panel>
    </div>
  );
}
