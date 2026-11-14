"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Search } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import { getBooks, getCategories } from "../services/medien-service";
import { LEVELS, type BookCard } from "../types";
import { Cover, EmptyState, Pager, PriceTag, PurchaseButton, SectionTitle, StatusBadge, useDebounced } from "./media-ui";

const PAGE_SIZE = 24;
const PER_SHELF = 8;

/** One book standing on a shelf: cover with a spine shadow, lifts on hover (GPU transform only — cheap and smooth). */
function BookOnShelf({ book }: { book: BookCard }) {
  return (
    <Link href={`/medien/bibliothek/${book.id}`} data-testid="book-card" data-free={book.access_type === "FREE" ? "1" : "0"} data-locked={book.locked ? "1" : "0"}
          className="group relative w-32 shrink-0 snap-start sm:w-36" aria-label={book.title}>
      <div className="relative origin-bottom transition duration-300 ease-out will-change-transform group-hover:-translate-y-3 group-hover:scale-[1.04] group-focus-visible:-translate-y-3">
        <Cover src={book.cover_url} kind="BOOK" alt={book.title} className="aspect-[3/4] w-full rounded-r-md rounded-l-[3px] shadow-[4px_6px_14px_rgba(0,0,0,0.45)]" />
        <span className="pointer-events-none absolute inset-y-0 left-0 w-2.5 rounded-l-[3px] bg-gradient-to-r from-black/45 via-white/10 to-transparent" />
        <span className="absolute right-1.5 top-1.5"><StatusBadge item={book} /></span>
      </div>
    </Link>
  );
}

function Shelf({ books }: { books: BookCard[] }) {
  return (
    <div className="relative" data-testid="shelf">
      <div className="flex snap-x items-end gap-4 overflow-x-auto px-4 pb-1 pt-6 sm:gap-6 sm:px-6">
        {books.map((b) => <BookOnShelf key={b.id} book={b} />)}
      </div>
      <div className="h-3.5 rounded-sm bg-gradient-to-b from-amber-700 via-amber-900 to-amber-950 shadow-[0_10px_18px_rgba(0,0,0,0.35)]" />
      <div className="mx-3 h-2 rounded-b-md bg-black/25 blur-[3px]" />
    </div>
  );
}

function OfferCard({ book }: { book: BookCard }) {
  const { t } = useTranslation();
  return (
    <div className="flex w-72 shrink-0 gap-3 rounded-2xl bg-surface-card p-3 shadow-[var(--shadow-sm)] ring-1 ring-accent-gold/40" data-testid="offer-card">
      <Link href={`/medien/bibliothek/${book.id}`} className="w-20 shrink-0"><Cover src={book.cover_url} kind="BOOK" alt={book.title} className="aspect-[3/4] w-full rounded-md shadow" /></Link>
      <div className="flex min-w-0 flex-1 flex-col">
        <Link href={`/medien/bibliothek/${book.id}`} className="truncate text-sm font-bold text-text-primary hover:underline">{book.title}</Link>
        <p className="truncate text-xs text-text-muted">{book.author ?? t("medien.unknownAuthor")}</p>
        <PriceTag item={book} className="mt-1" />
        <PurchaseButton item={book} size="sm" className="mt-auto pt-2" />
      </div>
    </div>
  );
}

/** Bibliothek: special offers on top, category chips, search (title / author), level + sort + free/paid filters, and the
 * books on real shelves (a shelf scrolls sideways on phones). Categories come from the admin panel. */
