import { api } from "@/src/services/api";

import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type { Book, BookCreate, BookUpdate } from "../types/content.types";

// Not built on createCrudApi (which hardcodes PUT for updates) — the
// backend's admin book router uses PATCH, matching the endpoint list
// the feature was specced against exactly.
export const booksApi = {
  // No params here — same convention as vocabularyApi/quizzesApi: fetch
  // every admin row once, filter by level client-side (see
  // book-manager.tsx), matching how those managers filter by lessonId.
  async list(): Promise<Book[]> {
    const response = await api.get<Book[]>(ADMIN_ENDPOINTS.adminBooks);
    return response.data;
  },
  async get(id: string): Promise<Book> {
    const response = await api.get<Book>(`${ADMIN_ENDPOINTS.adminBooks}/${id}`);
    return response.data;
  },
  async create(data: BookCreate): Promise<Book> {
    const response = await api.post<Book>(ADMIN_ENDPOINTS.adminBooks, data);
    return response.data;
  },
  async update(id: string, data: BookUpdate): Promise<Book> {
    const response = await api.patch<Book>(`${ADMIN_ENDPOINTS.adminBooks}/${id}`, data);
    return response.data;
  },
  async remove(id: string): Promise<void> {
    await api.delete(`${ADMIN_ENDPOINTS.adminBooks}/${id}`);
  },
  async publish(id: string): Promise<Book> {
    const response = await api.post<Book>(`${ADMIN_ENDPOINTS.adminBooks}/${id}/publish`);
    return response.data;
  },
};

export async function uploadBookPdf(bookId: string, file: File): Promise<Book> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post<Book>(`${ADMIN_ENDPOINTS.adminBooks}/${bookId}/upload-pdf`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}
