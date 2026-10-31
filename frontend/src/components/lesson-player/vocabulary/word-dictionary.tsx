"use client";

import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Bookmark, BookmarkCheck, CheckCircle2, Circle, Search, Volume2 } from "lucide-react";

import { getWortschatzWords, setWortschatzWordState, type WortschatzWord, type WortschatzWords } from "@/features/lessons/services/wortschatz-service";
import { filterWords, wordTypes } from "@/features/lessons/utils/wortschatz-filter";
import { useSpeech } from "@/features/woerterbuch/hooks/use-speech";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

const chip = "inline-flex min-h-9 items-center gap-1.5 rounded-full px-3 text-xs font-semibold ring-1 transition";
const chipOn = "bg-accent-blue text-white ring-accent-blue";
const chipOff = "bg-surface-card text-text-secondary ring-surface-border hover:text-accent-blue";

/** Wortschatz → Wörterbuch: the lesson's words (or every open topic of the
 * level) with search (German + Uzbek), topic and word-type filters, grammar
 * forms, examples, pronunciation and the student's own saved / learned
 * state (stored on the server per student). Missing data is shown as missing. */
export default function WordDictionary({ lessonId }: { lessonId: string }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { speak, speakingKey, error: speechError } = useSpeech();
  const [scope, setScope] = useState<"lesson" | "level">("lesson");
  const [query, setQuery] = useState("");
  const [topic, setTopic] = useState<number | null>(null);
  const [wordType, setWordType] = useState<string | null>(null);
  const [onlySaved, setOnlySaved] = useState(false);
  const [hideLearned, setHideLearned] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);

  const key = ["wortschatz-words", lessonId, scope];
  const { data, isLoading } = useQuery({ queryKey: key, queryFn: () => getWortschatzWords(lessonId, scope) });
  const words = useMemo(() => data?.words ?? [], [data]);
  const shown = useMemo(() => filterWords(words, { query, topic, wordType, onlySaved, hideLearned }), [words, query, topic, wordType, onlySaved, hideLearned]);
  const types = useMemo(() => wordTypes(words), [words]);

  async function toggle(word: WortschatzWord, change: { saved?: boolean; learned?: boolean }) {
    setBusy(word.id);
    try {
      const updated = await setWortschatzWordState(lessonId, word.id, change);
      for (const s of ["lesson", "level"] as const) {
        queryClient.setQueryData<WortschatzWords>(["wortschatz-words", lessonId, s], (old) =>
          old ? { ...old, words: old.words.map((w) => (w.id === updated.id ? { ...w, saved: updated.saved, learned: updated.learned } : w)) } : old,
        );
      }
    } finally {
      setBusy(null);
    }
  }

  if (isLoading) return <p className="text-sm text-text-muted">{t("common.loading")}</p>;
  if (!words.length && scope === "lesson") {
    return (
      <div className="space-y-3 rounded-2xl bg-surface-hover/60 p-6 text-center ring-1 ring-surface-border" data-testid="ws-dictionary-empty">
        <p className="text-text-secondary">{t("lessons.vocabularyEmpty")}</p>
        <button type="button" onClick={() => setScope("level")} className={cn(chip, chipOff)} data-testid="ws-scope-level">
          {t("lessons.wsScopeLevel")}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="ws-dictionary">
      <div className="space-y-3">
        <div className="relative">
          <Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t("lessons.vocabularySearch")}
            aria-label={t("lessons.vocabularySearch")}
            className="min-h-11 w-full rounded-xl bg-surface-hover/50 pl-9 pr-3 text-base text-text-primary outline-none ring-1 ring-surface-border focus:ring-2 focus:ring-accent-blue sm:text-sm"
            data-testid="ws-search"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {(["lesson", "level"] as const).map((s) => (
            <button key={s} type="button" onClick={() => { setScope(s); setTopic(null); }} className={cn(chip, scope === s ? chipOn : chipOff)}
                    aria-pressed={scope === s} data-testid={`ws-scope-${s}`}>
              {s === "lesson" ? t("lessons.wsScopeLesson") : t("lessons.wsScopeLevel")}
            </button>
          ))}
          <button type="button" onClick={() => setOnlySaved((v) => !v)} className={cn(chip, onlySaved ? chipOn : chipOff)} aria-pressed={onlySaved}
                  data-testid="ws-only-saved">
            <Bookmark size={13} /> {t("lessons.wsOnlySaved")}
          </button>
          <button type="button" onClick={() => setHideLearned((v) => !v)} className={cn(chip, hideLearned ? chipOn : chipOff)} aria-pressed={hideLearned}>
            <CheckCircle2 size={13} /> {t("lessons.wsHideLearned")}
          </button>
        </div>
        <div className="grid gap-2 sm:grid-cols-2">
          {scope === "level" && (data?.topics.length ?? 0) > 1 && (
            <select value={topic ?? ""} onChange={(e) => setTopic(e.target.value ? Number(e.target.value) : null)}
                    className="min-h-11 w-full rounded-xl bg-surface-card px-3 text-sm text-text-primary ring-1 ring-surface-border" aria-label={t("lessons.wsAllTopics")}
                    data-testid="ws-topic">
              <option value="">{t("lessons.wsAllTopics")}</option>
              {data?.topics.map((tp) => (
                <option key={tp.lesson_id} value={tp.number}>{tp.number}. {tp.title}</option>
              ))}
            </select>
          )}
          {types.length > 1 && (
            <select value={wordType ?? ""} onChange={(e) => setWordType(e.target.value || null)}
                    className="min-h-11 w-full rounded-xl bg-surface-card px-3 text-sm text-text-primary ring-1 ring-surface-border" aria-label={t("lessons.wsAllTypes")}
                    data-testid="ws-type">
              <option value="">{t("lessons.wsAllTypes")}</option>
              {types.map((ty) => <option key={ty} value={ty}>{ty}</option>)}
            </select>
          )}
        </div>
        <p className="text-xs text-text-muted" data-testid="ws-count">
          {t("lessons.wsCount", { n: shown.length, total: words.length, learned: words.filter((w) => w.learned).length })}
        </p>
        {speechError === "no-voice" && <p className="text-xs text-warning">{t("lessons.wsNoVoice")}</p>}
      </div>

      {shown.length === 0 ? (
        <p className="rounded-xl bg-surface-hover/60 p-4 text-center text-sm text-text-secondary">{t("lessons.wsNoResults")}</p>
      ) : (
        <ul className="grid gap-2.5 md:grid-cols-2">
          {shown.map((w) => (
            <li key={w.id} className={cn("rounded-xl bg-surface-card p-3.5 ring-1 ring-surface-border", w.learned && "ring-success/40")} data-testid="ws-word"
                data-word={w.german_word}>
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="break-words text-[15px] text-text-primary">
                    {w.article && <span className="mr-1 text-text-muted">{w.article}</span>}
                    <span className="font-bold">{w.german_word}</span>
                    {w.plural && <span className="ml-1 text-xs text-text-muted">(Pl. {w.plural})</span>}
                  </p>
                  <p className="break-words text-sm text-text-secondary">{w.translation}</p>
                </div>
                <button type="button" onClick={() => speak(w.audio_text, w.id, w.audio_url)} aria-label={`${t("lessons.wsListen")}: ${w.audio_text}`}
                        className={cn("flex h-10 w-10 shrink-0 items-center justify-center rounded-full ring-1 ring-surface-border", speakingKey === w.id ? "bg-accent-blue text-white" : "text-accent-blue")}>
                  <Volume2 size={16} />
                </button>
              </div>
              <div className="mt-2 flex flex-wrap gap-1.5 text-[11px]">
                {w.word_type && <span className="rounded-full bg-surface-hover px-2 py-0.5 font-semibold text-text-secondary">{w.word_type}</span>}
                {scope === "level" && <span className="rounded-full bg-surface-hover px-2 py-0.5 text-text-muted">{w.lesson_number}. {w.lesson_title}</span>}
              </div>
              {w.word_type === "Verb" && (w.verb_praeteritum || w.verb_partizip_ii) && (
                <p className="mt-1.5 text-xs text-text-secondary" data-testid="ws-verb-forms">
                  {w.verb_praeteritum && <>Präteritum: <strong>{w.verb_praeteritum}</strong></>}
                  {w.verb_partizip_ii && <> · Perfekt: <strong>{w.verb_auxiliary === "sein" ? "ist" : w.verb_auxiliary === "haben" ? "hat" : "…"} {w.verb_partizip_ii}</strong></>}
                </p>
              )}
              {w.example_sentence && (
                <p className="mt-1.5 text-xs italic text-text-primary">
                  {w.example_sentence}
                  {w.example_translation && <span className="block not-italic text-text-muted">{w.example_translation}</span>}
                </p>
              )}
              {w.missing.length > 0 && (
                <p className="mt-1.5 text-[11px] text-text-muted" data-testid="ws-missing">
                  {t("lessons.wsMissing", { fields: w.missing.map((m) => t(`lessons.wsField_${m}`)).join(", ") })}
                </p>
              )}
              <div className="mt-2.5 flex flex-wrap gap-2">
                <button type="button" disabled={busy === w.id} onClick={() => toggle(w, { saved: !w.saved })} aria-pressed={w.saved}
                        className={cn(chip, w.saved ? "bg-amber-100 text-amber-800 ring-amber-200" : chipOff)} data-testid="ws-save">
                  {w.saved ? <BookmarkCheck size={13} /> : <Bookmark size={13} />} {w.saved ? t("lessons.wsSaved") : t("lessons.wsSave")}
                </button>
                <button type="button" disabled={busy === w.id} onClick={() => toggle(w, { learned: !w.learned })} aria-pressed={w.learned}
                        className={cn(chip, w.learned ? "bg-success/10 text-success ring-success/30" : chipOff)} data-testid="ws-learned">
                  {w.learned ? <CheckCircle2 size={13} /> : <Circle size={13} />} {w.learned ? t("lessons.wsLearned") : t("lessons.wsMarkLearned")}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
