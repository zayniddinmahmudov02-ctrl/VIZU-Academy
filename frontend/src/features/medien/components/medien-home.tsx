"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, BookOpen, Clapperboard, Music } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

import { getOverview } from "../services/medien-service";
import { Cover, PriceTag, SectionTitle, StatusBadge } from "./media-ui";
import { MedienStatsOverview } from "./medien-stats";

const CARDS = [
  { href: "/medien/bibliothek", key: "library", icon: BookOpen, tone: "from-amber-600/90 via-amber-800 to-stone-950", count: "books" as const, testId: "medien-card-library" },
  { href: "/medien/musik", key: "music", icon: Music, tone: "from-fuchsia-600/90 via-violet-800 to-indigo-950", count: "songs" as const, testId: "medien-card-music" },
  { href: "/medien/filme", key: "films", icon: Clapperboard, tone: "from-sky-600/90 via-blue-900 to-slate-950", count: "films" as const, testId: "medien-card-films" },
];

/** VIZU MEDIENWELT start page: banner, the three worlds, continue reading / watching and the special offers. */
export default function MedienHome() {
  const { t } = useTranslation();
  const { data } = useQuery({ queryKey: ["medien-overview"], queryFn: getOverview });

  return (
    <div className="space-y-10" data-testid="medien-home">
      <header className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-brand-900 via-[#0b1d4a] to-[#12306e] p-7 text-white shadow-[var(--shadow-md)] sm:p-12">
        <div className="pointer-events-none absolute -right-16 -top-20 h-72 w-72 rounded-full bg-accent-blue/30 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-24 left-1/3 h-64 w-64 rounded-full bg-accent-gold/20 blur-3xl" />
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-white/60">VIZU Academy</p>
        <h1 className="mt-2 text-3xl font-extrabold tracking-tight sm:text-5xl" data-testid="medien-title">VIZU MEDIENWELT</h1>
        <p className="mt-3 max-w-xl text-base text-white/80 sm:text-lg">{t("medien.bannerSub")}</p>
      </header>

      <MedienStatsOverview />

      <section className="grid gap-4 md:grid-cols-3" aria-label="Medienwelt">
        {CARDS.map(({ href, key, icon: Icon, tone, count, testId }) => (
          <Link key={href} href={href} data-testid={testId}
                className={`group relative flex min-h-[200px] flex-col justify-between overflow-hidden rounded-3xl bg-gradient-to-br ${tone} p-6 text-white shadow-[var(--shadow-md)] transition hover:-translate-y-1 hover:shadow-[var(--shadow-lg)]`}>
            <Icon className="absolute -bottom-6 -right-4 text-white/10 transition group-hover:scale-110" size={150} aria-hidden />
            <div className="relative flex h-12 w-12 items-center justify-center rounded-2xl bg-white/15 text-white backdrop-blur"><Icon size={24} /></div>
            <div className="relative">
              <p className="text-2xl font-extrabold text-white">{t(`medien.${key}`)}</p>
              <p className="mt-1 text-sm text-white/80">{t(`medien.${key}Desc`)}</p>
              <p className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-white">
                {data ? t(`medien.${count}Count`, { n: data.counts[count] }) : "…"} <ArrowRight size={14} className="transition group-hover:translate-x-1" />
              </p>
            </div>
          </Link>
        ))}
      </section>

      {!!data?.continue.length && (
        <section data-testid="medien-continue">
          <SectionTitle>{t("medien.continue")}</SectionTitle>
          <div className="flex snap-x gap-3 overflow-x-auto pb-2">
            {data.continue.map((item) => {
              const pct = item.progress.total ? Math.min(100, Math.round((100 * item.progress.position) / item.progress.total)) : 0;
              const href = item.kind === "BOOK" ? `/medien/bibliothek/${item.id}` : `/medien/filme/${item.id}`;
              return (
                <Link key={`${item.kind}-${item.id}`} href={href} className="group w-44 shrink-0 snap-start" data-testid="continue-item">
                  <div className="relative">
                    <Cover src={item.cover_url} kind={item.kind} alt={item.title} className="aspect-[3/4] w-full rounded-xl shadow-md transition group-hover:-translate-y-1" />
                    <div className="absolute inset-x-0 bottom-0 h-1.5 overflow-hidden rounded-b-xl bg-black/40"><div className="h-full bg-accent-blue" style={{ width: `${pct}%` }} /></div>
                  </div>
                  <p className="mt-2 truncate text-sm font-semibold text-text-primary">{item.title}</p>
                  <p className="text-xs text-text-muted">{item.kind === "BOOK" ? t("medien.pageOf", { page: item.progress.position, total: item.progress.total ?? "?" }) : `${pct}%`}</p>
                </Link>
              );
            })}
          </div>
        </section>
      )}

      {!!data?.special_offers.length && (
        <section data-testid="medien-offers">
          <SectionTitle>{t("medien.specialOffers")}</SectionTitle>
          <div className="flex snap-x gap-3 overflow-x-auto pb-2">
            {data.special_offers.map((item) => (
              <Link key={`${item.kind}-${item.id}`} href={item.kind === "BOOK" ? `/medien/bibliothek/${item.id}` : `/medien/filme/${item.id}`} className="group w-44 shrink-0 snap-start">
                <div className="relative">
                  <Cover src={item.cover_url} kind={item.kind} alt={item.title} className="aspect-[3/4] w-full rounded-xl shadow-md transition group-hover:-translate-y-1" />
                  <span className="absolute left-2 top-2"><StatusBadge item={item} /></span>
                </div>
                <p className="mt-2 truncate text-sm font-semibold text-text-primary">{item.title}</p>
                <PriceTag item={item} />
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
