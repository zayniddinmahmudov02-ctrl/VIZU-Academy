"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Eye, Search } from "lucide-react";

import { EmptyState, ErrorState, fieldClass, Loading, Pager, Panel, StudentStatusBadge, TeacherPageTitle } from "@/components/teacher/teacher-ui";
import { formatDate, formatDateTime, formatDuration } from "@/features/activity/lib/format";
import { useTeacherMe } from "@/features/teacher/hooks/use-teacher-me";
import { getKontrollStudents } from "@/features/teacher/services/teacher-panel.service";
import { useTranslation } from "@/lib/i18n/use-translation";

const SORTS = ["registered", "name", "usage", "last_activity"] as const;

export default function KontrollPage() {
  const { t, language } = useTranslation();
  const me = useTeacherMe();
  const allowed = !!me.data?.can_access_student_control;
  const [search, setSearch] = useState("");
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<(typeof SORTS)[number]>("registered");
  const [page, setPage] = useState(1);

  useEffect(() => {
    const id = window.setTimeout(() => { setQ(search.trim()); setPage(1); }, 300);
    return () => window.clearTimeout(id);
  }, [search]);

  const list = useQuery({
    queryKey: ["kontroll-students", q, sort, page],
    queryFn: () => getKontrollStudents({ search: q || undefined, sort, page, page_size: 25 }),
    enabled: allowed,
    placeholderData: keepPreviousData,
  });

  if (me.isLoading) return <Loading />;
  if (!allowed) {
    return (
      <div data-testid="kontroll-denied">
        <TeacherPageTitle title={t("tpanel.kTitle")} />
        <EmptyState text={t("tpanel.kNoAccess")} />
      </div>
    );
  }

  const cols = ["colId", "colName", "colEmail", "colRegistered", "kColUsage", "colLastActivity", "kColCourses", "kColLessons", "kColMusic", "kColVocab", "kColBooks", "kColFilms"];

  return (
    <div data-testid="kontroll">
      <TeacherPageTitle title={t("tpanel.kTitle")} subtitle={t("tpanel.kSubtitle")} />
      <p className="mb-4 flex items-start gap-2 rounded-2xl bg-accent-gold/10 p-3 text-sm text-text-secondary ring-1 ring-accent-gold/25"><Eye size={16} className="mt-0.5 shrink-0" />{t("tpanel.kReadOnly")}</p>
      <Panel>
        <div className="flex flex-wrap gap-2">
          <label className="relative min-w-[14rem] flex-1">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder={t("tpanel.searchStudents")} aria-label={t("tpanel.search")} className={`${fieldClass} w-full pl-9`} data-testid="kontroll-search" />
          </label>
          <select value={sort} onChange={(e) => { setSort(e.target.value as (typeof SORTS)[number]); setPage(1); }} aria-label={t("tpanel.kSort")} className={fieldClass} data-testid="kontroll-sort">
            {SORTS.map((s) => <option key={s} value={s}>{t(`tpanel.sort_${s}`)}</option>)}
          </select>
        </div>
        <div className="mt-4">
          {list.isLoading && <Loading />}
          {list.isError && <ErrorState onRetry={() => list.refetch()} />}
          {list.data && list.data.items.length === 0 && <EmptyState text={q ? t("tpanel.emptyFilter") : t("tpanel.emptyStudents")} />}
          {list.data && list.data.items.length > 0 && (
            <>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[1100px] text-left text-sm" data-testid="kontroll-table">
                  <thead><tr className="text-xs text-text-muted">{cols.map((k) => <th key={k} className="pb-2 pr-3 font-medium">{t(`tpanel.${k}`)}</th>)}</tr></thead>
                  <tbody className="text-text-secondary">
                    {list.data.items.map((s) => (
                      <tr key={s.id} className="border-t border-surface-border" data-testid="kontroll-row">
                        <td className="py-2 pr-3 font-mono text-xs" title={s.id}>{s.id.slice(0, 8)}</td>
                        <td className="py-2 pr-3"><Link href={`/teacher/kontroll/${s.id}`} className="font-medium text-text-primary hover:text-accent-blue">{s.name}</Link>
                          {s.status !== "active" && <span className="ml-1.5"><StudentStatusBadge status={s.status} /></span>}</td>
                        <td className="max-w-[13rem] truncate py-2 pr-3">{s.email}</td>
                        <td className="whitespace-nowrap py-2 pr-3">{formatDate(s.registered_at, language)}</td>
                        <td className="whitespace-nowrap py-2 pr-3 font-medium text-text-primary">{formatDuration(s.usage_seconds, language)}</td>
                        <td className="whitespace-nowrap py-2 pr-3 text-xs">{s.last_activity_at ? formatDateTime(s.last_activity_at, language) : t("tpanel.never")}</td>
                        <td className="py-2 pr-3">{s.courses_completed}</td>
                        <td className="py-2 pr-3">{s.lessons_completed}</td>
                        <td className="whitespace-nowrap py-2 pr-3">{formatDuration(s.music_seconds, language)}</td>
                        <td className="whitespace-nowrap py-2 pr-3">{formatDuration(s.vocabulary_seconds, language)}</td>
                        <td className="py-2 pr-3">{s.books_viewed}</td>
                        <td className="py-2 pr-3">{s.films_viewed}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pager page={list.data.page} pageSize={list.data.page_size} total={list.data.total} onPage={setPage} />
            </>
          )}
        </div>
      </Panel>
    </div>
  );
}
