"use client";

import { useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Star, Volume2, X } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { getWord, type WordBrief, type WordCard as Word } from "../woerterbuch-service";
import { useSpeech } from "../hooks/use-speech";
import { useStar } from "../hooks/use-star";

const label = "text-[11px] font-semibold uppercase tracking-wide text-text-muted";

export function ReviewBadge({ status }: { status: Word["status"] }) {
  const { t } = useTranslation();
  if (status === "verified") return null;
  return (
    <span className="inline-flex items-center rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-semibold text-amber-700 ring-1 ring-amber-500/30 dark:text-amber-300"
          title={t("woerterbuch.unverifiedHint")}>
      {t("woerterbuch.unverified")}
    </span>
  );
}

export function LevelBadge({ level }: { level: string }) {
  return <span className="shrink-0 rounded-full bg-brand-800 px-2 py-0.5 text-[10px] font-bold text-white">{level}</span>;
}

/** Filled star = saved, outline = not saved; the same state everywhere (useStar). */
export function StarButton({ word }: { word: Pick<WordBrief, "id" | "saved"> }) {
  const { t } = useTranslation();
  const { toggle, pending } = useStar();
  const busy = pending === word.id;
  return (
    <button type="button" onClick={(e) => { e.stopPropagation(); toggle(word.id, word.saved); }} disabled={busy}
            aria-pressed={word.saved} aria-label={t(word.saved ? "woerterbuch.unstar" : "woerterbuch.star")}
            title={t(word.saved ? "woerterbuch.unstar" : "woerterbuch.star")} data-testid="wb-star"
            className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-amber-500 ring-1 ring-surface-border transition hover:bg-amber-500/10 disabled:opacity-60">
      {busy ? <Loader2 size={18} className="animate-spin" /> : <Star size={20} fill={word.saved ? "currentColor" : "none"} />}
    </button>
  );
}

function SpeakButton({ text, id, labelKey }: { text: string; id: string; labelKey: string }) {
  const { t } = useTranslation();
  const { speak, speakingKey, error } = useSpeech();
  const active = speakingKey === id;
  return (
    <span className="inline-flex items-center gap-2">
      <button type="button" onClick={(e) => { e.stopPropagation(); speak(text, id); }} aria-label={t(labelKey)} title={t(labelKey)} aria-pressed={active}
              className={`inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full ring-1 transition ${
                active ? "bg-brand-800 text-white ring-brand-800" : "bg-brand-50 text-brand-800 ring-brand-200 hover:bg-brand-100 dark:bg-brand-900/40 dark:text-brand-200 dark:ring-brand-700"}`}>
        <Volume2 size={16} className={active ? "animate-pulse" : ""} />
      </button>
      {error && <span role="alert" className="text-[11px] text-danger">{t(`woerterbuch.tts_${error.replace("-", "_")}`)}</span>}
    </span>
  );
}

function Row({ k, v }: { k: string; v?: string | null }) {
  const { t } = useTranslation();
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-surface-border/60 py-1.5 last:border-0">
      <dt className="text-xs text-text-muted">{k}</dt>
      <dd className={`text-right text-sm ${v ? "font-medium text-text-primary" : "italic text-text-muted"}`}>{v || t("woerterbuch.notEntered")}</dd>
    </div>
  );
}

const detail = (w: Word, key: string) => {
  const v = w.details[key];
  return typeof v === "string" ? v : null;
};

