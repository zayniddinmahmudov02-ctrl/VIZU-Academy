import { api } from "@/src/services/api";

export interface CrudApi<TResponse, TCreate, TUpdate> {
  list: (params?: Record<string, string>) => Promise<TResponse[]>;
  create: (data: TCreate) => Promise<TResponse>;
  update: (id: string, data: TUpdate) => Promise<TResponse>;
  remove: (id: string) => Promise<void>;
}

/** Builds a plain-JSON CRUD client for one of the ~15 flat content-type
 * endpoints (grammar, vocabulary, quiz, ...) — every one of them follows
 * the exact same `GET base / POST base / PUT base/{id} / DELETE base/{id}`
 * shape, so this is the only implementation needed for all of them. */
export function createCrudApi<TResponse, TCreate, TUpdate>(
  basePath: string,
): CrudApi<TResponse, TCreate, TUpdate> {
  // Some list/create endpoints are registered with a trailing slash
  // (`/languages/`), others without (`/grammars`) — normalize once here so
  // item-level URLs never end up with a double slash either way.
  const itemBase = basePath.endsWith("/") ? basePath.slice(0, -1) : basePath;

  return {
    async list(params) {
      const response = await api.get<TResponse[]>(basePath, { params });
      return response.data;
    },
    async create(data) {
      const response = await api.post<TResponse>(basePath, data);
      return response.data;
    },
    async update(id, data) {
      const response = await api.put<TResponse>(`${itemBase}/${id}`, data);
      return response.data;
    },
    async remove(id) {
      await api.delete(`${itemBase}/${id}`);
    },
  };
}
