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

function TeilContent({ teil }: { teil: PublicTeilContent }) {
  return (
    <div className="rounded-2xl bg-surface-card p-6 shadow-[var(--shadow-sm)] ring-1 ring-surface-border">
      <h2 className="text-lg font-bold text-text-primary">{teil.title}</h2>
      {teil.instructions && <p className="mt-1 text-sm text-text-secondary">{teil.instructions}</p>}

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
            <div className="prose-editor text-text-secondary" dangerouslySetInnerHTML={{ __html: teil.reading_content.text }} />
          )}
        </div>
      )}

      {teil.listening_content && (
        <div className="mt-4 space-y-3">
          <audio controls src={teil.listening_content.audio_url} className="w-full">
            <track kind="captions" />
          </audio>
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
          <div
            className="prose-editor text-text-secondary"
            dangerouslySetInnerHTML={{ __html: teil.writing_task.task_text }}
          />
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
          <div
            className="prose-editor text-text-secondary"
            dangerouslySetInnerHTML={{ __html: teil.speaking_task.task_text }}
          />
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
    </div>
  );
}
