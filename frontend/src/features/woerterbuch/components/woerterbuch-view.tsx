"use client";

import { BookText, Search } from "lucide-react";

import { useWoerterbuch } from "../hooks/use-woerterbuch";
import PageHeader from "@/components/dashboard/page-header";
import { useTranslation } from "@/lib/i18n/use-translation";

export default function WoerterbuchView() {
  const { t } = useTranslation();
  const { query, setQuery, result, search } = useWoerterbuch();

  return (
    <div className="space-y-8">
      <PageHeader
        icon={BookText}
        titleKey="woerterbuch.title"
        subtitleKey="woerterbuch.subtitle"
        gradient="from-emerald-600 to-emerald-400"
      />

      {/* Search bar */}
      <div className="mx-auto flex w-full items-center gap-2 rounded-card bg-surface-card p-2 shadow-[var(--shadow-md)] ring-1 ring-surface-border sm:w-[65%]">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && search()}
          type="text"
          placeholder={t("woerterbuch.placeholder")}
          className="w-full bg-transparent px-4 py-3 text-lg text-text-primary outline-none placeholder:text-text-muted"
        />
        <button
          type="button"
          onClick={search}
          disabled={!query.trim()}
          className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-button bg-gradient-to-r from-emerald-600 to-emerald-400 px-6 py-3 text-sm font-semibold text-white shadow-md shadow-emerald-600/25 transition enabled:hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Search size={16} />
          {t("woerterbuch.search")}
        </button>
      </div>

      {/* Result card */}
      <div className="rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        {result ? (
          <div className="space-y-4">
            <div className="flex items-baseline gap-2 border-b border-surface-border pb-4">
              {result.article && (
                <span className="text-lg font-medium text-text-secondary">{result.article}</span>
              )}
              <h2 className="text-2xl font-bold text-text-primary">{result.word}</h2>
            </div>

            <dl className="grid gap-4 sm:grid-cols-2">
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-text-muted">
                  {t("woerterbuch.plural")}
                </dt>
                <dd className="mt-1 text-text-primary">{result.plural ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-text-muted">
                  {t("woerterbuch.translation")}
                </dt>
                <dd className="mt-1 text-text-primary">{result.translation}</dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-text-muted">
                  {t("woerterbuch.partOfSpeech")}
                </dt>
                <dd className="mt-1 text-text-primary">{result.partOfSpeech}</dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-text-muted">
                  {t("woerterbuch.level")}
                </dt>
                <dd className="mt-1 text-text-primary">{result.cefrLevel}</dd>
              </div>
            </dl>

            {result.exampleSentence && (
              <div className="border-t border-surface-border pt-4">
                <dt className="text-xs font-semibold uppercase tracking-wide text-text-muted">
                  {t("woerterbuch.example")}
                </dt>
                <dd className="mt-1 text-text-primary italic">{result.exampleSentence}</dd>
              </div>
            )}
          </div>
        ) : (
          <p className="text-text-muted">{t("woerterbuch.emptyState")}</p>
        )}
      </div>
    </div>
  );
}
