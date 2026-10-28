"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Shuffle } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { CEFR_LEVELS, drawRandomFive, type CefrLevel } from "../woerterbuch-service";
import { CompactWordCard, WordModal } from "./word-card";

/** "Random Wörter": five different words per draw — one from each level when
 *  mixed; the server avoids words this student saw in the last days. The set
 *  lives in the query cache so a star click elsewhere updates it too. */
export default function RandomFive() {
  const { t } = useTranslation();
  const [level, setLevel] = useState<CefrLevel | "ALL">("ALL");
  const [open, setOpen] = useState<string | null>(null);
  const draw = useQuery({
    queryKey: ["dictionary", "random"],
    queryFn: () => drawRandomFive(level),
    enabled: false,
    staleTime: Infinity,
    gcTime: Infinity,
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 rounded-card bg-surface-card p-4 shadow-[var(--shadow-md)] ring-1 ring-surface-border sm:flex-row sm:items-center sm:justify-between">
        <div role="radiogroup" aria-label={t("woerterbuch.level")} className="flex flex-wrap gap-1.5">
          {(["ALL", ...CEFR_LEVELS] as const).map((l) => (
            <button key={l} type="button" role="radio" aria-checked={level === l} onClick={() => setLevel(l)}
                    className={`rounded-xl px-3.5 py-2 text-sm font-semibold ring-1 transition ${
                      level === l ? "bg-brand-800 text-white ring-brand-800" : "text-brand-800 ring-brand-200 hover:bg-brand-50 dark:text-brand-200 dark:ring-brand-700"}`}>
              {l === "ALL" ? t("woerterbuch.mixedLevels") : l}
            </button>
          ))}
        </div>
        <button type="button" onClick={() => draw.refetch()} disabled={draw.isFetching} data-testid="wb-random-next"
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-brand-800 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-900 disabled:opacity-50">
          {draw.isFetching ? <Loader2 size={16} className="animate-spin" /> : <Shuffle size={16} />}
          {draw.data ? t("woerterbuch.nextFive") : t("woerterbuch.startFive")}
        </button>
      </div>

      {draw.isError && <p role="alert" className="rounded-card bg-danger/10 p-4 text-sm text-danger">{t("woerterbuch.loadError")}</p>}

      {!draw.data ? (
        <p className="rounded-card bg-surface-card p-6 text-text-muted ring-1 ring-surface-border">{t("woerterbuch.randomIntro")}</p>
      ) : (
        <>
          {!draw.data.complete && (
            <p role="status" className="rounded-card bg-amber-500/10 p-3 text-sm text-amber-800 ring-1 ring-amber-500/30 dark:text-amber-200">
              {t("woerterbuch.fewerThanFive", { n: draw.data.items.length })}
            </p>
          )}
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {draw.data.items.map((w) => <CompactWordCard key={w.id} word={w} onOpen={() => setOpen(w.id)} />)}
          </div>
        </>
      )}
      {open && <WordModal id={open} onClose={() => setOpen(null)} />}
    </div>
  );
}
