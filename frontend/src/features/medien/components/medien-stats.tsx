"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { BookOpen, ChevronDown, Clapperboard, Clock, Info, Music } from "lucide-react";

import ActivityBars from "@/features/activity/components/activity-bars";
import { formatClock, formatDate, formatDateTime, formatDuration, percent } from "@/features/activity/lib/format";
import type { BookStat, FilmStat, MediaStats, SongStat } from "@/features/activity/types";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import { getMediaStats } from "../services/medien-service";

export const MEDIA_STATS_KEY = ["medien-stats"] as const;

function useMediaStats() {
  return useQuery({ queryKey: MEDIA_STATS_KEY, queryFn: getMediaStats, staleTime: 60_000, refetchOnWindowFocus: true });
}

function Card({ icon: Icon, label, value, lines, tone, testId }: { icon: typeof Music; label: string; value: string; lines: string[]; tone: string; testId: string }) {
  return (
    <div className="flex items-start gap-4 rounded-2xl bg-surface-card p-5 shadow-[var(--shadow-md)] ring-1 ring-surface-border" data-testid={testId}>
      <div className={cn("flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl text-white", tone)}><Icon size={20} /></div>
      <div className="min-w-0">
        <p className="text-sm font-medium text-text-secondary">{label}</p>
        <p className="mt-0.5 text-2xl font-extrabold text-text-primary" data-testid={`${testId}-value`}>{value}</p>
        {lines.map((line) => <p key={line} className="text-xs text-text-muted">{line}</p>)}
      </div>
    </div>
  );
}

function Privacy() {
  const { t } = useTranslation();
  return (
    <details className="rounded-2xl bg-accent-blue/5 px-4 py-3 text-sm ring-1 ring-accent-blue/15" data-testid="medien-stats-privacy">
      <summary className="flex cursor-pointer select-none items-center gap-2 font-medium text-text-primary"><Info size={15} className="text-accent-blue" />{t("mstats.privacyTitle")}</summary>
      <p className="mt-2 text-text-secondary">{t("mstats.privacyText")}</p>
      <p className="mt-1 text-xs text-text-muted">{t("mstats.oldPlays")}</p>
    </details>
  );
}

function Since({ data }: { data: MediaStats }) {
  const { t, language } = useTranslation();
  return <p className="text-xs text-text-muted">{data.tracking_since ? t("mstats.since", { date: formatDate(data.tracking_since, language) }) : t("mstats.sinceNow")}</p>;
}

