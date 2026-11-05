"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Clock3, Mic, PenLine } from "lucide-react";

import { getPublicKompetenz } from "@/features/vorbereitung/services/vorbereitung-service";
import type { PublicTeilContent } from "@/features/vorbereitung/types/vorbereitung.types";

const KOMPETENZ_LABEL: Record<string, string> = {
  LESEN: "Lesen",
  HOEREN: "Hören",
  SCHREIBEN: "Schreiben",
  SPRECHEN: "Sprechen",
};

export default function PublicKompetenzPage() {
  const { modelTestId, kompetenzId } = useParams<{ modelTestId: string; kompetenzId: string }>();

  const { data: kompetenz, isLoading, isError } = useQuery({
    queryKey: ["public-kompetenz", kompetenzId],
    queryFn: () => getPublicKompetenz(kompetenzId),
  });

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <Link
        href={`/vorbereitung/modelltest/${modelTestId}`}
        className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary transition-colors hover:text-accent-blue"
      >
        <ArrowLeft size={16} />
        Zurück zum Modelltest
      </Link>

      {isLoading && <p className="text-sm text-text-secondary">Wird geladen…</p>}

      {isError && (
        <p className="rounded-2xl bg-surface-card p-6 text-center text-sm text-text-secondary shadow-[var(--shadow-sm)] ring-1 ring-surface-border">
          Dieser Bereich ist nicht verfügbar.
        </p>
      )}

      {kompetenz && (
        <>
          <header>
            <h1 className="text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
              {KOMPETENZ_LABEL[kompetenz.type] ?? kompetenz.type}
            </h1>
            {kompetenz.description && <p className="mt-2 text-text-secondary">{kompetenz.description}</p>}
          </header>

          {kompetenz.teile.length === 0 && (
            <p className="rounded-2xl bg-surface-card p-6 text-center text-sm text-text-secondary shadow-[var(--shadow-sm)] ring-1 ring-surface-border">
              Für diesen Bereich sind noch keine Aufgaben verfügbar.
            </p>
          )}

          <div className="space-y-6">
            {kompetenz.teile.map((teil) => (
              <TeilContent key={teil.id} teil={teil} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// Imported Modelltests store plain text (line breaks matter); editor content is HTML.
function isHtml(value: string): boolean {
  return /<\/?[a-z][^>]*>/i.test(value);
}

function TaskText({ value, className = "" }: { value: string; className?: string }) {
  if (isHtml(value)) {
    return <div className={`prose-editor text-text-secondary ${className}`} dangerouslySetInnerHTML={{ __html: value }} />;
  }
  return <div className={`whitespace-pre-line break-words text-text-secondary ${className}`}>{value}</div>;
}

const OPTION_LETTERS = "ABCDEFGHIJ";

function TeilQuestions({ teil }: { teil: PublicTeilContent }) {
  // ORDERING items are bare slots ("A1"…"A5") for the parts already in the text — nothing to show
  const questions = (teil.questions ?? []).filter((q) => q.question_type !== "ORDERING");
  if (questions.length === 0) return null;
  // MATCHING shares one letter list (headings A–J in the text): show it once, not per item
  const shared = questions.every((q) => q.question_type === "MATCHING");
  return (
    <ol className="mt-5 space-y-4" data-testid="teil-questions">
      {questions.map((q) => (
        <li key={q.id} className="rounded-xl bg-surface-hover/60 p-4 ring-1 ring-surface-border">
          <p className="whitespace-pre-line break-words text-sm font-medium text-text-primary">{q.question_text}</p>
          {!shared && q.options.length > 0 && (
            <ul className="mt-2 space-y-1">
              {q.options.map((o, i) => (
                <li key={o.id} className="flex gap-2 text-sm text-text-secondary">
                  <span className="font-semibold text-text-muted">{OPTION_LETTERS[i] ?? i + 1})</span>
                  <span className="break-words">{o.option_text}</span>
                </li>
              ))}
            </ul>
          )}
        </li>
      ))}
    </ol>
  );
}

function TeilContent({ teil }: { teil: PublicTeilContent }) {
  return (
    <div className="rounded-2xl bg-surface-card p-4 shadow-[var(--shadow-sm)] ring-1 ring-surface-border sm:p-6">
      <h2 className="text-lg font-bold text-text-primary">{teil.title}</h2>
      {teil.instructions && <p className="mt-1 whitespace-pre-line text-sm text-text-secondary">{teil.instructions}</p>}
      {teil.description && <TaskText value={teil.description} className="mt-3 text-sm" />}

      {teil.reading_content && (
        <div className="mt-4">
          {teil.reading_content.image_url && teil.reading_content.content_type !== "TEXT" && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={teil.reading_content.image_url}
              alt=""
              className="mb-4 max-h-[420px] w-full rounded-xl object-cover"
            />
          )}
          {teil.reading_content.text && teil.reading_content.content_type !== "IMAGE" && (
            <TaskText value={teil.reading_content.text} />
          )}
        </div>
      )}

      {teil.listening_content && (
        <div className="mt-4 space-y-3">
          {teil.listening_content.audio_url ? (
            <audio controls src={teil.listening_content.audio_url} className="w-full">
              <track kind="captions" />
            </audio>
          ) : (
            <p className="rounded-xl bg-surface-hover px-4 py-3 text-sm text-text-muted">Audio noch nicht verfügbar.</p>
          )}
          {teil.listening_content.image_url && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={teil.listening_content.image_url}
              alt=""
              className="max-h-[420px] w-full rounded-xl object-cover"
            />
          )}
        </div>
      )}

      {teil.writing_task && (
        <div className="mt-4 space-y-3">
          <TaskText value={teil.writing_task.task_text} />
          {teil.writing_task.image_url && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={teil.writing_task.image_url}
              alt=""
              className="max-h-[420px] w-full rounded-xl object-cover"
            />
          )}
          <div className="flex flex-wrap items-center gap-3 text-xs font-medium text-text-muted">
            {teil.writing_task.word_limit && (
              <span className="flex items-center gap-1 rounded-lg bg-surface-hover px-2.5 py-1">
                <PenLine size={13} /> {teil.writing_task.word_limit} Wörter
              </span>
            )}
            {teil.writing_task.time_limit_minutes && (
              <span className="flex items-center gap-1 rounded-lg bg-surface-hover px-2.5 py-1">
                <Clock3 size={13} /> {teil.writing_task.time_limit_minutes} Min.
              </span>
            )}
          </div>
        </div>
      )}

      {teil.speaking_task && (
        <div className="mt-4 space-y-3">
          <TaskText value={teil.speaking_task.task_text} />
          {teil.speaking_task.image_url && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={teil.speaking_task.image_url}
              alt=""
              className="max-h-[420px] w-full rounded-xl object-cover"
            />
          )}
          <div className="flex flex-wrap items-center gap-3 text-xs font-medium text-text-muted">
            <span className="flex items-center gap-1 rounded-lg bg-surface-hover px-2.5 py-1">
              <Clock3 size={13} /> {teil.speaking_task.preparation_time_seconds}s Vorbereitung
            </span>
            <span className="flex items-center gap-1 rounded-lg bg-surface-hover px-2.5 py-1">
              <Mic size={13} /> {teil.speaking_task.speaking_time_seconds}s Sprechzeit
            </span>
          </div>
        </div>
      )}

      <TeilQuestions teil={teil} />
    </div>
  );
}
