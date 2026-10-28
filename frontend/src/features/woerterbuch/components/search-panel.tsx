"use client";

import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";
import { keepPreviousData, useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { Loader2, Search, Star } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { CEFR_LEVELS, getWord, searchWords, type CefrLevel, type DictionaryMeta, type WordBrief } from "../woerterbuch-service";
import { useDebouncedValue } from "../hooks/use-debounced-value";
import WordCardView, { LevelBadge } from "./word-card";

const select = "rounded-xl border border-surface-border bg-surface-card px-3 py-2 text-sm text-text-primary outline-none focus:border-brand-600";

/** Live search (autocomplete): results update with every letter (short
 *  debounce), words starting with the query first; ↑/↓ move, Enter opens
 *  the word card. Searching and ranking happen on the server, 10 at a time. */
export default function SearchPanel({ meta }: { meta?: DictionaryMeta }) {
  const { t } = useTranslation();
  const listId = useId();
  const [query, setQuery] = useState("");
  const [level, setLevel] = useState<CefrLevel | "">("");
  const [wordType, setWordType] = useState("");
  // the highlighted option belongs to one result list; a new query / filter starts at the top
  const [cursor, setCursor] = useState({ list: "", index: 0 });
  const [selected, setSelected] = useState<string | null>(null);
  const cardRef = useRef<HTMLDivElement>(null);
  const q = useDebouncedValue(query.trim(), 150);

  const results = useInfiniteQuery({
    queryKey: ["dictionary", "search", q, level, wordType],
    queryFn: ({ pageParam, signal }) => searchWords({ q, level, word_type: wordType, page: pageParam }, signal),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page * last.page_size < last.total ? last.page + 1 : undefined),
    enabled: q.length > 0,
    placeholderData: keepPreviousData,
  });
  const items: WordBrief[] = q ? results.data?.pages.flatMap((p) => p.items) ?? [] : [];
  const total = results.data?.pages[0]?.total ?? 0;

  const card = useQuery({ queryKey: ["dictionary", "entry", selected], queryFn: () => getWord(selected!), enabled: !!selected });

  const listKey = `${q}|${level}|${wordType}`;
  const active = cursor.list === listKey ? cursor.index : 0;
  const setActive = (next: number | ((i: number) => number)) =>
    setCursor({ list: listKey, index: typeof next === "function" ? next(active) : next });

  function open(id: string) {
    setSelected(id);
    // on a phone the card is below the list: bring it into view
    requestAnimationFrame(() => cardRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (!items.length) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((i) => Math.min(i + 1, items.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      open(items[Math.min(active, items.length - 1)].id);
    }
  }

  useEffect(() => {
    document.getElementById(`${listId}-${active}`)?.scrollIntoView({ block: "nearest" });
  }, [active, listId]);

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-2 rounded-card bg-surface-card p-2 shadow-[var(--shadow-md)] ring-1 ring-surface-border sm:flex-row sm:items-center">
        <label className="flex flex-1 items-center gap-2 px-3">
          <Search size={18} className="shrink-0 text-brand-700" aria-hidden />
          <span className="sr-only">{t("woerterbuch.placeholder")}</span>
          <input value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={onKeyDown} type="search" maxLength={80}
                 autoComplete="off" autoCorrect="off" autoCapitalize="off" spellCheck={false} enterKeyHint="search"
                 role="combobox" aria-expanded={items.length > 0} aria-controls={listId} aria-autocomplete="list"
                 aria-activedescendant={items.length ? `${listId}-${active}` : undefined}
                 placeholder={t("woerterbuch.placeholder")} data-testid="wb-search"
                 className="w-full bg-transparent py-3 text-lg text-text-primary outline-none placeholder:text-text-muted" />
          {results.isFetching && <Loader2 size={16} className="animate-spin text-text-muted" />}
        </label>
        <div className="flex gap-2 px-2 pb-2 sm:pb-0">
          <select aria-label={t("woerterbuch.level")} className={select} value={level} onChange={(e) => setLevel(e.target.value as CefrLevel | "")}>
            <option value="">{t("woerterbuch.allLevels")}</option>
            {CEFR_LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
          <select aria-label={t("woerterbuch.partOfSpeech")} className={select} value={wordType} onChange={(e) => setWordType(e.target.value)}>
            <option value="">{t("woerterbuch.allPos")}</option>
            {(meta?.word_types ?? []).map((p) => <option key={p} value={p}>{p}</option>)}
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
      ) : results.isSuccess && total === 0 && !results.isPlaceholderData ? (
        <p className="rounded-card bg-surface-card p-6 text-text-muted ring-1 ring-surface-border" data-testid="wb-no-results">{t("woerterbuch.noResults", { q })}</p>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
          <div className="self-start rounded-card bg-surface-card ring-1 ring-surface-border">
            <p className="border-b border-surface-border px-4 py-2 text-xs text-text-muted">{t("woerterbuch.resultCount", { n: total })}</p>
            <ul id={listId} role="listbox" aria-label={t("woerterbuch.results")} className="max-h-[60vh] overflow-y-auto" data-testid="wb-results">
              {items.map((w, i) => (
                <li key={w.id} id={`${listId}-${i}`} role="option" aria-selected={i === active}
                    onClick={() => { setActive(i); open(w.id); }} onMouseEnter={() => setActive(i)}
                    className={`flex cursor-pointer items-center justify-between gap-3 px-4 py-2.5 ${
                      i === active ? "bg-brand-50 dark:bg-brand-900/40" : ""} ${w.id === selected ? "border-l-4 border-brand-700" : ""}`}>
                  <span className="min-w-0">
                    <span className="block truncate font-semibold text-text-primary">
                      {w.article ? <span className="font-normal text-brand-700 dark:text-brand-300">{w.article} </span> : null}{w.lemma}
                    </span>
                    <span className="block truncate text-sm text-text-secondary">{w.translation}</span>
                  </span>
                  <span className="flex shrink-0 items-center gap-2">
                    {w.saved && <Star size={14} className="text-amber-500" fill="currentColor" aria-label={t("woerterbuch.savedMark")} />}
                    <LevelBadge level={w.level} />
                  </span>
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
          <div ref={cardRef} className="scroll-mt-4">
            {!selected ? (
              <p className="rounded-card bg-surface-card p-6 text-sm text-text-muted ring-1 ring-surface-border">{t("woerterbuch.pickHint")}</p>
            ) : card.isLoading ? (
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