/** Top of Medien: Musik gehört / Bücher angesehen / Filme angesehen, the total media time, 14 days by area and the latest items. */
export function MedienStatsOverview() {
  const { t, language } = useTranslation();
  const { data, isLoading, isError, refetch } = useMediaStats();

  if (isLoading) {
    return <div className="grid gap-4 md:grid-cols-4" aria-busy="true">{[0, 1, 2, 3].map((i) => <div key={i} className="h-28 animate-pulse rounded-2xl bg-surface-card ring-1 ring-surface-border" />)}</div>;
  }
  if (isError || !data) {
    return (
      <p className="rounded-2xl bg-danger/5 p-4 text-sm text-danger ring-1 ring-danger/20" role="alert">
        {t("mstats.loadError")} <button className="underline" onClick={() => refetch()}>{t("tpanel.retry")}</button>
      </p>
    );
  }
  const recent = [
    ...data.music.recent.map((s) => ({ kind: "MUSIC" as const, id: s.id, title: s.title, sub: s.artist, at: s.last_listened_at, href: "/medien/musik" })),
    ...data.books.recent.map((b) => ({ kind: "BOOK" as const, id: b.id, title: b.title, sub: b.author, at: b.last_opened_at, href: `/medien/bibliothek/${b.id}` })),
    ...data.films.recent.map((f) => ({ kind: "FILM" as const, id: f.id, title: f.title, sub: null, at: f.last_watched_at, href: `/medien/filme/${f.id}` })),
  ].sort((a, b) => (b.at ?? "").localeCompare(a.at ?? "")).slice(0, 6);
  const ICONS = { MUSIC: Music, BOOK: BookOpen, FILM: Clapperboard };

  return (
    <section className="space-y-4" data-testid="medien-stats" aria-labelledby="medien-stats-title">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <h2 id="medien-stats-title" className="text-lg font-bold text-text-primary">{t("mstats.title")}</h2>
        <Since data={data} />
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card icon={Music} tone="bg-gradient-to-br from-fuchsia-600 to-indigo-700" testId="stat-music" label={t("mstats.musicHeard")}
              value={t("mstats.songs", { n: data.music.songs_listened })}
              lines={[`${t("mstats.listened")}: ${formatDuration(data.music.listened_seconds, language)}`, t("mstats.plays", { n: data.music.play_count })]} />
        <Card icon={BookOpen} tone="bg-gradient-to-br from-amber-600 to-stone-800" testId="stat-books" label={t("mstats.booksViewed")}
              value={t("mstats.books", { n: data.books.books_opened })}
              lines={[`${t("mstats.reading")}: ${formatDuration(data.books.reading_seconds, language)}`, t("mstats.completed", { n: data.books.books_completed })]} />
        <Card icon={Clapperboard} tone="bg-gradient-to-br from-sky-600 to-slate-800" testId="stat-films" label={t("mstats.filmsViewed")}
              value={t("mstats.films", { n: data.films.films_watched })}
              lines={[`${t("mstats.watching")}: ${formatDuration(data.films.watched_seconds, language)}`, t("mstats.completed", { n: data.films.films_completed })]} />
        <Card icon={Clock} tone="bg-gradient-to-br from-brand-700 to-[#12306e]" testId="stat-usage" label={t("mstats.usageTime")}
              value={formatDuration(data.media_seconds, language)} lines={[t("mstats.chartTitle")]} />
      </div>
      <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <ActivityBars days={data.daily} language={language} title={t("mstats.chartTitle")} tableLabel={t("mstats.table")} emptyLabel={t("mstats.chartEmpty")}
                      series={[{ key: "MUSIC", label: t("mstats.areaMUSIC") }, { key: "BOOK", label: t("mstats.areaBOOK") }, { key: "FILM", label: t("mstats.areaFILM") }]}
                      testId="medien-stats-chart" />
        <div className="rounded-2xl bg-surface-card p-4 ring-1 ring-surface-border sm:p-5" data-testid="medien-stats-recent">
          <p className="text-sm font-semibold text-text-primary">{t("mstats.recent")}</p>
          {recent.length === 0 ? (
            <p className="mt-6 text-center text-sm text-text-muted">{t("mstats.emptyMusic")}</p>
          ) : (
            <ul className="mt-3 space-y-2.5">
              {recent.map((r) => {
                const Icon = ICONS[r.kind];
                return (
                  <li key={`${r.kind}-${r.id}`}>
                    <Link href={r.href} className="flex items-center gap-3 rounded-xl p-1.5 transition hover:bg-surface-hover">
                      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-surface-hover text-text-secondary"><Icon size={16} /></span>
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-sm font-medium text-text-primary">{r.title}</span>
                        <span className="block truncate text-xs text-text-muted">{[r.sub, formatDateTime(r.at, language)].filter(Boolean).join(" · ")}</span>
                      </span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </div>
      <Privacy />
    </section>
  );
}

function Toggle({ open, onClick, testId }: { open: boolean; onClick: () => void; testId: string }) {
  const { t } = useTranslation();
  return (
    <button type="button" onClick={onClick} aria-expanded={open} data-testid={testId}
            className="inline-flex items-center gap-1.5 rounded-full bg-surface-card px-3 py-1.5 text-sm font-medium text-text-primary ring-1 ring-surface-border transition hover:bg-surface-hover">
      {open ? t("mstats.hide") : t("mstats.show")}
      <ChevronDown size={15} className={cn("transition", open && "rotate-180")} />
    </button>
  );
}

function Row({ cells }: { cells: React.ReactNode[] }) {
  return <tr className="border-t border-surface-border">{cells.map((c, i) => <td key={i} className="py-2 pr-3 align-top">{c}</td>)}</tr>;
}

function Table({ head, children }: { head: string[]; children: React.ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[520px] text-left text-sm">
        <thead><tr className="text-xs text-text-muted">{head.map((h) => <th key={h} className="pb-2 pr-3 font-medium">{h}</th>)}</tr></thead>
        <tbody className="text-text-secondary">{children}</tbody>
      </table>
    </div>
  );
}

/** One section's statistics (Musik / Bibliothek / Filme), folded by default. */
export function MedienStatsSection({ kind }: { kind: "MUSIC" | "BOOK" | "FILM" }) {
  const { t, language } = useTranslation();
  const [open, setOpen] = useState(false);
  const [all, setAll] = useState(false);
  const { data, isError } = useMediaStats();
  const testId = `medien-section-stats-${kind.toLowerCase()}`;

  const summary = !data ? "…" : kind === "MUSIC"
    ? `${t("mstats.songs", { n: data.music.songs_listened })} · ${formatDuration(data.music.listened_seconds, language)}`
    : kind === "BOOK"
      ? `${t("mstats.books", { n: data.books.books_opened })} · ${formatDuration(data.books.reading_seconds, language)}`
      : `${t("mstats.films", { n: data.films.films_watched })} · ${formatDuration(data.films.watched_seconds, language)}`;
  const label = kind === "MUSIC" ? t("mstats.musicHeard") : kind === "BOOK" ? t("mstats.booksViewed") : t("mstats.filmsViewed");
  const limit = all ? 50 : 8;

  return (
    <section className="rounded-2xl bg-surface-card/70 p-4 ring-1 ring-surface-border" data-testid={testId}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-text-secondary"><span className="font-semibold text-text-primary">{label}:</span> <span data-testid={`${testId}-summary`}>{summary}</span></p>
        <Toggle open={open} onClick={() => setOpen((v) => !v)} testId={`${testId}-toggle`} />
      </div>
      {open && isError && <p className="mt-3 text-sm text-danger" role="alert">{t("mstats.loadError")}</p>}
      {open && data && (
        <div className="mt-4 space-y-4">
          {kind === "MUSIC" && <MusicBlock songs={data.music.history.slice(0, limit)} top={data.music.top} />}
          {kind === "BOOK" && <BookBlock books={data.books.history.slice(0, limit)} />}
          {kind === "FILM" && <FilmBlock films={data.films.history.slice(0, limit)} continueList={data.films.continue} />}
          {(kind === "MUSIC" ? data.music.history : kind === "BOOK" ? data.books.history : data.films.history).length > 8 && (
            <button type="button" className="text-sm font-medium text-accent-blue" onClick={() => setAll((v) => !v)}>{all ? t("mstats.less") : t("mstats.more")}</button>
          )}
          <Since data={data} />
        </div>
      )}
    </section>
  );
}

function MusicBlock({ songs, top }: { songs: SongStat[]; top: SongStat[] }) {
  const { t, language } = useTranslation();
  if (!songs.length) return <p className="text-sm text-text-muted">{t("mstats.emptyMusic")}</p>;
  return (
    <>
      {!!top.length && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-text-muted">{t("mstats.top")}</p>
          <ol className="flex flex-wrap gap-2">
            {top.map((s, i) => (
              <li key={s.id} className="rounded-full bg-surface-hover px-3 py-1 text-xs text-text-primary">{i + 1}. {s.title} · {formatDuration(s.listened_seconds, language)}</li>
            ))}
          </ol>
        </div>
      )}
      <Table head={[t("mstats.colTitle"), t("mstats.colArtist"), t("mstats.colTime"), t("mstats.colPlays"), t("mstats.colLast")]}>
        {songs.map((s) => <Row key={s.id} cells={[<span key="t" className="font-medium text-text-primary">{s.title}</span>, s.artist ?? "—",
          formatDuration(s.listened_seconds, language), s.play_count, formatDateTime(s.last_listened_at, language)]} />)}
      </Table>
    </>
  );
}

function BookBlock({ books }: { books: BookStat[] }) {
  const { t, language } = useTranslation();
  if (!books.length) return <p className="text-sm text-text-muted">{t("mstats.emptyBooks")}</p>;
  return (
    <Table head={[t("mstats.colTitle"), t("mstats.colProgress"), t("mstats.colTime"), t("mstats.colLast")]}>
      {books.map((b) => (
        <Row key={b.id} cells={[
          <Link key="t" href={`/medien/bibliothek/${b.id}`} className="font-medium text-text-primary hover:underline">{b.title}</Link>,
          b.completed ? t("mstats.done") : b.page ? t("mstats.pageOf", { page: b.page, total: b.pages ?? "?" }) : "—",
          formatDuration(b.reading_seconds, language), formatDateTime(b.last_opened_at, language)]} />
      ))}
    </Table>
  );
}

function FilmBlock({ films, continueList }: { films: FilmStat[]; continueList: FilmStat[] }) {
  const { t, language } = useTranslation();
  if (!films.length) return <p className="text-sm text-text-muted">{t("mstats.emptyFilms")}</p>;
  return (
    <>
      {!!continueList.length && (
        <div className="flex flex-wrap gap-2" data-testid="film-continue">
          {continueList.map((f) => (
            <Link key={f.id} href={`/medien/filme/${f.id}`} className="rounded-full bg-accent-blue/10 px-3 py-1.5 text-xs font-medium text-accent-blue hover:bg-accent-blue/15">
              {t("mstats.continueWatching")}: {f.title} · {t("mstats.continueAt", { time: formatClock(f.position_seconds) })}
            </Link>
          ))}
        </div>
      )}
      <Table head={[t("mstats.colTitle"), t("mstats.colProgress"), t("mstats.colTime"), t("mstats.colLast")]}>
        {films.map((f) => {
          const pct = percent(f.position_seconds, f.duration_seconds);
          return <Row key={f.id} cells={[<Link key="t" href={`/medien/filme/${f.id}`} className="font-medium text-text-primary hover:underline">{f.title}</Link>,
            f.completed ? t("mstats.done") : pct !== null ? `${pct}%` : formatClock(f.position_seconds),
            formatDuration(f.watched_seconds, language), formatDateTime(f.last_watched_at, language)]} />;
        })}
      </Table>
    </>
  );
}
