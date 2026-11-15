"use client";

import { useState } from "react";
import { Download, Loader2 } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

import { errorCode, getBookDownloadLink, mediaUrl } from "../services/medien-service";

interface Props {
  bookId: string;
  /** icon only (reader toolbar) instead of icon + label */
  compact?: boolean;
  className?: string;
  /** called with the translated message of a failed download; without it the message is shown under the button */
  onError?: (message: string) => void;
}

/** "PDF herunterladen / PDF yuklab olish". Asks the server for a short-lived download link of the ORIGINAL file (403 unless the whole book is open
 * to the student: free, bought, staff) and starts the download with it. The link is never shown or stored; the file name comes from the book title. */
export default function DownloadPdfButton({ bookId, compact = false, className, onError }: Props) {
  const { t } = useTranslation();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function download() {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const { url, filename } = await getBookDownloadLink(bookId);
      const link = document.createElement("a");
      link.href = mediaUrl(url);
      link.download = filename;
      link.rel = "noopener";
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      const code = errorCode(err);
      const key = code && ["PURCHASE_REQUIRED", "FILE_MISSING", "NOT_FOUND"].includes(code) ? `medien.err.${code}` : "medien.err.GENERIC";
      const message = t(key);
      if (onError) onError(message);
      else setError(message);
    } finally {
      setBusy(false);
    }
  }

  const base = compact
    ? "flex h-9 w-9 items-center justify-center rounded-lg text-text-secondary transition hover:bg-surface-hover disabled:opacity-40"
    : "inline-flex items-center gap-2 rounded-xl bg-surface-hover px-5 py-2.5 text-sm font-semibold text-text-primary ring-1 ring-surface-border transition hover:opacity-90 disabled:opacity-50";

  return (
    <span className="inline-flex flex-col items-start gap-1">
      <button type="button" onClick={() => void download()} disabled={busy} aria-label={t("medien.downloadPdf")} title={t("medien.downloadPdf")}
              data-testid="book-download" className={`${base} ${className ?? ""}`}>
        {busy ? <Loader2 size={18} className="animate-spin" /> : <Download size={18} />}
        {!compact && <span>{t("medien.downloadPdf")}</span>}
      </button>
      {error && <span className="text-xs text-danger" role="alert" data-testid="book-download-error">{error}</span>}
    </span>
  );
}
