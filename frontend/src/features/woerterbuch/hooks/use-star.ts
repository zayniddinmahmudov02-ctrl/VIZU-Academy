"use client";

import { useCallback, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { useTranslation } from "@/lib/i18n/use-translation";
import { setWordSaved } from "../woerterbuch-service";
import { announce } from "../components/status-toast";

/** Returns `data` with `saved` set on every object whose id is `id` — search
 *  pages, word cards, the Random 5 set and the saved list all hold the same
 *  word, so one star click updates them all. */
function withSaved<T>(data: T, id: string, saved: boolean): T {
  if (Array.isArray(data)) return data.map((d) => withSaved(d, id, saved)) as T;
  if (data && typeof data === "object") {
    const next: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(data)) next[k] = withSaved(v, id, saved);
    if ((data as { id?: unknown }).id === id && "saved" in data) next.saved = saved;
    return next as T;
  }
  return data;
}

/** The star: saves / removes a word on the server, then syncs every cached view. */
export function useStar() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const [pending, setPending] = useState<string | null>(null);

  const toggle = useCallback(
    async (id: string, saved: boolean) => {
      setPending(id);
      try {
        const res = await setWordSaved(id, !saved);
        qc.setQueriesData({ queryKey: ["dictionary"] }, (data: unknown) => withSaved(data, id, res.saved));
        await qc.invalidateQueries({ queryKey: ["dictionary", "saved"] });
        announce(t(res.saved ? "woerterbuch.starAdded" : "woerterbuch.starRemoved"));
      } catch {
        announce(t("woerterbuch.actionError"), true);
      } finally {
        setPending(null);
      }
    },
    [qc, t],
  );

  return { toggle, pending };
}
