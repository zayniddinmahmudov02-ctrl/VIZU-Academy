"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import BookViewer from "@/components/books/book-viewer";
import { getBooksByLevel } from "@/features/books/services/book-service";
import { getStatus } from "@/features/vizu-pay/services/vizu-pay-service";

import BookCard from "./book-card";

interface Props {
  level: string;
}

/** Renders nothing if this level has no published books — the row only
 * ever appears above Lesson 1 when there's real content, never an empty
 * "BÜCHER" heading. Fetches the viewer's user's Premium status ONCE
 * here (not per book, not per book-card fetch attempt) purely to drive
 * card badges — see book-card.tsx's docstring on why that's safe. */
export default function BookRow({ level }: Props) {
  const { data: books } = useQuery({
    queryKey: ["public-books", level],
    queryFn: () => getBooksByLevel(level),
  });

  const { data: status } = useQuery({
    queryKey: ["vizu-pay-status"],
    queryFn: getStatus,
  });

  const [openBook, setOpenBook] = useState<{ id: string; title: string } | null>(null);

  if (!books || books.length === 0) {
    return null;
  }

  return (
    <section className="space-y-4">
      <h2 className="flex items-center gap-2 text-lg font-bold text-text-primary">📚 BÜCHER</h2>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
        {books.map((book) => (
          <BookCard
            key={book.id}
            book={book}
            isPremium={!!status?.isPremium}
            onOpen={() => setOpenBook({ id: book.id, title: book.title })}
          />
        ))}
      </div>

      {openBook && <BookViewer bookId={openBook.id} title={openBook.title} onClose={() => setOpenBook(null)} />}
    </section>
  );
}
