"use client";

import { useState } from "react";
import { keepPreviousData, useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { Loader2, Search } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { CEFR_LEVELS, getWord, searchWords, type CefrLevel, type DictionaryMeta, type WordBrief } from "../woerterbuch-service";
import { useDebouncedValue } from "../hooks/use-debounced-value";
import WordCardView from "./word-card";

const select = "rounded-xl border border-surface-border bg-surface-card px-3 py-2 text-sm text-text-primary outline-none focus:border-brand-600";

/** Server-side search (debounced, paginated) + the selected word's card. */
export default function SearchPanel({ meta }: { meta?: DictionaryMeta }) {
  const { t } = useTranslation();
  const [query, setQuery] = useState("");
  const [level, setLevel] = useState<CefrLevel | "">("");
  const [pos, setPos] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const q = useDebouncedValue(query.trim(), 300);

  const results = useInfiniteQuery({
    queryKey: ["dictionary", "search", q, level, pos],
    queryFn: ({ pageParam, signal }) => searchWords({ q, level, pos, page: pageParam }, signal),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page * last.page_size < last.total ? last.page + 1 : undefined),
    enabled: q.length > 0,
    placeholderData: keepPreviousData,
  });
  const items: WordBrief[] = results.data?.pages.flatMap((p) => p.items) ?? [];
  const total = results.data?.pages[0]?.total ?? 0;
  const activeId = selected ?? items[0]?.id ?? null;

  const card = useQuery({
    queryKey: ["dictionary", "entry", activeId],
    queryFn: () => getWord(activeId!),
    enabled: !!activeId && q.length > 0,
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-2 rounded-card bg-surface-card p-2 shadow-[var(--shadow-md)] ring-1 ring-surface-border sm:flex-row sm:items-center">
        <label className="flex flex-1 items-center gap-2 px-3">
          <Search size={18} className="shrink-0 text-brand-700" aria-hidden />
          <span className="sr-only">{t("woerterbuch.placeholder")}</span>
          <input value={query} onChange={(e) => { setQuery(e.target.value); setSelected(null); }} type="search" maxLength={80} autoComplete="off"
                 placeholder={t("woerterbuch.placeholder")} data-testid="wb-search"
                 className="w-full bg-transparent py-3 text-lg text-text-primary outline-none placeholder:text-text-muted" />
          {results.isFetching && <Loader2 size={16} className="animate-spin text-text-muted" />}
        </label>
        <div className="flex gap-2 px-2 pb-2 sm:pb-0">
          <select aria-label={t("woerterbuch.level")} className={select} value={level} onChange={(e) => { setLevel(e.target.value as CefrLevel | ""); setSelected(null); }}>
            <option value="">{t("woerterbuch.allLevels")}</option>
            {CEFR_LEVELS.map((l) => <option key={l} value={l}>{l}{meta ? ` (${meta.levels[l]})` : ""}</option>)}
          </select>
          <select aria-label={t("woerterbuch.partOfSpeech")} className={select} value={pos} onChange={(e) => { setPos(e.target.value); setSelected(null); }}>
            <option value="">{t("woerterbuch.allPos")}</option>
            {(meta?.parts_of_speech ?? []).map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
      </div>

      {!q ? (
        <p className="rounded-card bg-surface-card p-6 text-text-muted ring-1 ring-surface-border">{t("woerterbuch.emptyState")}</p>
      ) : results.isError ? (
        <p role="alert" className="rounded-card bg-danger/10 p-4 text-sm text-danger ring-1 ring-danger/20">
          {t("woerterbuch.loadError")}{" "}
          <button type="button" className="font-semibold underline" onClick={() => results.refetch()}>{t("woerterbuch.retry")}</button>
        </p>
      ) : results.isSuccess && total === 0 ? (
        <p className="rounded-card bg-surface-card p-6 text-text-muted ring-1 ring-surface-border" data-testid="wb-no-results">{t("woerterbuch.noResults", { q })}</p>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
          <div className="rounded-card bg-surface-card ring-1 ring-surface-border">
            <p className="border-b border-surface-border px-4 py-2 text-xs text-text-muted">{t("woerterbuch.resultCount", { n: total })}</p>
            <ul className="max-h-[60vh] overflow-y-auto" data-testid="wb-results">
              {items.map((w) => (
                <li key={w.id}>
                  <button type="button" onClick={() => setSelected(w.id)} aria-current={w.id === activeId}
                          className={`flex w-full items-center justify-between gap-3 px-4 py-2.5 text-left hover:bg-brand-50 dark:hover:bg-brand-900/30 ${
                            w.id === activeId ? "bg-brand-50 dark:bg-brand-900/40" : ""}`}>
                    <span className="min-w-0">
                      <span className="block truncate font-semibold text-text-primary">{w.article ? <span className="font-normal text-brand-700 dark:text-brand-300">{w.article} </span> : null}{w.lemma}</span>
                      <span className="block truncate text-sm text-text-secondary">{w.translation}</span>
                    </span>
                    <span className="shrink-0 rounded-full bg-brand-800 px-2 py-0.5 text-[10px] font-bold text-white">{w.cefr_level}</span>
                  </button>
                </li>
              ))}
            </ul>
            {results.hasNextPage && (
              <button type="button" onClick={() => results.fetchNextPage()} disabled={results.isFetchingNextPage}
                      className="w-full border-t border-surface-border py-2.5 text-sm font-semibold text-brand-800 hover:bg-brand-50 disabled:opacity-50 dark:text-brand-200">
                {results.isFetchingNextPage ? t("woerterbuch.loading") : t("woerterbuch.loadMore")}
              </button>
            )}
          </div>
          <div>
            {card.isLoading ? (
              <div className="flex h-40 items-center justify-center rounded-card bg-surface-card ring-1 ring-surface-border"><Loader2 className="animate-spin text-text-muted" /></div>
            ) : card.isError ? (
              <p role="alert" className="rounded-card bg-danger/10 p-4 text-sm text-danger">{t("woerterbuch.loadError")}</p>
            ) : card.data ? (
              <WordCardView key={card.data.id} word={card.data} />
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
