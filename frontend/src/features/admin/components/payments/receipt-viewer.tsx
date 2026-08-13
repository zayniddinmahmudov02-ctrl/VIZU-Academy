"use client";

import { useEffect, useState } from "react";
import { Download, FileText, Loader2 } from "lucide-react";

import FormDialog from "@/components/admin/form-dialog";
import { api } from "@/src/services/api";
import type { AdminOrderItem } from "@/features/admin/types/vizu-pay.types";

interface Props {
  order: AdminOrderItem | null;
  onClose: () => void;
}

/** Fetches the receipt through the authenticated endpoint (never a public
 * URL — see backend VizuPayService.get_order_proof) and shows an inline
 * preview for images, or a download/open action for PDFs. One blob
 * fetch per open, revoked on close so it never lingers in memory. */
export default function ReceiptViewer({ order, onClose }: Props) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [contentType, setContentType] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!order?.proof_download_url) return;

    let isMounted = true;
    let url: string | null = null;
    setLoading(true);
    setError(false);

    api
      .get(order.proof_download_url, { responseType: "blob" })
      .then((response) => {
        if (!isMounted) return;
        url = URL.createObjectURL(response.data);
        setBlobUrl(url);
        setContentType(response.headers["content-type"] ?? response.data.type ?? null);
      })
      .catch(() => {
        if (isMounted) setError(true);
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
      if (url) URL.revokeObjectURL(url);
      setBlobUrl(null);
      setContentType(null);
    };
  }, [order?.proof_download_url]);

  const isImage = contentType?.startsWith("image/");
  const isPdf = contentType === "application/pdf";
  const buyerName = order ? [order.user_first_name, order.user_last_name].filter(Boolean).join(" ") || order.user_username : "";

  return (
    <FormDialog open={!!order} onOpenChange={(open) => !open && onClose()} title={`Beleg — ${buyerName}`} size="lg">
      <div className="flex min-h-[16rem] items-center justify-center">
        {loading && <Loader2 size={24} className="animate-spin text-[var(--admin-text-muted)]" />}

        {!loading && error && (
          <p className="text-sm text-[var(--admin-danger)]">Beleg konnte nicht geladen werden.</p>
        )}

        {!loading && !error && blobUrl && isImage && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={blobUrl} alt="Zahlungsbeleg" className="max-h-[70vh] w-full rounded-xl object-contain" />
        )}

        {!loading && !error && blobUrl && isPdf && (
          <div className="flex flex-col items-center gap-4 py-10">
            <FileText size={40} className="text-[var(--admin-text-muted)]" />
            <p className="text-sm text-[var(--admin-text-secondary)]">PDF-Beleg</p>
            <div className="flex gap-2">
              <a
                href={blobUrl}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1.5 rounded-lg bg-[var(--admin-primary)] px-3.5 py-2 text-xs font-semibold text-white hover:brightness-110"
              >
                <FileText size={13} />
                In neuem Tab öffnen
              </a>
              <a
                href={blobUrl}
                download={`receipt-${order?.id}.pdf`}
                className="flex items-center gap-1.5 rounded-lg ring-1 ring-[var(--admin-border-strong)] px-3.5 py-2 text-xs font-semibold text-[var(--admin-text-secondary)] hover:bg-[var(--admin-hover)]"
              >
                <Download size={13} />
                Herunterladen
              </a>
            </div>
          </div>
        )}

        {!loading && !error && blobUrl && !isImage && !isPdf && (
          <a
            href={blobUrl}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 rounded-lg bg-[var(--admin-primary)] px-3.5 py-2 text-xs font-semibold text-white hover:brightness-110"
          >
            Datei öffnen
          </a>
        )}
      </div>
    </FormDialog>
  );
}
