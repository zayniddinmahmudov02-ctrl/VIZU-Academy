"use client";

import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Captions, Clock, Lock } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

import { sortByLanguage } from "../lib/subtitles";
import { errorCode, getFilm } from "../services/medien-service";
import FilmPlayer from "./film-player";
import { Cover, EmptyState, PriceTag, PurchaseButton, StatusBadge } from "./media-ui";

/** Film page: the player (when the film is free or owned and has a video) or poster + text + price + buy button. The
 * video URL is only requested by the player after the server checked the access. */
export default function FilmWatchClient({ filmId }: { filmId: string }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { data: film, isLoading, error } = useQuery({ queryKey: ["medien-film", filmId], queryFn: () => getFilm(filmId), retry: false });

  if (isLoading) return <p className="py-16 text-center text-sm text-text-secondary">{t("medien.loading")}</p>;
  if (error || !film) return <EmptyState text={errorCode(error) === "NOT_FOUND" ? t("medien.err.NOT_FOUND") : t("medien.err.GENERIC")} />;

  const meta = [film.level, film.category?.name, film.genre, film.year, film.language?.toUpperCase()].filter(Boolean);
  return (
    <div className="space-y-6" data-testid="film-detail">
      <Link href="/medien/filme" className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary hover:text-accent-blue"><ArrowLeft size={16} /> {t("medien.films")}</Link>

      {!film.locked && film.playable ? (
        <FilmPlayer filmId={film.id} title={film.title} onProgress={() => { void queryClient.invalidateQueries({ queryKey: ["medien-continue"] }); void queryClient.invalidateQueries({ queryKey: ["medien-overview"] }); }} />
      ) : (
        <div className="relative isolate overflow-hidden rounded-2xl bg-black" data-testid="film-poster">
          <Cover src={film.cover_url} kind="FILM" eager className="aspect-video w-full opacity-60" />
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-black/50 p-4 text-center text-white">
            {film.locked ? <><Lock size={28} /><p className="text-lg font-semibold">{t("medien.lockedNote")}</p><PurchaseButton item={film} /></> : <p className="text-lg font-semibold">{t("medien.err.FILE_MISSING")}</p>}
          </div>
        </div>
      )}

      <article className="space-y-3 rounded-3xl bg-surface-card p-5 shadow-[var(--shadow-sm)] ring-1 ring-surface-border sm:p-7">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <h1 className="text-2xl font-extrabold text-text-primary sm:text-3xl" data-testid="film-title">{film.title}</h1>
          <div className="flex items-center gap-3"><StatusBadge item={film} /><PriceTag item={film} /></div>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-text-secondary">
          {meta.map((m) => <span key={String(m)} className="rounded-full bg-surface-hover px-3 py-1">{m}</span>)}
          {film.duration_minutes && <span className="inline-flex items-center gap-1 rounded-full bg-surface-hover px-3 py-1"><Clock size={12} /> {t("medien.minutes", { n: film.duration_minutes })}</span>}
          {!!film.subtitles?.length && <span className="inline-flex items-center gap-1 rounded-full bg-surface-hover px-3 py-1" data-testid="film-subtitle-langs"><Captions size={12} /> {sortByLanguage(film.subtitles).map((s) => s.label).join(" · ")}</span>}
        </div>
        {film.description && <p className="whitespace-pre-line text-sm leading-relaxed text-text-secondary">{film.description}</p>}
      </article>
    </div>
  );
}
