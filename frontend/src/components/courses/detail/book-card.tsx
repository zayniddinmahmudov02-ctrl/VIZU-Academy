"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { BookOpen, Lock } from "lucide-react";

import type { Book } from "@/features/books/services/book-service";

interface Props {
  book: Book;
  isPremium: boolean;
  onOpen: () => void;
}

/** Mirrors ModuleCard's exact locked/unlocked visual language (see
 * components/courses/detail/module-card.tsx) — free users get a lock
 * badge + a link to /vizu-pay, Premium users get an "OCHISH" open pill
 * that opens the PDF viewer. `isPremium` here is only a one-time status
 * check driving this badge (see book-row.tsx) — the real gate is always
 * the backend's own check on the file endpoint, so a stale/wrong value
 * here can never actually leak a file. */
export default function BookCard({ book, isPremium, onOpen }: Props) {
  const locked = !isPremium;

  const content = (
    <>
      <div
        className={`flex aspect-[3/4] w-full items-center justify-center overflow-hidden rounded-xl ${
          locked ? "bg-slate-200 dark:bg-slate-700" : "bg-gradient-to-br from-yellow-500 to-amber-400"
        }`}
      >
        {book.cover_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={book.cover_url} alt={book.title} loading="lazy" className="h-full w-full object-cover" />
        ) : (
          <BookOpen size={32} className={locked ? "text-slate-500 dark:text-slate-300" : "text-white"} />
        )}
      </div>

      <div className="mt-2.5 space-y-0.5">
        <p className="line-clamp-2 text-sm font-bold text-text-primary">{book.title}</p>
        {book.author && <p className="truncate text-xs text-text-secondary">{book.author}</p>}
        <span className="inline-block rounded-full bg-surface-hover px-2 py-0.5 text-[10px] font-semibold text-text-muted">
          {book.level}
        </span>
      </div>

      <div className="mt-2.5">
        {locked ? (
          <div className="flex items-center justify-center gap-1.5 rounded-full bg-warning/15 px-3 py-1.5 text-xs font-semibold text-warning">
            <Lock size={12} />
            PREMIUM
          </div>
        ) : (
          <div className="flex items-center justify-center gap-1.5 rounded-full bg-[var(--accent-gold)] px-3 py-1.5 text-xs font-semibold text-white">
            <BookOpen size={12} />
            OCHISH
          </div>
        )}
      </div>
    </>
  );

  return (
    <motion.div whileHover={{ y: -3 }} transition={{ duration: 0.2 }}>
      {locked ? (
        <Link
          href="/vizu-pay"
          className="block rounded-2xl border border-slate-200 bg-slate-100 p-3 transition-all duration-300 dark:border-slate-700 dark:bg-slate-800"
        >
          {content}
        </Link>
      ) : (
        <button
          type="button"
          onClick={onOpen}
          className="block w-full rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card)] p-3 text-left transition-all duration-300 hover:border-[var(--accent-gold)] hover:shadow-xl"
        >
          {content}
        </button>
      )}
    </motion.div>
  );
}
