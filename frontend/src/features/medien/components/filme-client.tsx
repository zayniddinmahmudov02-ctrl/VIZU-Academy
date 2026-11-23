"use client";

import { useState } from "react";
import Link from "next/link";
import { useQueries, useQuery } from "@tanstack/react-query";
import { ArrowLeft, Clock, Play, Search } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import { getCategories, getContinue, getFilms, getOverview } from "../services/medien-service";
import { LEVELS, type FilmCard } from "../types";
import { Cover, EmptyState, Pager, PriceTag, SectionTitle, StatusBadge, useDebounced } from "./media-ui";
import { MedienStatsSection } from "./medien-stats";

const PAGE_SIZE = 24;
const DURATIONS: Record<string, { min_minutes?: number; max_minutes?: number }> = { short: { max_minutes: 30 }, medium: { min_minutes: 30, max_minutes: 90 }, long: { min_minutes: 90 } };

export function FilmTile({ film, wide = false }: { film: FilmCard; wide?: boolean }) {
  const { t } = useTranslation();
  return (
    <Link href={`/medien/filme/${film.id}`} data-testid="film-card" data-free={film.access_type === "FREE" ? "1" : "0"} className={cn("group shrink-0 snap-start", wide ? "w-full" : "w-40 sm:w-44")}>
      <div className="relative overflow-hidden rounded-xl shadow-md transition duration-300 group-hover:-translate-y-1 group-hover:shadow-xl">
        <Cover src={film.cover_url} kind="FILM" alt={film.title} className="aspect-[2/3] w-full" />
        <span className="absolute left-2 top-2"><StatusBadge item={film} /></span>
        {film.level && <span className="absolute right-2 top-2 rounded bg-black/70 px-1.5 py-0.5 text-[10px] font-bold text-white">{film.level}</span>}
        <span className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 transition group-hover:opacity-100"><Play className="text-white" size={34} /></span>
      </div>
      <p className="mt-2 truncate text-sm font-semibold text-text-primary">{film.title}</p>
      <p className="flex items-center gap-1.5 text-xs text-text-muted">
        {film.duration_minutes ? <><Clock size={11} /> {t("medien.minutes", { n: film.duration_minutes })}</> : null}
        {film.year ? <span>· {film.year}</span> : null}
        {film.genre ? <span className="truncate">· {film.genre}</span> : null}
      </p>
      <PriceTag item={film} className="mt-0.5" />
    </Link>
  );
}

function Row({ title, films, testId }: { title: string; films: FilmCard[]; testId?: string }) {
  if (!films.length) return null;
  return (
    <section data-testid={testId ?? "film-row"}>
      <SectionTitle>{title}</SectionTitle>
      <div className="flex snap-x gap-3 overflow-x-auto pb-3">{films.map((f) => <FilmTile key={f.id} film={f} />)}</div>
    </section>
  );
}

/** Filme: cinematic hero for the featured film, "Weiter ansehen", one row per category and a filter bar (title, category,
 * level, length, genre, free / paid). With a filter or a search the rows turn into a result grid. */
