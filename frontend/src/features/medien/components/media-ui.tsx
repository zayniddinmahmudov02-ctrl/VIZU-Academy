"use client";

/* eslint-disable @next/next/no-img-element -- covers come from the API with long cache headers; next/image would proxy them again */

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpen, Check, Clapperboard, Loader2, Lock, Music, ShoppingCart } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import { errorCode, getMyPurchases, mediaUrl, requestPurchase } from "../services/medien-service";
import type { MediaCard, MediaKind } from "../types";

const ICON = { BOOK: BookOpen, SONG: Music, FILM: Clapperboard } as const;
const TONE: Record<MediaKind, string> = {
  BOOK: "from-amber-700 via-amber-800 to-stone-900",
  SONG: "from-fuchsia-700 via-violet-800 to-indigo-950",
  FILM: "from-sky-700 via-blue-900 to-slate-950",
};

/** Cover / poster: lazy loaded, decoded off the main thread, a branded gradient while loading or when there is none. */
export function Cover({ src, kind, alt = "", className, eager = false }: { src: string | null | undefined; kind: MediaKind; alt?: string; className?: string; eager?: boolean }) {
  const Icon = ICON[kind];
  const [failed, setFailed] = useState(false);
  return (
    <div className={cn("relative overflow-hidden bg-gradient-to-br", TONE[kind], className)}>
      {(!src || failed) && <Icon className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-white/40" size={34} aria-hidden />}
      {src && !failed && <img src={mediaUrl(src)} alt={alt} loading={eager ? "eager" : "lazy"} decoding="async" onError={() => setFailed(true)} className="absolute inset-0 h-full w-full object-cover" />}
    </div>
  );
}

export function formatPrice(n: number | null | undefined, currency = "UZS"): string {
  if (n == null) return "";
  return `${new Intl.NumberFormat("de-DE").format(n)} ${currency === "UZS" ? "so'm" : currency}`;
}

/** FREE badge, or the price (old price struck through and the discount when there is one). */
export function PriceTag({ item, className }: { item: Pick<MediaCard, "access_type" | "price" | "old_price" | "discount_percent" | "currency">; className?: string }) {
  const { t } = useTranslation();
  if (item.access_type === "FREE") {
    return <span className={cn("inline-flex rounded-full bg-success/15 px-2 py-0.5 text-[11px] font-bold text-success", className)} data-testid="tag-free">{t("medien.free")}</span>;
  }
  return (
    <span className={cn("inline-flex flex-wrap items-baseline gap-x-1.5", className)} data-testid="tag-price">
      <span className="text-sm font-extrabold text-text-primary">{formatPrice(item.price, item.currency)}</span>
      {item.old_price && <span className="text-xs text-text-muted line-through">{formatPrice(item.old_price, item.currency)}</span>}
      {item.discount_percent && <span className="rounded bg-danger/10 px-1 text-[10px] font-bold text-danger">-{item.discount_percent}%</span>}
    </span>
  );
}

export function StatusBadge({ item }: { item: Pick<MediaCard, "access_type" | "locked"> }) {
  const { t } = useTranslation();
  if (item.access_type === "FREE") return <span className="rounded-full bg-success px-2 py-0.5 text-[10px] font-bold uppercase text-white shadow">{t("medien.free")}</span>;
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase shadow", item.locked ? "bg-black/70 text-white" : "bg-success text-white")}>
      {item.locked ? <Lock size={10} /> : <Check size={10} />}{t("medien.paid")}
    </span>
  );
}

/** Buy button of a locked item: sends a purchase request (no money is handled here — an admin grants the access after the
 * payment arrived), then shows the request status. */
export function PurchaseButton({ item, className, size = "md" }: { item: Pick<MediaCard, "id" | "kind" | "locked" | "price">; className?: string; size?: "sm" | "md" }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const purchases = useQuery({ queryKey: ["medien-purchases"], queryFn: getMyPurchases, enabled: item.locked, staleTime: 30_000 });
  const open = purchases.data?.find((p) => p.content_id === item.id && (p.status === "REQUESTED" || p.status === "GRANTED"));
  const mutation = useMutation({
    mutationFn: () => requestPurchase(item.kind, item.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["medien-purchases"] }),
  });
  if (!item.locked) return null;
  const requested = !!open || mutation.isSuccess;
  return (
    <div className={className}>
      <button type="button" disabled={requested || mutation.isPending} onClick={() => mutation.mutate()} data-testid="purchase-button"
              className={cn("inline-flex items-center justify-center gap-2 rounded-xl bg-accent-blue font-semibold text-white transition hover:opacity-90 disabled:opacity-60", size === "sm" ? "px-3 py-1.5 text-xs" : "px-5 py-2.5 text-sm")}>
        {mutation.isPending ? <Loader2 size={14} className="animate-spin" /> : requested ? <Check size={14} /> : <ShoppingCart size={14} />}
        {requested ? t("medien.purchaseRequested") : t("medien.buy")}
      </button>
      {requested && <p className="mt-1.5 text-xs text-text-secondary" data-testid="purchase-info">{t("medien.purchaseInfo")}</p>}
      {mutation.isError && <p role="alert" className="mt-1.5 text-xs text-danger">{errorCode(mutation.error) === "NOT_PAID" ? t("medien.err.NOT_PAID") : t("medien.err.GENERIC")}</p>}
    </div>
  );
}

export function useDebounced<T>(value: T, ms = 350): T {
  const [v, setV] = useState(value);
  useEffect(() => {
    const id = window.setTimeout(() => setV(value), ms);
    return () => window.clearTimeout(id);
  }, [value, ms]);
  return v;
}

export function EmptyState({ text }: { text: string }) {
  return <p className="rounded-card bg-surface-card p-8 text-center text-sm text-text-secondary ring-1 ring-surface-border" data-testid="medien-empty">{text}</p>;
}

export function SectionTitle({ children, action }: { children: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div className="mb-3 flex items-end justify-between gap-3">
      <h2 className="text-lg font-bold text-text-primary sm:text-xl">{children}</h2>
      {action}
    </div>
  );
}

export function Pager({ page, pageSize, total, onChange }: { page: number; pageSize: number; total: number; onChange: (p: number) => void }) {
  const { t } = useTranslation();
  const pages = Math.max(1, Math.ceil(total / pageSize));
  if (pages <= 1) return null;
  return (
    <div className="mt-5 flex items-center justify-center gap-3 text-sm" data-testid="pager">
      <button className="rounded-lg px-3 py-1.5 font-semibold ring-1 ring-surface-border hover:bg-surface-hover disabled:opacity-40" disabled={page <= 1} onClick={() => onChange(page - 1)}>{t("medien.prev")}</button>
      <span className="text-text-secondary">{page} / {pages}</span>
      <button className="rounded-lg px-3 py-1.5 font-semibold ring-1 ring-surface-border hover:bg-surface-hover disabled:opacity-40" disabled={page >= pages} onClick={() => onChange(page + 1)}>{t("medien.next")}</button>
    </div>
  );
}
