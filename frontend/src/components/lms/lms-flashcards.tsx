"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, Check, RotateCcw, Shuffle, Undo2 } from "lucide-react";

import { getLessonVocabularies, type LessonVocabularyItem } from "@/features/lessons/services/vocabulary-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

function label(w: LessonVocabularyItem): string {
  return w.article ? `${w.article} ${w.german_word}` : w.german_word;
}

function shuffled(ids: string[]): string[] {
  const out = [...ids];
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

/** Wortschatz flashcards: German on the front, the translation on the back.
 * "Weiß ich" / "Nochmal" sorts the cards; the review round repeats only the
 * cards marked "Nochmal". A study aid in the browser — the graded Wortschatz
 * result comes from the exercise sets below (server-side). Same query key as
 * VocabularySection, so the words are fetched once. */
export default function LmsFlashcards({ lessonId }: { lessonId: string }) {
  const { t } = useTranslation();
  const { data: words } = useQuery({ queryKey: ["lesson-vocabularies", lessonId], queryFn: () => getLessonVocabularies(lessonId) });
  // null = the lesson's word order; set by shuffle / the review round
  const [customOrder, setOrder] = useState<string[] | null>(null);
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [known, setKnown] = useState<Set<string>>(new Set());
  const [again, setAgain] = useState<Set<string>>(new Set());

  const byId = useMemo(() => new Map((words ?? []).map((w) => [w.id, w])), [words]);
  const order = (customOrder ?? (words ?? []).map((w) => w.id)).filter((id) => byId.has(id));

  if (!words?.length || !order.length) return null;

  const done = index >= order.length;
  const card = done ? null : byId.get(order[index]);

  function go(next: number) {
    setFlipped(false);
    setIndex(Math.max(0, Math.min(order.length, next)));
  }
  function mark(id: string, ok: boolean) {
    setKnown((s) => { const n = new Set(s); if (ok) n.add(id); else n.delete(id); return n; });
    setAgain((s) => { const n = new Set(s); if (ok) n.delete(id); else n.add(id); return n; });
    go(index + 1);
  }
  function restart(ids: string[]) {
    setOrder(ids);
    setIndex(0);
    setFlipped(false);
  }
  function shuffle() {
    restart(shuffled(order));
  }

  return (
    <section className="lms-fade-in space-y-4 rounded-card bg-surface-card p-5 ring-1 ring-surface-border sm:p-6" data-testid="lms-flashcards">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-bold text-text-primary">{t("lms.flashcardsTitle")}</h3>
          <p className="text-sm text-text-secondary">{t("lms.flashcardsHint")}</p>
        </div>
        <div className="flex items-center gap-3 text-xs font-semibold">
          <span className="text-success" data-testid="lms-flashcards-known">✓ {known.size}</span>
          <span className="text-warning" data-testid="lms-flashcards-again">↻ {again.size}</span>
          <span className="text-text-muted">{t("lms.flashcardsOf", { n: Math.min(index + 1, order.length), total: order.length })}</span>
        </div>
      </div>

      {card ? (
        <>
          <button
            type="button"
            onClick={() => setFlipped((f) => !f)}
            className="lms-flashcard group block w-full [perspective:1200px] focus-visible:outline-none"
            aria-label={t("lms.flashcardsFlip")}
            aria-pressed={flipped}
            data-testid="lms-flashcard"
            data-flipped={flipped}
          >
            <span className={cn("lms-flashcard-inner relative block h-44 w-full sm:h-48", flipped && "is-flipped")}>
              <span className="lms-flashcard-face absolute inset-0 flex flex-col items-center justify-center gap-2 rounded-2xl bg-gradient-to-br from-[#0e1834] to-accent-blue p-6 text-white shadow-[var(--shadow-md)] ring-2 ring-transparent group-focus-visible:ring-accent-blue">
                <span className="text-xs uppercase tracking-widest text-white/70">Deutsch</span>
                <span className="text-center text-2xl font-bold sm:text-3xl" data-testid="lms-flashcard-front">{label(card)}</span>
                {card.plural && <span className="text-sm text-white/70">Pl. {card.plural}</span>}
              </span>
              <span className="lms-flashcard-face lms-flashcard-back absolute inset-0 flex flex-col items-center justify-center gap-2 rounded-2xl bg-white p-6 text-text-primary shadow-[var(--shadow-md)] ring-1 ring-accent-blue/30 dark:bg-surface-card">
                <span className="text-xs uppercase tracking-widest text-accent-blue">O&apos;zbekcha</span>
                <span className="text-center text-2xl font-bold sm:text-3xl" data-testid="lms-flashcard-back">{card.translation}</span>
                {card.example_sentence && <span className="text-center text-sm text-text-secondary">{card.example_sentence}</span>}
              </span>
            </span>
          </button>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <button type="button" onClick={() => go(index - 1)} disabled={index === 0}
                    className="inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm font-semibold text-text-secondary ring-1 ring-surface-border transition hover:text-accent-blue disabled:opacity-40">
              <ArrowLeft size={15} /> {t("lms.flashcardsPrev")}
            </button>
            <div className="flex flex-wrap gap-2">
              <button type="button" onClick={() => mark(card.id, false)} data-testid="lms-flashcard-again"
                      className="inline-flex items-center gap-1.5 rounded-xl bg-warning/10 px-4 py-2 text-sm font-semibold text-warning transition hover:bg-warning/20">
                <Undo2 size={15} /> {t("lms.flashcardsAgain")}
              </button>
              <button type="button" onClick={() => mark(card.id, true)} data-testid="lms-flashcard-known"
                      className="inline-flex items-center gap-1.5 rounded-xl bg-success/10 px-4 py-2 text-sm font-semibold text-success transition hover:bg-success/20">
                <Check size={15} /> {t("lms.flashcardsKnown")}
              </button>
            </div>
            <button type="button" onClick={() => go(index + 1)}
                    className="inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm font-semibold text-text-secondary ring-1 ring-surface-border transition hover:text-accent-blue">
              {t("lms.flashcardsNext")} <ArrowRight size={15} />
            </button>
          </div>
        </>
      ) : (
        <div className="lms-pop flex flex-col items-center gap-3 rounded-2xl bg-surface-hover/60 p-6 text-center" data-testid="lms-flashcards-done">
          <p className="font-semibold text-text-primary">
            {again.size ? t("lms.flashcardsRoundDone", { known: known.size, again: again.size }) : t("lms.flashcardsAllKnown")}
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            {again.size > 0 && (
              <button type="button" onClick={() => restart(order.filter((id) => again.has(id)))} data-testid="lms-flashcards-review"
                      className="inline-flex items-center gap-1.5 rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white hover:opacity-90">
                <RotateCcw size={15} /> {t("lms.flashcardsReview")}
              </button>
            )}
            <button type="button" onClick={() => restart(words.map((w) => w.id))}
                    className="inline-flex items-center gap-1.5 rounded-xl px-4 py-2 text-sm font-semibold text-text-secondary ring-1 ring-surface-border hover:text-accent-blue">
              <RotateCcw size={15} /> {t("lms.flashcardsRestart")}
            </button>
          </div>
        </div>
      )}
      <div className="flex justify-end">
        <button type="button" onClick={shuffle} className="inline-flex items-center gap-1.5 text-xs font-semibold text-text-muted hover:text-accent-blue">
          <Shuffle size={13} /> {t("lms.flashcardsShuffle")}
        </button>
      </div>
    </section>
  );
}
