"use client";

import BookManager from "@/features/admin/components/managers/book-manager";

export default function AdminBooksPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-[var(--admin-text-primary)]">Bücher</h1>
        <p className="mt-1 text-sm text-[var(--admin-text-secondary)]">
          PDF-Bücher pro Level verwalten — sichtbar für Studenten am Anfang ihrer Lektionsliste, öffnen nur mit
          Premium.
        </p>
      </div>

      <BookManager />
    </div>
  );
}
