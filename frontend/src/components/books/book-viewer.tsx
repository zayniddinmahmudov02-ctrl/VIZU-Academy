"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Download, Lock, X } from "lucide-react";

import { API_URL } from "@/constants/api";
import { getToken } from "@/src/lib/token";
import { refreshAccessToken } from "@/services/api";

interface Props {
  bookId: string;
  title: string;
  onClose: () => void;
}

type ViewerState = "loading" | "ready" | "premium_required" | "error";

async function fetchBookFile(bookId: string, token: string | null): Promise<Response> {
  return fetch(`${API_URL}/api/v1/books/${bookId}/file`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
}

/** Opens a book's PDF in-browser. Fetches the protected file as a Blob
 * with the current Authorization header (same manual-fetch-with-token
 * shape used for bulk vocabulary analysis) rather than a bare
 * `<iframe src="/books/{id}/file">` — a raw src can't carry a Bearer
 * token, and unlike video this isn't a native media element that
 * strictly needs one, so no new signed-token machinery is needed. The
 * real gate is always the backend re-checking Premium status on this
 * exact request — a stale/optimistic frontend state can never actually
 * obtain the file; a 403 here is shown as "Premium required", not a
 * generic error. */
export default function BookViewer({ bookId, title, onClose }: Props) {
  const [state, setState] = useState<ViewerState>("loading");
  const [blobUrl, setBlobUrl] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let objectUrl: string | null = null;

    async function load() {
      setState("loading");
      try {
        let response = await fetchBookFile(bookId, getToken());
        if (response.status === 401) {
          const newToken = await refreshAccessToken();
          if (newToken) {
            response = await fetchBookFile(bookId, newToken);
          }
        }

        if (cancelled) return;

        if (response.status === 403) {
          setState("premium_required");
          return;
        }
        if (!response.ok) {
          setState("error");
          return;
        }

        const blob = await response.blob();
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setBlobUrl(objectUrl);
        setState("ready");
      } catch {
        if (!cancelled) setState("error");
      }
    }

    load();

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [bookId]);

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-black/80 backdrop-blur-sm">
      <div className="flex items-center justify-between bg-surface-card px-4 py-3 shadow-md">
        <p className="truncate text-sm font-semibold text-text-primary">{title}</p>
        <div className="flex items-center gap-2">
          {state === "ready" && blobUrl && (
            <a
              href={blobUrl}
              download={`${title}.pdf`}
              className="inline-flex items-center gap-1.5 rounded-button bg-accent-blue px-3 py-1.5 text-xs font-semibold text-white transition hover:opacity-90"
            >
              <Download size={14} />
              Herunterladen
            </a>
          )}
          <button
            type="button"
            onClick={onClose}
            aria-label="Schließen"
            className="flex h-8 w-8 items-center justify-center rounded-full text-text-secondary hover:bg-surface-hover"
          >
            <X size={18} />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-hidden bg-surface-hover">
        {state === "loading" && (
          <div className="flex h-full items-center justify-center text-sm text-text-secondary">Wird geladen...</div>
        )}

        {state === "premium_required" && (
          <div className="flex h-full flex-col items-center justify-center gap-3 px-6 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-warning/15 text-warning">
              <Lock size={22} />
            </div>
            <p className="text-lg font-semibold text-text-primary">Premium erforderlich</p>
            <p className="max-w-sm text-sm text-text-secondary">
              Dieses Buch ist nur für Premium-Studenten verfügbar.
            </p>
            <Link
              href="/vizu-pay"
              className="mt-2 rounded-xl bg-accent-blue px-5 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90"
            >
              Premium freischalten
            </Link>
          </div>
        )}

        {state === "error" && (
          <div className="flex h-full items-center justify-center text-sm text-text-secondary">
            Das Buch konnte nicht geladen werden.
          </div>
        )}

        {state === "ready" && blobUrl && (
          <iframe src={blobUrl} title={title} className="h-full w-full border-0" />
        )}
      </div>
    </div>
  );
}