export default function BibliothekClient() {
  const { t } = useTranslation();
  const [category, setCategory] = useState("");
  const [level, setLevel] = useState("");
  const [sort, setSort] = useState("new");
  const [access, setAccess] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const q = useDebounced(search);

  const categories = useQuery({ queryKey: ["medien-categories", "BOOK"], queryFn: () => getCategories("BOOK"), staleTime: 60_000 });
  const offers = useQuery({ queryKey: ["medien-books-offers"], queryFn: () => getBooks({ special: true, page_size: 12 }), staleTime: 30_000 });
  const books = useQuery({
    queryKey: ["medien-books", category, level, sort, access, q, page],
    queryFn: () => getBooks({ category, level, sort, access, q, page, page_size: PAGE_SIZE }),
    placeholderData: (prev) => prev,
  });
  const items = books.data?.items ?? [];
  const shelves = Array.from({ length: Math.ceil(items.length / PER_SHELF) }, (_, i) => items.slice(i * PER_SHELF, (i + 1) * PER_SHELF));
  const reset = <T,>(set: (v: T) => void) => (v: T) => { set(v); setPage(1); };
  const select = "rounded-xl bg-surface-card px-3 py-2 text-sm text-text-primary ring-1 ring-surface-border";

  return (
    <div className="space-y-6" data-testid="bibliothek">
      <Link href="/medien" className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary hover:text-accent-blue"><ArrowLeft size={16} /> {t("medien.title")}</Link>
      <header className="rounded-3xl bg-gradient-to-br from-amber-800 via-stone-900 to-brand-900 p-6 text-white shadow-[var(--shadow-md)] sm:p-9">
        <h1 className="text-2xl font-extrabold sm:text-4xl">{t("medien.library")}</h1>
        <p className="mt-1 text-white/75">{t("medien.libraryDesc")}</p>
      </header>

      {!!offers.data?.items.length && (
        <section data-testid="bibliothek-offers">
          <SectionTitle>{t("medien.specialOffers")}</SectionTitle>
          <div className="flex snap-x gap-3 overflow-x-auto pb-2">{offers.data.items.map((b) => <OfferCard key={b.id} book={b} />)}</div>
        </section>
      )}

      <div className="flex flex-wrap items-center gap-2" data-testid="book-categories" role="tablist">
        {[{ id: "", name: t("medien.all"), slug: "" }, ...(categories.data ?? [])].map((c) => (
          <button key={c.id || "all"} role="tab" aria-selected={category === (c.slug || "")} onClick={() => reset(setCategory)(c.slug || "")} data-testid="book-category" data-slug={c.slug}
                  className={cn("rounded-full px-4 py-1.5 text-sm font-semibold transition", category === (c.slug || "") ? "bg-accent-blue text-white" : "bg-surface-card text-text-secondary ring-1 ring-surface-border hover:bg-surface-hover")}>
            {c.name}{"count" in c && typeof c.count === "number" ? <span className="ml-1.5 text-xs opacity-70">{c.count}</span> : null}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        <label className="relative min-w-[14rem] flex-1">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input value={search} onChange={(e) => reset(setSearch)(e.target.value)} placeholder={t("medien.searchBooks")} aria-label={t("medien.searchBooks")} data-testid="book-search"
                 className={cn(select, "w-full pl-9")} />
        </label>
        <select value={level} onChange={(e) => reset(setLevel)(e.target.value)} aria-label={t("medien.level")} data-testid="book-level" className={select}>
          <option value="">{t("medien.allLevels")}</option>
          {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
        </select>
        <select value={access} onChange={(e) => reset(setAccess)(e.target.value)} aria-label={t("medien.access")} data-testid="book-access" className={select}>
          <option value="">{t("medien.freeAndPaid")}</option>
          <option value="FREE">{t("medien.free")}</option>
          <option value="PAID">{t("medien.paid")}</option>
        </select>
        <select value={sort} onChange={(e) => reset(setSort)(e.target.value)} aria-label={t("medien.sort")} data-testid="book-sort" className={select}>
          <option value="new">{t("medien.sortNew")}</option>
          <option value="popular">{t("medien.sortPopular")}</option>
          <option value="title">{t("medien.sortTitle")}</option>
        </select>
      </div>

      {books.isLoading && <p className="py-10 text-center text-sm text-text-secondary">{t("medien.loading")}</p>}
      {books.isError && <EmptyState text={t("medien.err.GENERIC")} />}
      {books.data && !items.length && <EmptyState text={t("medien.noBooks")} />}
      {!!items.length && (
        <div className="space-y-8 rounded-3xl bg-gradient-to-b from-stone-900/90 to-stone-950 py-6 shadow-inner ring-1 ring-black/20" data-testid="bookshelves">
          {shelves.map((s, i) => <Shelf key={i} books={s} />)}
        </div>
      )}
      {!!items.length && <ul className="sr-only">{items.map((b) => <li key={b.id}>{b.title} — {b.author}</li>)}</ul>}
      <Pager page={page} pageSize={PAGE_SIZE} total={books.data?.total ?? 0} onChange={setPage} />
    </div>
  );
}
