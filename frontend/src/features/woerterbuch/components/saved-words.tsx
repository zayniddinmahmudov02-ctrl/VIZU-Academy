"use client";

import { useRef, useState } from "react";
import { keepPreviousData, useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { Loader2, Search } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { CEFR_LEVELS, getSavedWords, getWord, type CefrLevel } from "../woerterbuch-service";
import { useDebouncedValue } from "../hooks/use-debounced-value";
import WordCardView, { LevelBadge, StarButton } from "./word-card";

/** "Gespeicherte Wörter": the student's starred words — search, level filter,
 *  page by page; un-starring removes a word from the list. */
export default function SavedWords() {
  const { t } = useTranslation();
  const [query, setQuery] = useState("");
  const [level, setLevel] = useState<CefrLevel | "">("");
  const [selected, setSelected] = useState<string | null>(null);
  const cardRef = useRef<HTMLDivElement>(null);
  const q = useDebouncedValue(query.trim(), 250);

  const list = useInfiniteQuery({
    queryKey: ["dictionary", "saved", q, level],
    queryFn: ({ pageParam, signal }) => getSavedWords({ q, level, page: pageParam }, signal),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page * last.page_size < last.total ? last.page + 1 : undefined),
    placeholderData: keepPreviousData,
  });
  const items = list.data?.pages.flatMap((p) => p.items) ?? [];
  const byLevel = list.data?.pages[0]?.by_level;
  const all = byLevel ? Object.values(byLevel).reduce((a, b) => a + b, 0) : undefined;
  const card = useQuery({ queryKey: ["dictionary", "entry", selected], queryFn: () => getWord(selected!), enabled: !!selected });

  const chip = (active: boolean) =>
    `rounded-xl px-3 py-1.5 text-sm font-semibold ring-1 transition ${
      active ? "bg-brand-800 text-white ring-brand-800" : "text-brand-800 ring-brand-200 hover:bg-brand-50 dark:text-brand-200 dark:ring-brand-700"}`;

  return (
    <div className="space-y-4">
      <div className="space-y-3 rounded-card bg-surface-card p-3 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        <label className="flex items-center gap-2 px-2">
          <Search size={18} className="shrink-0 text-brand-700" aria-hidden />
          <span className="sr-only">{t("woerterbuch.savedSearch")}</span>
          <input value={query} onChange={(e) => setQuery(e.target.value)} type="search" maxLength={80} autoComplete="off"
                 placeholder={t("woerterbuch.savedSearch")} data-testid="wb-saved-search"
                 className="w-full bg-transparent py-2 text-base text-text-primary outline-none placeholder:text-text-muted" />
          {list.isFetching && <Loader2 size={16} className="animate-spin text-text-muted" />}
        </label>
        <div role="radiogroup" aria-label={t("woerterbuch.level")} className="flex flex-wrap gap-1.5">
          <button type="button" role="radio" aria-checked={level === ""} onClick={() => setLevel("")} className={chip(level === "")}>
            {t("woerterbuch.allLevels")}{all !== undefined ? ` (${all})` : ""}
          </button>
          {CEFR_LEVELS.map((l) => (
            <button key={l} type="button" role="radio" aria-checked={level === l} onClick={() => setLevel(l)} className={chip(level === l)}>
              {l}{byLevel ? ` (${byLevel[l]})` : ""}
            </button>
          ))}
        </div>
      </div>

      {list.isLoading ? (
        <div className="flex h-32 items-center justify-center"><Loader2 className="animate-spin text-text-muted" /></div>
      ) : list.isError ? (
        <p role="alert" className="rounded-card bg-danger/10 p-4 text-sm text-danger">
          {t("woerterbuch.loadError")}{" "}
          <button type="button" className="font-semibold underline" onClick={() => list.refetch()}>{t("woerterbuch.retry")}</button>
        </p>
      ) : items.length === 0 ? (
        <p className="rounded-card bg-surface-card p-6 text-text-muted ring-1 ring-surface-border" data-testid="wb-saved-empty">
          {q || level ? t("woerterbuch.savedNoMatch") : t("woerterbuch.savedEmpty")}
        </p>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
          <div className="self-start rounded-card bg-surface-card ring-1 ring-surface-border">
            <p className="border-b border-surface-border px-4 py-2 text-xs text-text-muted">{t("woerterbuch.resultCount", { n: list.data?.pages[0]?.total ?? 0 })}</p>
            <ul className="max-h-[60vh] overflow-y-auto" data-testid="wb-saved-list">
              {items.map((w) => (
                <li key={w.id} className={`flex items-center gap-2 px-2 ${w.id === selected ? "bg-brand-50 dark:bg-brand-900/40" : ""}`}>
                  <button type="button" onClick={() => { setSelected(w.id); requestAnimationFrame(() => cardRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })); }}
                          aria-current={w.id === selected}
                          className="flex min-w-0 flex-1 items-center justify-between gap-3 rounded-lg px-2 py-2.5 text-left hover:bg-brand-50 dark:hover:bg-brand-900/30">
                    <span className="min-w-0">
                      <span className="block truncate font-semibold text-text-primary">{w.article ? `${w.article} ` : ""}{w.lemma}</span>
                      <span className="block truncate text-sm text-text-secondary">{w.translation}</span>
                    </span>
                    <LevelBadge level={w.level} />
                  </button>
                  <StarButton word={w} />
                </li>
              ))}
            </ul>
            {list.hasNextPage && (
              <button type="button" onClick={() => list.fetchNextPage()} disabled={list.isFetchingNextPage}
                      className="w-full border-t border-surface-border py-2.5 text-sm font-semibold text-brand-800 hover:bg-brand-50 disabled:opacity-50 dark:text-brand-200">
                {list.isFetchingNextPage ? t("woerterbuch.loading") : t("woerterbuch.loadMore")}
              </button>
            )}
          </div>
          <div ref={cardRef} className="scroll-mt-4">
            {!selected ? (
              <p className="rounded-card bg-surface-card p-6 text-sm text-text-muted ring-1 ring-surface-border">{t("woerterbuch.pickHint")}</p>
            ) : card.isLoading ? (
              <div className="flex h-40 items-center justify-center rounded-card bg-surface-card ring-1 ring-surface-border"><Loader2 className="animate-spin text-text-muted" /></div>
            ) : card.data ? (
              <WordCardView key={card.data.id} word={card.data} />
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