export default function FilmeClient() {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [level, setLevel] = useState("");
  const [length, setLength] = useState("");
  const [genre, setGenre] = useState("");
  const [access, setAccess] = useState("");
  const [page, setPage] = useState(1);
  const q = useDebounced(search);
  const filtering = !!(q || category || level || length || genre || access);

  const overview = useQuery({ queryKey: ["medien-overview"], queryFn: getOverview });
  const cats = useQuery({ queryKey: ["medien-categories", "FILM"], queryFn: () => getCategories("FILM"), staleTime: 60_000 });
  const cont = useQuery({ queryKey: ["medien-continue", "FILM"], queryFn: () => getContinue(false) });
  const rows = useQueries({ queries: (cats.data ?? []).filter((c) => (c.count ?? 0) > 0).map((c) => ({ queryKey: ["medien-films-row", c.slug], queryFn: () => getFilms({ category: c.slug, page_size: 14 }), enabled: !filtering, staleTime: 30_000 })) });
  const results = useQuery({
    queryKey: ["medien-films", q, category, level, length, genre, access, page],
    queryFn: () => getFilms({ q, category, level, genre, access, ...DURATIONS[length], page, page_size: PAGE_SIZE }),
    enabled: filtering, placeholderData: (p) => p,
  });
  const genres = useQuery({ queryKey: ["medien-films-genres"], queryFn: async () => [...new Set((await getFilms({ page_size: 60 })).items.map((f) => f.genre).filter(Boolean) as string[])].sort(), staleTime: 60_000 });
  const hero = overview.data?.featured_film ?? null;
  const select = "rounded-xl bg-surface-card px-3 py-2 text-sm text-text-primary ring-1 ring-surface-border";
  const reset = <T,>(set: (v: T) => void) => (v: T) => { set(v); setPage(1); };
  const continuing = (cont.data ?? []).filter((c) => c.kind === "FILM") as (FilmCard & { progress: { position: number; total: number | null } })[];

  return (
    <div className="space-y-8" data-testid="filme">
      <Link href="/medien" className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary hover:text-accent-blue"><ArrowLeft size={16} /> {t("medien.title")}</Link>

      {hero ? (
        <header className="relative isolate overflow-hidden rounded-3xl bg-slate-950 text-white shadow-[var(--shadow-md)]" data-testid="film-hero">
          <Cover src={hero.cover_url} kind="FILM" eager className="absolute inset-0 -z-10 opacity-60 blur-[2px]" />
          <div className="absolute inset-0 -z-10 bg-gradient-to-r from-slate-950 via-slate-950/80 to-transparent" />
          <div className="max-w-2xl space-y-3 p-6 sm:p-12">
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-white/60">{t("medien.featuredFilm")}</p>
            <h1 className="text-3xl font-extrabold sm:text-5xl">{hero.title}</h1>
            <p className="flex flex-wrap items-center gap-2 text-sm text-white/80">
              {hero.language && <span className="rounded bg-white/15 px-2 py-0.5 font-semibold uppercase">{hero.language}</span>}
              {hero.level && <span className="rounded bg-white/15 px-2 py-0.5 font-semibold">{hero.level}</span>}
              {hero.duration_minutes && <span>{t("medien.minutes", { n: hero.duration_minutes })}</span>}
              {hero.genre && <span>· {hero.genre}</span>}
            </p>
            {hero.description && <p className="line-clamp-3 text-sm text-white/85 sm:text-base">{hero.description}</p>}
            <Link href={`/medien/filme/${hero.id}`} data-testid="film-hero-watch" className="inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-sm font-bold text-slate-900 transition hover:opacity-90"><Play size={16} /> {t("medien.watch")}</Link>
          </div>
        </header>
      ) : (
        <header className="rounded-3xl bg-gradient-to-br from-sky-700 via-blue-900 to-slate-950 p-6 text-white shadow-[var(--shadow-md)] sm:p-9">
          <h1 className="text-2xl font-extrabold sm:text-4xl">{t("medien.films")}</h1>
          <p className="mt-1 text-white/75">{t("medien.filmsDesc")}</p>
        </header>
      )}

      <MedienStatsSection kind="FILM" />

      <div className="flex flex-wrap gap-2">
        <label className="relative min-w-[14rem] flex-1"><Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input value={search} onChange={(e) => reset(setSearch)(e.target.value)} placeholder={t("medien.searchFilms")} aria-label={t("medien.searchFilms")} data-testid="film-search" className={cn(select, "w-full pl-9")} /></label>
        <select value={category} onChange={(e) => reset(setCategory)(e.target.value)} aria-label={t("medien.category")} data-testid="film-category" className={select}>
          <option value="">{t("medien.allCategories")}</option>{(cats.data ?? []).map((c) => <option key={c.id} value={c.slug}>{c.name}</option>)}</select>
        <select value={level} onChange={(e) => reset(setLevel)(e.target.value)} aria-label={t("medien.level")} data-testid="film-level" className={select}>
          <option value="">{t("medien.allLevels")}</option>{LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}</select>
        <select value={length} onChange={(e) => reset(setLength)(e.target.value)} aria-label={t("medien.length")} data-testid="film-length" className={select}>
          <option value="">{t("medien.anyLength")}</option><option value="short">{t("medien.lengthShort")}</option><option value="medium">{t("medien.lengthMedium")}</option><option value="long">{t("medien.lengthLong")}</option></select>
        <select value={genre} onChange={(e) => reset(setGenre)(e.target.value)} aria-label={t("medien.genre")} data-testid="film-genre" className={select}>
          <option value="">{t("medien.allGenres")}</option>{(genres.data ?? []).map((g) => <option key={g} value={g}>{g}</option>)}</select>
        <select value={access} onChange={(e) => reset(setAccess)(e.target.value)} aria-label={t("medien.access")} data-testid="film-access" className={select}>
          <option value="">{t("medien.freeAndPaid")}</option><option value="FREE">{t("medien.free")}</option><option value="PAID">{t("medien.paid")}</option></select>
      </div>

      {filtering ? (
        <section data-testid="film-results">
          {results.data && !results.data.items.length && <EmptyState text={t("medien.noFilms")} />}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-6">{results.data?.items.map((f) => <FilmTile key={f.id} film={f} wide />)}</div>
          <Pager page={page} pageSize={PAGE_SIZE} total={results.data?.total ?? 0} onChange={setPage} />
        </section>
      ) : (
        <>
          {!!continuing.length && (
            <section data-testid="film-continue">
              <SectionTitle>{t("medien.continueWatching")}</SectionTitle>
              <div className="flex snap-x gap-3 overflow-x-auto pb-3">
                {continuing.map((f) => {
                  const pct = f.progress.total ? Math.min(100, Math.round((100 * f.progress.position) / f.progress.total)) : 0;
                  return (
                    <Link key={f.id} href={`/medien/filme/${f.id}`} className="group w-60 shrink-0 snap-start" data-testid="continue-film">
                      <div className="relative overflow-hidden rounded-xl shadow-md"><Cover src={f.cover_url} kind="FILM" alt={f.title} className="aspect-video w-full transition group-hover:scale-105" />
                        <div className="absolute inset-x-0 bottom-0 h-1.5 bg-black/50"><div className="h-full bg-accent-blue" style={{ width: `${pct}%` }} /></div></div>
                      <p className="mt-2 truncate text-sm font-semibold text-text-primary">{f.title}</p><p className="text-xs text-text-muted">{pct}%</p>
                    </Link>
                  );
                })}
              </div>
            </section>
          )}
          {(cats.data ?? []).filter((c) => (c.count ?? 0) > 0).map((c, i) => <Row key={c.id} title={c.name} films={rows[i]?.data?.items ?? []} />)}
          {cats.data && !cats.data.some((c) => (c.count ?? 0) > 0) && <EmptyState text={t("medien.noFilms")} />}
        </>
      )}
    </div>
  );
}
