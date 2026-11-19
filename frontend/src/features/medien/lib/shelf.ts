/* Pure helpers of the Bibliothek bookshelf (no React, no project imports: unit-tested with node --test). */

export interface ShelfCategory { id: string; name: string; slug: string }
export interface ShelfGroup<T> { key: string; name: string; slug: string; books: T[] }

/** How many books stand side by side on one shelf board for a shelf this wide (px): never so many that a cover gets smaller than
 * ~96 px on a phone / ~118 px elsewhere, at least 2, at most 8. */
export function shelfColumns(width: number): number {
  if (!Number.isFinite(width) || width <= 0) return 3;
  const phone = width < 640;
  const min = phone ? 96 : 118;
  const gap = phone ? 12 : 22;
  return Math.max(2, Math.min(8, Math.floor((width + gap) / (min + gap))));
}

/** The books in rows of `n` (one row = one shelf board). */
export function rowsOf<T>(items: readonly T[], n: number): T[][] {
  const size = Math.max(1, Math.floor(n));
  const out: T[][] = [];
  for (let i = 0; i < items.length; i += size) out.push(items.slice(i, i + size));
  return out;
}

/** One shelf per category, in the admin's category order; books without a (known) category go to a last shelf named `otherName`.
 * Empty categories get no shelf. The order of the books inside a shelf is the order they came in (the chosen sort). */
export function groupByCategory<T extends { category: ShelfCategory | null }>(items: readonly T[], categories: readonly ShelfCategory[], otherName: string): ShelfGroup<T>[] {
  const known = new Map(categories.map((c, i) => [c.id, i]));
  const groups = new Map<string, ShelfGroup<T>>();
  for (const book of items) {
    const cat = book.category && known.has(book.category.id) ? book.category : null;
    const key = cat ? cat.id : "__other";
    if (!groups.has(key)) groups.set(key, { key, name: cat ? cat.name : otherName, slug: cat ? cat.slug : "", books: [] });
    groups.get(key)!.books.push(book);
  }
  return [...groups.values()].sort((a, b) => (known.get(a.key) ?? 1e9) - (known.get(b.key) ?? 1e9));
}
