"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Check, Lock, Search } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import { groupByCategory, rowsOf, shelfColumns } from "../lib/shelf";
import { getBooks, getCategories } from "../services/medien-service";
import { LEVELS, type BookCard } from "../types";
import { BookBuyButton, MyBookPayments } from "./book-payment";
import { Cover, EmptyState, formatPrice, Pager, PriceTag, SectionTitle, useDebounced } from "./media-ui";

const PAGE_SIZE = 60;

/** Width of an element, kept up to date (the shelves decide how many books fit side by side from it). */
function useWidth<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new ResizeObserver(() => setWidth(el.clientWidth));
    observer.observe(el);
    setWidth(el.clientWidth);
    return () => observer.disconnect();
  }, []);
  return [ref, width] as const;
}

/** The small sign on a cover: free / bought / price with a lock. */
function AccessSign({ book }: { book: BookCard }) {
  const { t } = useTranslation();
  if (book.access_type === "FREE") {
    return <span className="rounded-full bg-success px-2 py-0.5 text-[10px] font-bold uppercase text-white shadow" data-testid="book-sign-free">{t("medien.free")}</span>;
  }
  if (!book.locked) {
    return <span className="inline-flex items-center gap-1 rounded-full bg-success px-2 py-0.5 text-[10px] font-bold uppercase text-white shadow" data-testid="book-sign-owned"><Check size={10} />{t("medien.shelfOwned")}</span>;
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-black/75 px-2 py-0.5 text-[10px] font-bold text-white shadow" data-testid="book-sign-locked">
      <Lock size={10} />{book.price ? formatPrice(book.price, book.currency) : t("medien.paid")}
    </span>
  );
}

/** One book standing on a board: the cover in real proportions (2:3) with a spine shadow; lifts on hover (GPU transform only). */
function BookOnShelf({ book }: { book: BookCard }) {
  return (
    <Link href={`/medien/bibliothek/${book.id}`} data-testid="book-card" data-free={book.access_type === "FREE" ? "1" : "0"} data-locked={book.locked ? "1" : "0"}
          className="group relative block w-full max-w-[150px] justify-self-center focus-visible:outline-none" aria-label={book.title}>
      <div className="relative origin-bottom transition duration-300 ease-out will-change-transform group-hover:-translate-y-2.5 group-hover:scale-[1.03] group-focus-visible:-translate-y-2.5">
        <Cover src={book.cover_url} kind="BOOK" alt={book.title} className="aspect-[2/3] w-full rounded-r-md rounded-l-[3px] shadow-[4px_6px_14px_rgba(0,0,0,0.5)] ring-1 ring-black/20" />
        <span className="pointer-events-none absolute inset-y-0 left-0 w-2.5 rounded-l-[3px] bg-gradient-to-r from-black/50 via-white/10 to-transparent" />
        <span className="absolute right-1 top-1.5"><AccessSign book={book} /></span>
      </div>
    </Link>
  );
}

/** One board: the books stand on it side by side, their titles and authors are on the label strip below it. */
function Shelf({ books, columns }: { books: BookCard[]; columns: number }) {
  const { t } = useTranslation();
  const grid = { gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` };
  return (
    <div data-testid="shelf" data-columns={columns}>
      <div className="grid items-end gap-x-3 px-3 pt-5 sm:gap-x-5 sm:px-5" style={grid}>
        {books.map((b) => <BookOnShelf key={b.id} book={b} />)}
      </div>
      <div className="relative h-3.5 rounded-[3px] bg-gradient-to-b from-amber-600 via-amber-800 to-amber-950 shadow-[0_8px_14px_rgba(0,0,0,0.45)]" aria-hidden="true">
        <span className="absolute inset-x-0 top-0 h-px bg-amber-300/40" />
      </div>
      <div className="grid gap-x-3 px-3 pb-1 pt-2.5 sm:gap-x-5 sm:px-5" style={grid}>
        {books.map((b) => (
          <Link key={b.id} href={`/medien/bibliothek/${b.id}`} className="min-w-0 max-w-[150px] justify-self-center text-center" tabIndex={-1} data-testid="book-label">
            <span className="line-clamp-2 text-xs font-semibold leading-snug text-amber-50 sm:text-[13px]">{b.title}</span>
            <span className="mt-0.5 block truncate text-[11px] text-amber-100/60">{b.author ?? t("medien.unknownAuthor")}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}

/** A category: a brass name plate and as many boards as its books need (vertical — never a sideways scroll). */
function ShelfSection({ name, slug, books, columns }: { name: string; slug: string; books: BookCard[]; columns: number }) {
  const { t } = useTranslation();
  return (
    <section className="space-y-1" data-testid="shelf-section" data-slug={slug}>
      <div className="flex items-center gap-3 px-3 sm:px-5">
        <h2 className="rounded-md bg-gradient-to-b from-amber-200 to-amber-400 px-3 py-1 text-sm font-extrabold text-amber-950 shadow-[inset_0_1px_0_rgba(255,255,255,0.6),0_2px_6px_rgba(0,0,0,0.4)]">{name}</h2>
        <span className="text-xs text-amber-100/70">{books.length === 1 ? t("medien.shelfBook") : t("medien.shelfBooks", { n: books.length })}</span>
      </div>
      <div className="space-y-6">
        {rowsOf(books, columns).map((row, i) => <Shelf key={i} books={row} columns={columns} />)}
      </div>
    </section>
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
        <BookBuyButton book={book} size="sm" className="mt-auto pt-2" />
      </div>
    </div>
  );
}

/** Bibliothek: special offers on top, category chips, search (title / author), level + sort + free/paid filters, and the books on a real
 * bookcase: one shelf per category (Literatur, Grammatik, Zertifikatsbücher, Wortschatz, Sonstige … — from the admin panel, in its order),
 * boards stacked on top of each other, the covers side by side in their real proportions with title + author below and a free / price /
 * lock sign. The number of books per board follows the screen width, so the page only scrolls down. */
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
  const [caseRef, caseWidth] = useWidth<HTMLDivElement>();
  const columns = shelfColumns(caseWidth - 24);
  const groups = groupByCategory(items, categories.data ?? [], t("medien.shelfOther"));
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
      <div ref={caseRef} className={cn(!items.length && "hidden")}>
        {!!items.length && (
          <div className="space-y-8 rounded-3xl border-x-[6px] border-amber-950/80 bg-[linear-gradient(180deg,rgba(41,25,15,0.97),rgba(23,15,10,1))] py-5 shadow-[inset_0_10px_30px_rgba(0,0,0,0.6),0_10px_30px_-12px_rgba(0,0,0,0.5)] sm:py-7"
               data-testid="bookshelves">
            {groups.map((g) => <ShelfSection key={g.key} name={g.name} slug={g.slug} books={g.books} columns={columns} />)}
          </div>
        )}
      </div>
      {!!items.length && <ul className="sr-only">{items.map((b) => <li key={b.id}>{b.title} — {b.author}</li>)}</ul>}
      <Pager page={page} pageSize={PAGE_SIZE} total={books.data?.total ?? 0} onChange={setPage} />
      <MyBookPayments />
    </div>
  );
}
