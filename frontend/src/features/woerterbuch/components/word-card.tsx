"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Bookmark, BookmarkCheck, Check, Eye, Loader2, Volume2, X } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { markWord, saveWord, type ContentStatus, type WordCard as Word, type WordGrammar, type WordStatus } from "../woerterbuch-service";
import { useSpeech } from "../hooks/use-speech";

const label = "text-[11px] font-semibold uppercase tracking-wide text-text-muted";

export function ReviewBadge({ status }: { status: ContentStatus }) {
  const { t } = useTranslation();
  if (status !== "needs_review") return null;
  return (
    <span className="inline-flex items-center rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-semibold text-amber-700 ring-1 ring-amber-500/30 dark:text-amber-300"
          title={t("woerterbuch.unverifiedHint")}>
      {t("woerterbuch.unverified")}
    </span>
  );
}

function SpeakButton({ text, id, audioUrl, labelKey }: { text: string; id: string; audioUrl?: string | null; labelKey: string }) {
  const { t } = useTranslation();
  const { speak, speakingKey, error } = useSpeech();
  const active = speakingKey === id;
  return (
    <span className="inline-flex items-center gap-2">
      <button type="button" onClick={() => speak(text, id, audioUrl)} aria-label={t(labelKey)} aria-pressed={active}
              className={`inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full ring-1 transition ${
                active ? "bg-brand-800 text-white ring-brand-800" : "bg-brand-50 text-brand-800 ring-brand-200 hover:bg-brand-100 dark:bg-brand-900/40 dark:text-brand-200 dark:ring-brand-700"}`}>
        <Volume2 size={16} className={active ? "animate-pulse" : ""} />
      </button>
      {error && <span role="alert" className="text-[11px] text-danger">{t(`woerterbuch.tts_${error.replace("-", "_")}`)}</span>}
    </span>
  );
}

function Row({ k, v }: { k: string; v?: string | null }) {
  if (!v) return null;
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-surface-border/60 py-1.5 last:border-0">
      <dt className="text-xs text-text-muted">{k}</dt>
      <dd className="text-right text-sm font-medium text-text-primary">{v}</dd>
    </div>
  );
}

