"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpen, Check, Copy, Loader2, Search, Star, Volume2, X } from "lucide-react";

import { getWord, searchWords, setWordSaved, type WordBrief, type WordCard } from "@/features/woerterbuch/woerterbuch-service";
import { useSpeech } from "@/features/woerterbuch/hooks/use-speech";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import { lookupWord } from "../services/medien-service";
import type { WordPick } from "./subtitle-overlay";

const label = (e: { article: string | null; lemma: string }) => (e.article ? `${e.article} ${e.lemma}` : e.lemma);

async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    const area = document.createElement("textarea");
    area.value = text;
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    const ok = document.execCommand("copy");
    area.remove();
    return ok;
  }
}

/** The small card that opens when a word (or phrase) of a German subtitle is clicked: translation, article, word type, example from the
 * Wörterbuch; save (the Wörterbuch star = the student's saved words), copy, pronounce. Nothing is translated or guessed here — a word that is
 * not in the dictionary shows similar entries as suggestions only, and a search. */
export default function WordPopup({ pick, onClose }: { pick: WordPick; onClose: () => void }) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { speak, speakingKey, error: speechError } = useSpeech();
  const [word, setWord] = useState(pick.word);
  const [chosen, setChosen] = useState<string | null>(null); // a suggestion / search result opened as card
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState("");
  const [copied, setCopied] = useState<"word" | "sentence" | null>(null);
  const [saving, setSaving] = useState(false);
  const [savedOverride, setSavedOverride] = useState<Record<string, boolean>>({});

  const lookup = useQuery({ queryKey: ["medien-lookup", word.toLowerCase()], queryFn: () => lookupWord(word), staleTime: 5 * 60_000, retry: 1 });
  const picked = useQuery({ queryKey: ["dictionary", "entry", chosen], queryFn: () => getWord(chosen!), enabled: !!chosen });
  const found = useQuery({ queryKey: ["medien-lookup-search", submitted], queryFn: () => searchWords({ q: submitted }), enabled: submitted.length >= 2 });

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") { e.stopPropagation(); onClose(); } };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [onClose]);

  const entries: WordCard[] = picked.data ? [picked.data] : lookup.data?.entries ?? [];
  const entry = entries[0];
  const isSaved = (e: WordCard) => savedOverride[e.id] ?? e.saved;
  const suggestions: WordBrief[] = lookup.data?.status === "similar" ? lookup.data.suggestions : [];
  const none = !lookup.isLoading && !lookup.isError && !entry && !suggestions.length;
  const words = pick.phrase ? Array.from(new Set(pick.word.split(/\s+/).map((w) => w.replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, "")).filter(Boolean))) : [];

  async function toggleSave(e: WordCard) {
    setSaving(true);
    try {
      const res = await setWordSaved(e.id, !isSaved(e));
      setSavedOverride((m) => ({ ...m, [e.id]: res.saved }));
      void qc.invalidateQueries({ queryKey: ["dictionary", "saved"] });
    } finally {
      setSaving(false);
    }
  }
  async function copy(what: "word" | "sentence") {
    if (await copyText(what === "word" ? (entry ? label(entry) : pick.word) : pick.sentence)) {
      setCopied(what);
      window.setTimeout(() => setCopied(null), 1500);
    }
  }
  function open(id: string) {
    setChosen(id);
  }

  const btn = "inline-flex min-h-[44px] items-center gap-1.5 rounded-lg px-3 text-xs font-semibold ring-1 ring-surface-border transition hover:bg-surface-hover sm:min-h-9";
  return (
    <div role="dialog" aria-label={t("medien.wp.title")} data-testid="word-popup" onClick={(e) => e.stopPropagation()} onKeyDown={(e) => e.stopPropagation()}
         className="absolute inset-x-2 bottom-2 z-30 max-h-[80%] overflow-y-auto rounded-2xl bg-surface-card p-4 text-left text-text-primary shadow-2xl ring-1 ring-surface-border sm:inset-x-auto sm:bottom-20 sm:right-4 sm:w-[24rem]">
      <div className="flex items-start gap-2">
        <div className="min-w-0 flex-1">
          <h3 className="break-words text-xl font-extrabold leading-tight" data-testid="wp-word" lang="de">{entry ? label(entry) : word}</h3>
          <div className="mt-1 flex flex-wrap gap-1.5 text-[11px] font-semibold">
            {entry?.article && <span className="rounded-full bg-accent-blue/10 px-2 py-0.5 text-accent-blue" data-testid="wp-article">{entry.article}</span>}
            {entry?.word_type && <span className="rounded-full bg-surface-hover px-2 py-0.5 text-text-secondary" data-testid="wp-type">{entry.word_type}</span>}
            {entry && <span className="rounded-full bg-surface-hover px-2 py-0.5 text-text-secondary">{entry.level}</span>}
            {pick.phrase && <span className="rounded-full bg-surface-hover px-2 py-0.5 text-text-secondary">{t("medien.wp.phrase")}</span>}
          </div>
        </div>
        <button type="button" aria-label={t("medien.wp.listen")} title={t("medien.wp.listen")} onClick={() => speak(entry?.audio_text || (entry ? entry.lemma : word), "wp")} data-testid="wp-listen"
                className={cn("flex h-[44px] w-[44px] items-center justify-center rounded-lg hover:bg-surface-hover sm:h-9 sm:w-9", speakingKey === "wp" && "text-accent-blue")}><Volume2 size={18} /></button>
        <button type="button" aria-label={t("medien.wp.close")} onClick={onClose} data-testid="wp-close" className="flex h-[44px] w-[44px] items-center justify-center rounded-lg hover:bg-surface-hover sm:h-9 sm:w-9"><X size={18} /></button>
      </div>
      {speechError && <p className="mt-1 text-xs text-warning">{t(`medien.wp.speech.${speechError}`)}</p>}

      <p className="mt-2 line-clamp-3 border-l-2 border-accent-blue/40 pl-2 text-xs italic text-text-secondary" lang="de" data-testid="wp-sentence">„{pick.sentence}“</p>

      {pick.phrase && words.length > 1 && (
        <div className="mt-2 flex flex-wrap gap-1.5" data-testid="wp-words">
          {words.map((w) => <button key={w} type="button" onClick={() => { setWord(w); setChosen(null); setSubmitted(""); }} className="min-h-[40px] rounded-full bg-surface-hover px-3 py-1 text-xs font-semibold hover:bg-accent-blue/10 hover:text-accent-blue sm:min-h-0 sm:px-2.5" data-testid="wp-chip">{w}</button>)}
        </div>
      )}

      <div className="mt-3 space-y-3" aria-live="polite">
        {(lookup.isLoading || picked.isLoading) && <p className="flex items-center gap-2 text-sm text-text-secondary"><Loader2 size={15} className="animate-spin" /> {t("medien.wp.loading")}</p>}
        {lookup.isError && <p className="text-sm text-danger" role="alert" data-testid="wp-error">{t("medien.wp.error")} <button type="button" className="font-semibold underline" onClick={() => void lookup.refetch()}>{t("certificates.retry")}</button></p>}

        {lookup.data?.status === "form" && !picked.data && entry && <p className="text-xs text-text-secondary" data-testid="wp-form">{t("medien.wp.form", { lemma: label(entry) })}</p>}

        {entries.map((e, i) => (
          <div key={e.id} className={cn("space-y-1.5", i > 0 && "border-t border-surface-border pt-3")} data-testid="wp-entry">
            {i > 0 && <p className="text-sm font-bold">{label(e)} <span className="text-xs font-medium text-text-muted">{e.word_type} · {e.level}</span></p>}
            <p className="text-lg font-semibold text-accent-blue" data-testid="wp-translation">{e.translation}</p>
            {!!e.other_translations?.length && <p className="text-xs text-text-secondary">{e.other_translations.join(" · ")}</p>}
            {e.plural && <p className="text-xs text-text-secondary">{t("medien.wp.plural")}: <span lang="de">{e.plural}</span></p>}
            {e.example_de && (
              <div className="rounded-lg bg-surface-hover p-2 text-xs" data-testid="wp-example">
                <p className="font-medium" lang="de">{e.example_de}</p>
                {e.example_uz && <p className="mt-0.5 text-text-secondary">{e.example_uz}</p>}
              </div>
            )}
            {e.status === "needs_review" && <p className="text-[11px] text-text-muted">{t("medien.wp.unverified")}</p>}
            <button type="button" disabled={saving} aria-pressed={isSaved(e)} onClick={() => void toggleSave(e)} data-testid="wp-save"
                    className={cn(btn, isSaved(e) && "bg-warning/15 text-warning ring-warning/40")}>
              {saving ? <Loader2 size={14} className="animate-spin" /> : <Star size={14} className={isSaved(e) ? "fill-current" : ""} />} {t(isSaved(e) ? "medien.wp.saved" : "medien.wp.save")}
            </button>
          </div>
        ))}

        {!!suggestions.length && !picked.data && (
          <div data-testid="wp-similar">
            <p className="mb-1.5 text-xs text-text-secondary">{t("medien.wp.similar")}</p>
            <ul className="space-y-1">
              {suggestions.map((s) => (
                <li key={s.id}><button type="button" onClick={() => open(s.id)} data-testid="wp-suggestion" className="flex w-full items-center justify-between gap-2 rounded-lg px-2.5 py-1.5 text-left text-sm ring-1 ring-surface-border hover:bg-surface-hover">
                  <span className="font-semibold" lang="de">{label(s)}</span><span className="truncate text-xs text-text-secondary">{s.translation}</span></button></li>
              ))}
            </ul>
          </div>
        )}

        {(none || (!entry && !lookup.isLoading) || !!submitted) && (
          <div data-testid="wp-search-box">
            {none && <p className="mb-2 text-sm text-text-secondary" data-testid="wp-none">{t("medien.wp.none")}</p>}
            <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); setSubmitted(query.trim()); setChosen(null); }}>
              <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder={t("medien.wp.searchPlaceholder")} aria-label={t("medien.wp.searchPlaceholder")} maxLength={60} data-testid="wp-search-input"
                     className="h-9 min-w-0 flex-1 rounded-lg bg-surface-hover px-3 text-sm outline-none ring-1 ring-surface-border focus:ring-accent-blue" />
              <button type="submit" disabled={query.trim().length < 2} className={btn} data-testid="wp-search"><Search size={14} /> {t("medien.wp.search")}</button>
            </form>
            {submitted && found.isFetching && <p className="mt-2 text-xs text-text-secondary">{t("medien.wp.loading")}</p>}
            {submitted && found.data && (
              <ul className="mt-2 space-y-1" data-testid="wp-results">
                {found.data.items.map((s) => <li key={s.id}><button type="button" onClick={() => open(s.id)} data-testid="wp-result" className="flex w-full items-center justify-between gap-2 rounded-lg px-2.5 py-1.5 text-left text-sm ring-1 ring-surface-border hover:bg-surface-hover"><span className="font-semibold" lang="de">{label(s)}</span><span className="truncate text-xs text-text-secondary">{s.translation}</span></button></li>)}
                {!found.data.items.length && <li className="text-xs text-text-muted" data-testid="wp-no-results">{t("medien.wp.noResults")}</li>}
              </ul>
            )}
          </div>
        )}
      </div>

      <div className="mt-3 flex flex-wrap gap-2 border-t border-surface-border pt-3">
        <button type="button" onClick={() => void copy("word")} className={btn} data-testid="wp-copy">{copied === "word" ? <Check size={14} /> : <Copy size={14} />} {t(copied === "word" ? "medien.wp.copied" : "medien.wp.copy")}</button>
        <button type="button" onClick={() => void copy("sentence")} className={btn} data-testid="wp-copy-sentence">{copied === "sentence" ? <Check size={14} /> : <Copy size={14} />} {t(copied === "sentence" ? "medien.wp.copied" : "medien.wp.copySentence")}</button>
        <Link href="/woerterbuch" prefetch={false} className={btn} data-testid="wp-open"><BookOpen size={14} /> {t("medien.wp.open")}</Link>
      </div>
    </div>
  );
}