function Grammar({ w }: { w: Word }) {
  const { t } = useTranslation();
  if (w.word_type === "Nomen") {
    return (
      <dl>
        <Row k={t("woerterbuch.article")} v={w.article} />
        <Row k="Plural" v={w.plural ? `die ${w.plural}` : null} />
        {detail(w, "noun_genitive") && <Row k="Genitiv" v={detail(w, "noun_genitive")} />}
      </dl>
    );
  }
  if (w.word_type === "Verb" && w.verb) {
    const v = w.verb;
    return (
      <div className="space-y-3">
        <dl>
          <Row k="Infinitiv" v={v.infinitive} />
          <Row k="Präteritum" v={v.praeteritum} />
          <Row k="Partizip II" v={v.partizip_ii} />
          <Row k={t("woerterbuch.auxiliary")} v={v.auxiliary?.replace("/", " / ")} />
          {detail(w, "verb_perfekt") && <Row k="Perfekt" v={detail(w, "verb_perfekt")} />}
        </dl>
        <div>
          <p className={label}>Präsens</p>
          <table className="mt-1 w-full text-sm">
            <tbody>
              {["ich", "du", "er/sie/es", "wir", "ihr", "sie/Sie"].map((person) => {
                const form = v.praesens?.find((p) => p.person === person)?.form;
                return (
                  <tr key={person} className="border-b border-surface-border/60 last:border-0">
                    <td className="w-24 py-1 text-text-muted">{person}</td>
                    <td className={`py-1 ${form ? "font-medium text-text-primary" : "italic text-text-muted"}`}>{form ?? t("woerterbuch.notEntered")}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    );
  }
  if (w.word_type === "Adjektiv" && w.adjective) {
    const note = detail(w, "grammar_note");
    return (
      <dl>
        <Row k="Positiv" v={w.adjective.positiv} />
        <Row k="Komparativ" v={w.adjective.komparativ ?? (note === "nicht steigerbar" ? t("woerterbuch.notComparable") : null)} />
        <Row k="Superlativ" v={w.adjective.superlativ ?? (note === "nicht steigerbar" ? t("woerterbuch.notComparable") : null)} />
      </dl>
    );
  }
  const order = w.details.conjunction_word_order as { type?: string; word_order?: string } | undefined;
  const cases = w.details.preposition_cases as string[] | undefined;
  if (!order && !cases) return null;
  return (
    <dl>
      {cases && <Row k={t("woerterbuch.cases")} v={cases.join(" / ")} />}
      {order?.type && <Row k={t("woerterbuch.conjType")} v={order.type} />}
      {order?.word_order && <Row k={t("woerterbuch.wordOrder")} v={order.word_order} />}
    </dl>
  );
}

/** One-line grammar for compact cards: "der Apfel, die Äpfel", "lief – hat gelaufen" … */
function grammarLine(w: Word): string | null {
  if (w.word_type === "Nomen") return [w.article && `${w.article} ${w.lemma}`, w.plural && `die ${w.plural}`].filter(Boolean).join(", ") || null;
  if (w.word_type === "Verb" && w.verb) return [w.verb.praeteritum, w.verb.partizip_ii && `${w.verb.auxiliary === "sein" ? "ist" : "hat"} ${w.verb.partizip_ii}`].filter(Boolean).join(" – ") || null;
  if (w.word_type === "Adjektiv" && w.adjective) return [w.adjective.komparativ, w.adjective.superlativ].filter(Boolean).join(" – ") || null;
  return null;
}

function Example({ w }: { w: Word }) {
  const { t } = useTranslation();
  if (!w.example_de) return <p className="mt-1 text-sm text-text-muted">{t("woerterbuch.noExample")}</p>;
  return (
    <div className="mt-2 flex items-start gap-3 rounded-xl border-l-4 border-brand-700 bg-brand-50/60 p-3 dark:bg-brand-900/30">
      <div className="min-w-0 flex-1">
        <p className="italic text-text-primary">{w.example_de}</p>
        {w.example_uz && <p className="mt-1 text-sm text-text-secondary">{w.example_uz}</p>}
      </div>
      <SpeakButton text={w.example_de} id={`${w.id}-example`} labelKey="woerterbuch.listenExample" />
    </div>
  );
}

function Header({ w }: { w: Word }) {
  const { t } = useTranslation();
  return (
    <header className="flex items-start justify-between gap-3">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          {w.article && <span className="text-lg font-medium text-brand-700 dark:text-brand-300">{w.article}</span>}
          <h2 className="break-words text-2xl font-bold text-text-primary">{w.lemma}</h2>
          {w.audio_text && <SpeakButton text={w.audio_text} id={`${w.id}-word`} labelKey="woerterbuch.listenWord" />}
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs">
          <LevelBadge level={w.level} />
          {w.word_type && <span className="rounded-full bg-brand-50 px-2.5 py-0.5 font-semibold text-brand-800 ring-1 ring-brand-200 dark:bg-brand-900/40 dark:text-brand-200 dark:ring-brand-700">{w.word_type}</span>}
          <ReviewBadge status={w.status} />
          {w.also_in.length > 0 && <span className="text-text-muted">{t("woerterbuch.alsoIn", { levels: w.also_in.join(", ") })}</span>}
          {detail(w, "ipa") && <span className="font-mono text-text-muted">{detail(w, "ipa")}</span>}
        </div>
      </div>
      <StarButton word={w} />
    </header>
  );
}

/** Full word card: translation, grammar by word type, example, pronunciation, star. */
export default function WordCardView({ word: w }: { word: Word }) {
  const { t } = useTranslation();
  const hasGrammar = ["Nomen", "Verb", "Adjektiv"].includes(w.word_type ?? "") || !!w.details.conjunction_word_order || !!w.details.preposition_cases;
  return (
    <article className="rounded-card bg-surface-card p-5 shadow-[var(--shadow-md)] ring-1 ring-surface-border" data-testid="word-card">
      <div className="border-b border-surface-border pb-4"><Header w={w} /></div>
      <div className="space-y-5 pt-4">
        <section>
          <p className={label}>{t("woerterbuch.translation")}</p>
          <p className="mt-1 text-xl font-semibold text-text-primary">{w.translation}</p>
          {w.other_translations.length > 0 && (
            <p className="mt-1 text-sm text-text-secondary">{t("woerterbuch.otherMeanings")}: {w.other_translations.join("; ")}</p>
          )}
        </section>
        {hasGrammar && (
          <section>
            <p className={label}>{t("woerterbuch.grammar")}</p>
            <div className="mt-2 rounded-xl bg-surface-hover/60 p-3"><Grammar w={w} /></div>
          </section>
        )}
        <section>
          <p className={label}>{t("woerterbuch.example")}</p>
          <Example w={w} />
        </section>
        {w.review_note && (
          <p className="rounded-xl bg-amber-500/10 p-3 text-xs text-amber-800 ring-1 ring-amber-500/30 dark:text-amber-200">
            {t("woerterbuch.reviewNote")}: {w.review_note}
          </p>
        )}
        {w.attribution && (
          <a href={w.attribution.url} target="_blank" rel="noopener noreferrer" className="block text-[11px] text-text-muted underline-offset-2 hover:underline">
            {t("woerterbuch.grammarSource", { name: w.attribution.name, license: w.attribution.license })}
          </a>
        )}
      </div>
    </article>
  );
}

/** Random 5 card: the essentials; "Details" opens the full card. */
export function CompactWordCard({ word: w, onOpen }: { word: Word; onOpen: () => void }) {
  const { t } = useTranslation();
  const line = grammarLine(w);
  return (
    <article className="flex flex-col rounded-card bg-surface-card p-4 shadow-[var(--shadow-md)] ring-1 ring-surface-border" data-testid="wb-random-card">
      <Header w={w} />
      <p className="mt-3 text-lg font-semibold text-text-primary">{w.translation}</p>
      {line && <p className="mt-1 text-sm text-text-secondary">{line}</p>}
      <div className="flex-1"><Example w={w} /></div>
      <button type="button" onClick={onOpen}
              className="mt-3 self-start rounded-xl px-3 py-2 text-sm font-semibold text-brand-800 ring-1 ring-brand-200 hover:bg-brand-50 dark:text-brand-200 dark:ring-brand-700 dark:hover:bg-brand-900/40">
        {t("woerterbuch.details")}
      </button>
    </article>
  );
}

/** The full card in a dialog (Random 5 → Details). */
export function WordModal({ id, onClose }: { id: string; onClose: () => void }) {
  const { t } = useTranslation();
  const card = useQuery({ queryKey: ["dictionary", "entry", id], queryFn: () => getWord(id) });
  const closeRef = useRef<HTMLButtonElement>(null);
  const onCloseRef = useRef(onClose);

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onCloseRef.current();
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
      previous?.focus();
    };
  }, []);

  return (
    <div className="fixed inset-0 z-40 flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-4" onClick={onClose}>
      <div role="dialog" aria-modal="true" aria-label={card.data?.lemma ?? t("woerterbuch.details")}
           className="max-h-[92vh] w-full max-w-xl overflow-y-auto rounded-t-card bg-surface-card sm:rounded-card" onClick={(e) => e.stopPropagation()}>
        <div className="sticky top-0 z-10 flex justify-end bg-surface-card/95 p-2">
          <button ref={closeRef} type="button" onClick={onClose} aria-label={t("woerterbuch.close")}
                  className="inline-flex h-9 w-9 items-center justify-center rounded-full text-text-secondary hover:bg-surface-hover">
            <X size={18} />
          </button>
        </div>
        <div className="px-2 pb-2">
          {card.isLoading ? (
            <div className="flex h-40 items-center justify-center"><Loader2 className="animate-spin text-text-muted" /></div>
          ) : card.isError ? (
            <p role="alert" className="m-3 rounded-card bg-danger/10 p-4 text-sm text-danger">{t("woerterbuch.loadError")}</p>
          ) : card.data ? (
            <WordCardView word={card.data} />
          ) : null}
        </div>
      </div>
    </div>
  );
}