function Grammar({ pos, g }: { pos: string | null; g: WordGrammar }) {
  const { t } = useTranslation();
  if (pos === "Nomen") {
    return (
      <dl>
        <Row k={t("woerterbuch.article")} v={g.article} />
        <Row k={t("woerterbuch.singular")} v={g.singular ? `${g.number === "Plural" ? "" : `${g.article} `}${g.singular}`.trim() : null} />
        <Row k={t("woerterbuch.plural")} v={g.plural ?? (g.number === "Pluraletantum" ? null : g.plural_note === "kein Plural" ? t("woerterbuch.noPlural") : "—")} />
        {g.number === "Pluraletantum" && <Row k={t("woerterbuch.number")} v={t("woerterbuch.pluralOnly")} />}
        {g.plural_variants?.length ? <Row k={t("woerterbuch.pluralVariants")} v={g.plural_variants.join(", ")} /> : null}
      </dl>
    );
  }
  if (pos === "Verb") {
    return (
      <div className="space-y-3">
        <dl>
          <Row k={t("woerterbuch.infinitive")} v={g.infinitive} />
          <Row k="Präteritum" v={g.praeteritum} />
          <Row k="Partizip II" v={g.partizip_ii} />
          <Row k="Perfekt" v={g.perfekt ?? (g.auxiliary?.length === 2 && g.partizip_ii ? `hat / ist ${g.reflexive ? "sich " : ""}${g.partizip_ii}` : null)} />
          <Row k={t("woerterbuch.auxiliary")} v={g.auxiliary?.join(" / ")} />
          <Row k={t("woerterbuch.verbType")} v={[g.conjugation_type, g.separable ? t("woerterbuch.separable") : g.separable === false ? t("woerterbuch.inseparable") : null, g.reflexive ? t("woerterbuch.reflexive") : null].filter(Boolean).join(" · ")} />
        </dl>
        {g.praesens?.length ? (
          <div>
            <p className={label}>Präsens</p>
            <table className="mt-1 w-full text-sm">
              <tbody>
                {g.praesens.map((p) => (
                  <tr key={p.person} className="border-b border-surface-border/60 last:border-0">
                    <td className="w-24 py-1 text-text-muted">{p.person}</td>
                    <td className="py-1 font-medium text-text-primary">{p.form}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>
    );
  }
  if (pos === "Adjektiv") {
    return (
      <dl>
        <Row k="Positiv" v={g.positiv} />
        <Row k="Komparativ" v={g.komparativ} />
        <Row k="Superlativ" v={g.superlativ} />
        <Row k={t("woerterbuch.participleOf")} v={g.partizip_ii_von} />
        <Row k={t("woerterbuch.note")} v={g.note} />
      </dl>
    );
  }
  return (
    <dl>
      <Row k={t("woerterbuch.cases")} v={g.cases?.join(" / ")} />
      {g.wechselpraeposition && <Row k={t("woerterbuch.note")} v="Wechselpräposition" />}
      <Row k={t("woerterbuch.conjType")} v={g.conjunction?.type} />
      <Row k={t("woerterbuch.wordOrder")} v={g.conjunction?.word_order} />
    </dl>
  );
}

/** Full word card: translation, grammar by part of speech, example, audio,
 *  save / known / unknown. `concealed` (Random 5 self-test) hides everything
 *  but the German word until the student reveals it. */
export default function WordCardView({ word, concealed = false, onChange }: { word: Word; concealed?: boolean; onChange?: (w: Word) => void }) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const [revealed, setRevealed] = useState(!concealed);
  const [busy, setBusy] = useState<string | null>(null);
  const [actionError, setActionError] = useState(false);
  const g = word.grammar;

  async function act(kind: string, fn: () => Promise<Word>) {
    setBusy(kind);
    setActionError(false);
    try {
      const updated = await fn();
      onChange?.(updated);
      qc.setQueryData(["dictionary", "entry", word.id], updated);
      await qc.invalidateQueries({ queryKey: ["dictionary", "my"] });
    } catch {
      setActionError(true);
    } finally {
      setBusy(null);
    }
  }

  const toggleSave = () => act("save", () => saveWord(word.id, !word.me.saved));
  const mark = (status: WordStatus) => act(status, () => markWord(word.id, status));

  return (
    <article className="rounded-card bg-surface-card p-5 shadow-[var(--shadow-md)] ring-1 ring-surface-border" data-testid="word-card">
      <header className="flex flex-wrap items-start justify-between gap-3 border-b border-surface-border pb-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-baseline gap-2">
            {word.article && <span className="text-lg font-medium text-brand-700 dark:text-brand-300">{word.article}</span>}
            <h2 className="break-words text-2xl font-bold text-text-primary">{word.reflexive ? `sich ${word.lemma}` : word.lemma}</h2>
            <SpeakButton text={word.german} id={`${word.id}-word`} audioUrl={word.audio_url} labelKey="woerterbuch.listenWord" />
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs">
            {word.part_of_speech && <span className="rounded-full bg-brand-50 px-2.5 py-0.5 font-semibold text-brand-800 ring-1 ring-brand-200 dark:bg-brand-900/40 dark:text-brand-200 dark:ring-brand-700">{word.part_of_speech}</span>}
            <span className="rounded-full bg-brand-800 px-2.5 py-0.5 font-bold text-white">{word.cefr_level}</span>
            {word.levels.length > 1 && <span className="text-text-muted">{t("woerterbuch.alsoIn", { levels: word.levels.filter((l) => l !== word.cefr_level).join(", ") })}</span>}
            {word.ipa && <span className="font-mono text-text-muted">{word.ipa}</span>}
          </div>
        </div>
        <button type="button" onClick={toggleSave} disabled={busy !== null} aria-pressed={word.me.saved}
                className="inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm font-semibold text-brand-800 ring-1 ring-brand-200 hover:bg-brand-50 disabled:opacity-50 dark:text-brand-200 dark:ring-brand-700 dark:hover:bg-brand-900/40">
          {busy === "save" ? <Loader2 size={15} className="animate-spin" /> : word.me.saved ? <BookmarkCheck size={15} /> : <Bookmark size={15} />}
          {word.me.saved ? t("woerterbuch.saved") : t("woerterbuch.save")}
        </button>
      </header>

      {!revealed ? (
        <div className="py-8 text-center">
          <button type="button" onClick={() => setRevealed(true)}
                  className="inline-flex items-center gap-2 rounded-xl bg-brand-800 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-900">
            <Eye size={16} /> {t("woerterbuch.reveal")}
          </button>
        </div>
      ) : (
        <div className="space-y-5 pt-4">
          <section>
            <div className="flex items-center gap-2">
              <p className={label}>{t("woerterbuch.translation")}</p>
              <ReviewBadge status={word.status.translation} />
            </div>
            <p className="mt-1 text-xl font-semibold text-text-primary">{word.translation}</p>
            {word.translations_extra.length > 0 && (
              <p className="mt-1 text-sm text-text-secondary">{t("woerterbuch.otherMeanings")}: {word.translations_extra.join("; ")}</p>
            )}
          </section>

          {g && Object.keys(g).length > 0 && (
            <section>
              <div className="flex items-center gap-2">
                <p className={label}>{t("woerterbuch.grammar")}</p>
                <ReviewBadge status={word.status.grammar} />
              </div>
              <div className="mt-2 rounded-xl bg-surface-hover/60 p-3"><Grammar pos={word.part_of_speech} g={g} /></div>
            </section>
          )}

          <section>
            <div className="flex items-center gap-2">
              <p className={label}>{t("woerterbuch.example")}</p>
              <ReviewBadge status={word.status.example} />
            </div>
            {word.example_de ? (
              <div className="mt-2 flex items-start gap-3 rounded-xl border-l-4 border-brand-700 bg-brand-50/60 p-3 dark:bg-brand-900/30">
                <div className="min-w-0 flex-1">
                  <p className="italic text-text-primary">{word.example_de}</p>
                  {word.example_uz && <p className="mt-1 text-sm text-text-secondary">{word.example_uz}</p>}
                </div>
                <SpeakButton text={word.example_de} id={`${word.id}-example`} labelKey="woerterbuch.listenExample" />
              </div>
            ) : (
              <p className="mt-1 text-sm text-text-muted">{t("woerterbuch.noExample")}</p>
            )}
          </section>

          <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-surface-border pt-4">
            <div className="flex flex-wrap gap-2">
              <button type="button" onClick={() => mark("known")} disabled={busy !== null} aria-pressed={word.me.status === "known"}
                      className={`inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm font-semibold ring-1 disabled:opacity-50 ${
                        word.me.status === "known" ? "bg-success text-white ring-success" : "text-success ring-success/40 hover:bg-success/10"}`}>
                {busy === "known" ? <Loader2 size={15} className="animate-spin" /> : <Check size={15} />} {t("woerterbuch.known")}
              </button>
              <button type="button" onClick={() => mark("unknown")} disabled={busy !== null} aria-pressed={word.me.status === "unknown"}
                      className={`inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm font-semibold ring-1 disabled:opacity-50 ${
                        word.me.status === "unknown" ? "bg-danger text-white ring-danger" : "text-danger ring-danger/40 hover:bg-danger/10"}`}>
                {busy === "unknown" ? <Loader2 size={15} className="animate-spin" /> : <X size={15} />} {t("woerterbuch.unknown")}
              </button>
            </div>
            {word.attribution && (
              <a href={word.attribution.url} target="_blank" rel="noopener noreferrer" className="text-[11px] text-text-muted underline-offset-2 hover:underline">
                {t("woerterbuch.grammarSource", { name: word.attribution.name, license: word.attribution.license })}
              </a>
            )}
          </footer>
          {actionError && <p role="alert" className="text-sm text-danger">{t("woerterbuch.actionError")}</p>}
        </div>
      )}
    </article>
  );
}
