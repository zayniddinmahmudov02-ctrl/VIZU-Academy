import { api } from "@/lib/api";

export interface Book {
  id: string;
  title: string;
  author: string | null;
  description: string | null;
  level: string;
  cover_url: string | null;
  order_index: number;
}

// Public, unauthenticated — matches how course/module/lesson listing
// already works. Published-only, level-filtered server-side; never
// includes any storage/file field (see BookPublicResponse).
export async function getBooksByLevel(level: string): Promise<Book[]> {
  return api<Book[]>(`/api/v1/books?level=${encodeURIComponent(level)}`);
}
