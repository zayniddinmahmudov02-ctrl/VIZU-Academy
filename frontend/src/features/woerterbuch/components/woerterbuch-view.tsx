"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BookText, Bookmark, Search, Shuffle } from "lucide-react";

import PageHeader from "@/components/dashboard/page-header";
import { useTranslation } from "@/lib/i18n/use-translation";
import { getDictionaryMeta } from "../woerterbuch-service";
import MyWords from "./my-words";
import RandomFive from "./random-five";
import SearchPanel from "./search-panel";

const TABS = [
  { id: "search", icon: Search, key: "woerterbuch.tabSearch" },
  { id: "random", icon: Shuffle, key: "woerterbuch.tabRandom" },
  { id: "my", icon: Bookmark, key: "woerterbuch.tabMine" },
] as const;

type Tab = (typeof TABS)[number]["id"];

export default function WoerterbuchView() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<Tab>("search");
  const meta = useQuery({ queryKey: ["dictionary", "meta"], queryFn: getDictionaryMeta, staleTime: 10 * 60_000 });

  return (
    <div className="space-y-6">
      <PageHeader icon={BookText} titleKey="woerterbuch.title" subtitleKey="woerterbuch.subtitle" gradient="from-brand-900 to-brand-600" />

      <div role="tablist" aria-label={t("woerterbuch.title")} className="flex gap-1 overflow-x-auto rounded-card bg-surface-card p-1 ring-1 ring-surface-border">
        {TABS.map(({ id, icon: Icon, key }) => (
          <button key={id} type="button" role="tab" aria-selected={tab === id} onClick={() => setTab(id)} data-testid={`wb-tab-${id}`}
                  className={`inline-flex flex-1 items-center justify-center gap-2 whitespace-nowrap rounded-xl px-4 py-2.5 text-sm font-semibold transition ${
                    tab === id ? "bg-brand-800 text-white shadow" : "text-text-secondary hover:bg-brand-50 hover:text-brand-800 dark:hover:bg-brand-900/30"}`}>
            <Icon size={16} /> {t(key)}
          </button>
        ))}
      </div>

      <div role="tabpanel">
        {tab === "search" && <SearchPanel meta={meta.data} />}
        {tab === "random" && <RandomFive />}
        {tab === "my" && <MyWords />}
      </div>

      {meta.data && (
        <p className="text-center text-[11px] text-text-muted">
          {t("woerterbuch.footer", { total: meta.data.total })}{" "}
          <a href={meta.data.attribution.url} target="_blank" rel="noopener noreferrer" className="underline-offset-2 hover:underline">
            {meta.data.attribution.name} ({meta.data.attribution.license})
          </a>
        </p>
      )}
    </div>
  );
}
