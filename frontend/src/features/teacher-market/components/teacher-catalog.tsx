"use client";

import { useState } from "react";
import Link from "next/link";
import { useInfiniteQuery } from "@tanstack/react-query";
import { BookOpenCheck, Radio, Search } from "lucide-react";

import { EmptyState, ErrorState, Loading, TeacherPageTitle } from "@/components/teacher/teacher-ui";
import { useDebounced } from "@/features/medien/components/media-ui";
import { useTranslation } from "@/lib/i18n/use-translation";

import { getCatalog, type CatalogFilters } from "../services/market-service";
import { LANGUAGES, LEVELS } from "../types";
import { TeacherPhoto, buttonSecondary, inputClass } from "./ui";

const PAGE_SIZE = 24;

/** My Teacher catalog: portrait cards (photo 9:16 + name only), name search, a few filters, "load more" pages. */
export default function TeacherCatalog() {
  const { t } = useTranslation();
  const [q, setQ] = useState("");
  const [filters, setFilters] = useState<Omit<CatalogFilters, "q" | "page">>({});
  const query = useDebounced(q.trim());
  const list = useInfiniteQuery({
    queryKey: ["my-teacher-catalog", query, filters],
    queryFn: ({ pageParam }) => getCatalog({ ...filters, q: query || undefined, page: pageParam, page_size: PAGE_SIZE }),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page * last.page_size < last.total ? last.page + 1 : undefined),
  });
  const items = list.data?.pages.flatMap((p) => p.items) ?? [];
  const set = (key: keyof typeof filters, value: string) => setFilters((f) => ({ ...f, [key]: value || undefined }));
  const filtered = !!(query || Object.values(filters).some(Boolean));

  return (
    <div data-testid="my-teacher-catalog">
      <TeacherPageTitle title={t("market.title")} subtitle={t("market.subtitle")} actions={
        <>
          <Link href="/my-teacher/live" className={buttonSecondary} data-testid="link-live"><Radio size={16} /> {t("market.liveLessons")}</Link>
          <Link href="/my-teacher/meine-kurse" className={buttonSecondary} data-testid="link-my-courses"><BookOpenCheck size={16} /> {t("market.myCourses")}</Link>
        </>
      } />

      <div className="mb-6 grid gap-2 sm:grid-cols-2 lg:grid-cols-[minmax(0,2fr)_repeat(4,minmax(0,1fr))]">
        <label className="relative sm:col-span-2 lg:col-span-1">
          <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" aria-hidden />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("market.search")} aria-label={t("market.search")}
                 className={`${inputClass} pl-9`} data-testid="catalog-search" maxLength={100} />
        </label>
        <select className={inputClass} value={filters.language ?? ""} onChange={(e) => set("language", e.target.value)} aria-label={t("market.filterLanguage")}
                data-testid="filter-language">
          <option value="">{t("market.filterLanguage")}: {t("market.all")}</option>
          {LANGUAGES.map((l) => <option key={l} value={l}>{l}</option>)}
        </select>
        <select className={inputClass} value={filters.level ?? ""} onChange={(e) => set("level", e.target.value)} aria-label={t("market.filterLevel")}
                data-testid="filter-level">
          <option value="">{t("market.filterLevel")}: {t("market.all")}</option>
          {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
        </select>
        <select className={inputClass} value={filters.courses ?? ""} onChange={(e) => set("courses", e.target.value)} aria-label={t("market.filterCourses")}
                data-testid="filter-courses">
          <option value="">{t("market.filterCourses")}: {t("market.all")}</option>
          <option value="open">{t("market.coursesOpen")}</option>
          <option value="any">{t("market.coursesAny")}</option>
        </select>
        <select className={inputClass} value={filters.activity ?? ""} onChange={(e) => set("activity", e.target.value)} aria-label={t("market.filterActivity")}
                data-testid="filter-activity">
          <option value="">{t("market.filterActivity")}: {t("market.all")}</option>
          <option value="teaching">{t("market.activityTeaching")}</option>
        </select>
      </div>

      {list.isLoading ? <Loading /> : list.isError ? <ErrorState onRetry={() => list.refetch()} /> : items.length === 0 ? (
        <EmptyState text={t("market.noTeachers")} testId="catalog-empty">
          {filtered && <button type="button" className="text-sm font-medium text-accent-blue underline" onClick={() => { setQ(""); setFilters({}); }}>
            {t("market.resetFilters")}</button>}
        </EmptyState>
      ) : (
        <>
          <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 lg:grid-cols-4 xl:grid-cols-5" data-testid="teacher-grid">
            {items.map((teacher) => (
              <li key={teacher.id}>
                <Link href={`/my-teacher/${teacher.id}`} data-testid="teacher-card"
                      className="group block rounded-3xl bg-surface-card p-2 shadow-[var(--shadow-md)] ring-1 ring-surface-border transition duration-200 hover:-translate-y-1 hover:shadow-[var(--shadow-lg)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-blue">
                  <TeacherPhoto url={teacher.photo_url} name={teacher.name} className="transition duration-300 group-hover:brightness-105" />
                  <p className="truncate px-1.5 pb-1 pt-2.5 text-center text-sm font-semibold text-text-primary sm:text-base" data-testid="teacher-card-name">
                    {teacher.name}
                  </p>
                </Link>
              </li>
            ))}
          </ul>
          {list.hasNextPage && (
            <div className="mt-6 flex justify-center">
              <button type="button" className={buttonSecondary} onClick={() => list.fetchNextPage()} disabled={list.isFetchingNextPage} data-testid="catalog-more">
                {t("market.loadMore")}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
