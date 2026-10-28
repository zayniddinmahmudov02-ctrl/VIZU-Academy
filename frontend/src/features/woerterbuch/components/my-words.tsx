"use client";

import { useState } from "react";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { getMyWords, getWord } from "../woerterbuch-service";
import WordCardView from "./word-card";

type Kind = "saved" | "unknown" | "known";

/** The student's own lists: saved words and the words marked known / not known
 *  (the "not known" list is the review list). */
export default function MyWords() {
  const { t } = useTranslation();
  const [kind, setKind] = useState<Kind>("saved");
  const [selected, setSelected] = useState<string | null>(null);

  const list = useInfiniteQuery({
    queryKey: ["dictionary", "my", kind],
    queryFn: ({ pageParam }) => getMyWords(kind, pageParam),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page * last.page_size < last.total ? last.page + 1 : undefined),
  });
  const items = list.data?.pages.flatMap((p) => p.items) ?? [];
  const summary = list.data?.pages[0]?.summary;
  const activeId = selected && items.some((i) => i.id === selected) ? selected : items[0]?.id ?? null;
  const card = useQuery({ queryKey: ["dictionary", "entry", activeId], queryFn: () => getWord(activeId!), enabled: !!activeId });

  return (
    <div className="space-y-4">
      <div role="tablist" className="flex flex-wrap gap-1.5">
        {(["saved", "unknown", "known"] as const).map((k) => (
          <button key={k} type="button" role="tab" aria-selected={kind === k} onClick={() => { setKind(k); setSelected(null); }}
                  className={`rounded-xl px-3.5 py-2 text-sm font-semibold ring-1 ${
                    kind === k ? "bg-brand-800 text-white ring-brand-800" : "text-brand-800 ring-brand-200 hover:bg-brand-50 dark:text-brand-200 dark:ring-brand-700"}`}>
            {t(`woerterbuch.my_${k}`)}{summary ? ` (${summary[k]})` : ""}
          </button>
        ))}
        {summary && <span className="self-center text-xs text-text-muted">{t("woerterbuch.seenTotal", { n: summary.seen })}</span>}
      </div>

      {list.isLoading ? (
        <div className="flex h-32 items-center justify-center"><Loader2 className="animate-spin text-text-muted" /></div>
      ) : list.isError ? (
        <p role="alert" className="rounded-card bg-danger/10 p-4 text-sm text-danger">{t("woerterbuch.loadError")}</p>
      ) : items.length === 0 ? (
        <p className="rounded-card bg-surface-card p-6 text-text-muted ring-1 ring-surface-border">{t(`woerterbuch.my_empty_${kind}`)}</p>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
          <div className="rounded-card bg-surface-card ring-1 ring-surface-border">
            <ul className="max-h-[60vh] overflow-y-auto">
              {items.map((w) => (
                <li key={w.id}>
                  <button type="button" onClick={() => setSelected(w.id)} aria-current={w.id === activeId}
                          className={`flex w-full items-center justify-between gap-3 px-4 py-2.5 text-left hover:bg-brand-50 dark:hover:bg-brand-900/30 ${w.id === activeId ? "bg-brand-50 dark:bg-brand-900/40" : ""}`}>
                    <span className="min-w-0">
                      <span className="block truncate font-semibold text-text-primary">{w.article ? `${w.article} ` : ""}{w.lemma}</span>
                      <span className="block truncate text-sm text-text-secondary">{w.translation}</span>
                    </span>
                    <span className="shrink-0 rounded-full bg-brand-800 px-2 py-0.5 text-[10px] font-bold text-white">{w.cefr_level}</span>
                  </button>
                </li>
              ))}
            </ul>
            {list.hasNextPage && (
              <button type="button" onClick={() => list.fetchNextPage()} disabled={list.isFetchingNextPage}
                      className="w-full border-t border-surface-border py-2.5 text-sm font-semibold text-brand-800 hover:bg-brand-50 disabled:opacity-50 dark:text-brand-200">
                {t("woerterbuch.loadMore")}
              </button>
            )}
          </div>
          <div>{card.data && <WordCardView key={card.data.id} word={card.data} />}</div>
        </div>
      )}
    </div>
  );
}
