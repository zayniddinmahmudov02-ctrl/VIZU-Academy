"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, BookOpen, Lock } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

import { errorCode, getBook } from "../services/medien-service";
import { Cover, EmptyState, PriceTag, PurchaseButton, StatusBadge } from "./media-ui";
import PdfReader from "./pdf-reader";

/** Book details: cover, text, level, category and price — and "Lesen" (opens the PDF reader, resuming on the last page)
 * or the purchase button for PAID books that are not owned. The file itself is only ever fetched by the reader. */
export default function BookDetailClient({ bookId }: { bookId: string }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [reading, setReading] = useState(false);
  const { data: book, isLoading, error } = useQuery({ queryKey: ["medien-book", bookId], queryFn: () => getBook(bookId), retry: false });

  if (isLoading) return <p className="py-16 text-center text-sm text-text-secondary">{t("medien.loading")}</p>;
  if (error || !book) return <EmptyState text={errorCode(error) === "NOT_FOUND" ? t("medien.err.NOT_FOUND") : t("medien.err.GENERIC")} />;

  const page = book.progress?.position ?? 0;
  const meta = [book.level, book.category?.name, book.year, book.file_format?.toUpperCase()].filter(Boolean);

  return (
    <div className="space-y-6" data-testid="book-detail">
      <Link href="/medien/bibliothek" className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary hover:text-accent-blue"><ArrowLeft size={16} /> {t("medien.library")}</Link>
      <article className="grid gap-6 rounded-3xl bg-surface-card p-5 shadow-[var(--shadow-sm)] ring-1 ring-surface-border sm:p-8 md:grid-cols-[260px_1fr]">
        <div className="relative mx-auto w-48 md:w-full">
          <Cover src={book.cover_url} kind="BOOK" alt={book.title} eager className="aspect-[3/4] w-full rounded-r-lg rounded-l-[4px] shadow-[8px_10px_24px_rgba(0,0,0,0.4)]" />
          <span className="absolute right-2 top-2"><StatusBadge item={book} /></span>
        </div>
        <div className="min-w-0 space-y-4">
          <div>
            <h1 className="text-2xl font-extrabold text-text-primary sm:text-3xl" data-testid="book-title">{book.title}</h1>
            <p className="mt-1 text-text-secondary" data-testid="book-author">{book.author ?? t("medien.unknownAuthor")}</p>
          </div>
          <div className="flex flex-wrap gap-2">{meta.map((m) => <span key={String(m)} className="rounded-full bg-surface-hover px-3 py-1 text-xs font-semibold text-text-secondary">{m}</span>)}</div>
          {book.description && <p className="whitespace-pre-line text-sm leading-relaxed text-text-secondary" data-testid="book-description">{book.description}</p>}
          <div className="flex flex-wrap items-center gap-4 pt-2">
            <PriceTag item={book} />
            {book.locked ? (
              <PurchaseButton item={book} />
            ) : (
              <button type="button" disabled={!book.has_file} onClick={() => setReading(true)} data-testid="book-read"
                      className="inline-flex items-center gap-2 rounded-xl bg-accent-blue px-5 py-2.5 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50">
                <BookOpen size={16} /> {page > 1 ? t("medien.readContinue", { page }) : t("medien.read")}
              </button>
            )}
          </div>
          {book.locked && (
            <p className="flex items-center gap-2 rounded-xl bg-warning/10 p-3 text-sm text-text-secondary" data-testid="book-locked-note"><Lock size={15} className="shrink-0 text-warning" /> {t("medien.lockedNote")}</p>
          )}
        </div>
      </article>
      {reading && <PdfReader bookId={book.id} title={book.title} onClose={() => { setReading(false); void queryClient.invalidateQueries({ queryKey: ["medien-book", bookId] }); void queryClient.invalidateQueries({ queryKey: ["medien-overview"] }); }} />}
    </div>
  );
}
