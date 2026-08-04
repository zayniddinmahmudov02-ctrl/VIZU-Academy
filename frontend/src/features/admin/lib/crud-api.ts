import { api } from "@/src/services/api";
import { ensureArray } from "@/lib/ensure-array";

export interface CrudApi<TResponse, TCreate, TUpdate> {
  list: (params?: Record<string, string>) => Promise<TResponse[]>;
  create: (data: TCreate) => Promise<TResponse>;
  update: (id: string, data: TUpdate) => Promise<TResponse>;
  remove: (id: string) => Promise<void>;
}

export type WriteOnlyCrudApi<TResponse, TCreate, TUpdate> = Omit<
  CrudApi<TResponse, TCreate, TUpdate>,
  "list"
>;

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
      return ensureArray<TResponse>(response.data);
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

/** Same create/update/remove shape as `createCrudApi`, but deliberately
 * omits `.list` — for resources with no bare "list all" backend route
 * (e.g. content blocks that are 1:1 with a parent and only fetchable via
 * a scoped `GET .../{parentId}/...` endpoint). Calling `.list()` on a
 * plain `createCrudApi` for one of these would 404; leaving it off the
 * returned object entirely means that mistake fails at compile time
 * instead of at request time. */
export function createWriteOnlyCrudApi<TResponse, TCreate, TUpdate>(
  basePath: string,
): WriteOnlyCrudApi<TResponse, TCreate, TUpdate> {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { list: _list, ...writeOnly } = createCrudApi<TResponse, TCreate, TUpdate>(basePath);
  return writeOnly;
}
