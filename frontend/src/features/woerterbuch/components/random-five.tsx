"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Loader2, Shuffle } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { CEFR_LEVELS, drawRandomFive, type CefrLevel, type RandomFive as Draw, type WordCard } from "../woerterbuch-service";
import WordCardView from "./word-card";

/** "Random 5": five distinct words per draw from the chosen level (or all),
 *  unseen words first (the server keeps track); the answer is hidden until
 *  the student reveals it. */
export default function RandomFive() {
  const { t } = useTranslation();
  const [level, setLevel] = useState<CefrLevel | "ALL">("A1");
  const [draw, setDraw] = useState<Draw | null>(null);
  const [round, setRound] = useState(0);

  const next = useMutation({
    mutationFn: () => drawRandomFive(level),
    onSuccess: (data) => {
      setDraw(data);
      setRound((r) => r + 1);
    },
  });

  const update = (w: WordCard) => setDraw((d) => (d ? { ...d, items: d.items.map((i) => (i.id === w.id ? w : i)) } : d));

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 rounded-card bg-surface-card p-4 shadow-[var(--shadow-md)] ring-1 ring-surface-border sm:flex-row sm:items-center sm:justify-between">
        <div role="radiogroup" aria-label={t("woerterbuch.level")} className="flex flex-wrap gap-1.5">
          {([...CEFR_LEVELS, "ALL"] as const).map((l) => (
            <button key={l} type="button" role="radio" aria-checked={level === l} onClick={() => setLevel(l)}
                    className={`rounded-xl px-3.5 py-2 text-sm font-semibold ring-1 transition ${
                      level === l ? "bg-brand-800 text-white ring-brand-800" : "text-brand-800 ring-brand-200 hover:bg-brand-50 dark:text-brand-200 dark:ring-brand-700"}`}>
              {l === "ALL" ? t("woerterbuch.allLevels") : l}
            </button>
          ))}
        </div>
        <button type="button" onClick={() => next.mutate()} disabled={next.isPending} data-testid="wb-random-next"
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-brand-800 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-900 disabled:opacity-50">
          {next.isPending ? <Loader2 size={16} className="animate-spin" /> : <Shuffle size={16} />}
          {draw ? t("woerterbuch.nextFive") : t("woerterbuch.startFive")}
        </button>
      </div>

      {next.isError && <p role="alert" className="rounded-card bg-danger/10 p-4 text-sm text-danger">{t("woerterbuch.loadError")}</p>}

      {!draw ? (
        <p className="rounded-card bg-surface-card p-6 text-text-muted ring-1 ring-surface-border">{t("woerterbuch.randomIntro")}</p>
      ) : (
        <>
          <p className="text-sm text-text-secondary" data-testid="wb-random-info">
            {draw.unseen_before > 0
              ? t("woerterbuch.unseenLeft", { n: Math.max(draw.unseen_before - draw.items.length, 0), total: draw.pool_size })
              : t("woerterbuch.allSeen", { total: draw.pool_size })}
          </p>
          {!draw.complete && (
            <p role="status" className="rounded-card bg-amber-500/10 p-3 text-sm text-amber-800 ring-1 ring-amber-500/30 dark:text-amber-200">
              {t("woerterbuch.fewerThanFive", { n: draw.items.length })}
            </p>
          )}
          <div className="grid gap-4 md:grid-cols-2">
            {draw.items.map((w) => <WordCardView key={`${round}-${w.id}`} word={w} concealed onChange={update} />)}
          </div>
        </>
      )}
    </div>
  );
}
