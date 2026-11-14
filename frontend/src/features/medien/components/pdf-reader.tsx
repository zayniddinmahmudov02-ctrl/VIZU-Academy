"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { ChevronLeft, ChevronRight, Loader2, Lock, Maximize2, Minimize2, X, ZoomIn, ZoomOut } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

import { errorCode, mediaUrl, openBook, saveProgress } from "../services/medien-service";

const ZOOMS = [0.5, 0.75, 1, 1.25, 1.5, 2, 3];

interface Props {
  bookId: string;
  title: string;
  onClose: () => void;
}

type PdfDoc = import("pdfjs-dist").PDFDocumentProxy;

/** In-app PDF reader (pdf.js): one page at a time on a canvas, previous / next, page number input, zoom, fullscreen and
 * keyboard (← → + − F). The file comes from a short-lived signed URL issued after the access check; the last page is saved
 * to the server (debounced and on close) and the reader reopens on it. Pages render lazily — the whole book is never decoded. */
export default function PdfReader({ bookId, title, onClose }: Props) {
  const { t } = useTranslation();
  const wrapRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const docRef = useRef<PdfDoc | null>(null);
  const renderRef = useRef<{ cancel: () => void } | null>(null);
  const saveTimer = useRef<number | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "locked" | "error">("loading");
  const [pages, setPages] = useState(0);
  const [page, setPage] = useState(1);
  const [zoom, setZoom] = useState(1);
  const [fit, setFit] = useState(true);
  const [rendering, setRendering] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [draft, setDraft] = useState<string | null>(null); // text being typed in the page box; null = show the current page
  const pageRef = useRef(1);
  pageRef.current = page;

  const persist = useCallback((p: number, total: number) => {
    if (saveTimer.current) window.clearTimeout(saveTimer.current);
    saveTimer.current = null;
    void saveProgress("BOOK", bookId, p, total).catch(() => undefined);
  }, [bookId]);

  // open: signed URL -> pdf.js document -> resume page
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const info = await openBook(bookId);
        const pdfjs = await import("pdfjs-dist");
        pdfjs.GlobalWorkerOptions.workerSrc = new URL("pdfjs-dist/build/pdf.worker.min.mjs", import.meta.url).toString();
        const doc = await pdfjs.getDocument({ url: mediaUrl(info.url), withCredentials: false }).promise;
        if (cancelled) { void doc.destroy(); return; }
        docRef.current = doc;
        const start = Math.min(Math.max(1, info.progress?.position ?? 1), doc.numPages);
        setPages(doc.numPages);
        setPage(start);
        setState("ready");
      } catch (err) {
        if (!cancelled) setState(errorCode(err) === "PURCHASE_REQUIRED" ? "locked" : "error");
      }
    })();
    return () => {
      cancelled = true;
      renderRef.current?.cancel();
      void docRef.current?.destroy();
      docRef.current = null;
    };
  }, [bookId]);

  // render the current page (cancel an unfinished render first)
  useEffect(() => {
    const doc = docRef.current;
    const canvas = canvasRef.current;
    if (state !== "ready" || !doc || !canvas) return;
    let cancelled = false;
    setRendering(true);
    (async () => {
      try {
        const pdfPage = await doc.getPage(page);
        if (cancelled) return;
        const base = pdfPage.getViewport({ scale: 1 });
        const available = Math.max(240, (wrapRef.current?.clientWidth ?? 800) - 24);
        const scale = fit ? Math.min(available / base.width, 2.2) * zoom : zoom * 1.3;
        const ratio = Math.min(window.devicePixelRatio || 1, 2);
        const viewport = pdfPage.getViewport({ scale: scale * ratio });
        canvas.width = Math.floor(viewport.width);
        canvas.height = Math.floor(viewport.height);
        canvas.style.width = `${Math.floor(viewport.width / ratio)}px`;
        canvas.style.height = `${Math.floor(viewport.height / ratio)}px`;
        const task = pdfPage.render({ canvas, canvasContext: canvas.getContext("2d")!, viewport });
        renderRef.current = task;
        await task.promise;
      } catch {
        /* a cancelled render (page changed quickly) is expected */
      } finally {
        if (!cancelled) setRendering(false);
      }
    })();
    return () => { cancelled = true; renderRef.current?.cancel(); };
  }, [state, page, zoom, fit]);

  // save the last page (debounced) whenever it changes
  useEffect(() => {
    if (state !== "ready" || !pages) return;
    if (saveTimer.current) window.clearTimeout(saveTimer.current);
    saveTimer.current = window.setTimeout(() => persist(page, pages), 1200);
    return () => { if (saveTimer.current) window.clearTimeout(saveTimer.current); };
  }, [page, pages, state, persist]);

  const go = useCallback((p: number) => setPage((cur) => Math.min(Math.max(1, Number.isFinite(p) ? Math.round(p) : cur), Math.max(1, pages))), [pages]);
  const close = () => {
    if (state === "ready" && pages) persist(pageRef.current, pages);
    if (document.fullscreenElement) void document.exitFullscreen();
    onClose();
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement)?.tagName === "INPUT") return;
      if (e.key === "ArrowRight" || e.key === "PageDown") go(pageRef.current + 1);
      else if (e.key === "ArrowLeft" || e.key === "PageUp") go(pageRef.current - 1);
      else if (e.key === "+" || e.key === "=") setZoom((z) => ZOOMS.find((x) => x > z) ?? z);
      else if (e.key === "-") setZoom((z) => [...ZOOMS].reverse().find((x) => x < z) ?? z);
      else if (e.key === "f" || e.key === "F") toggleFullscreen();
      else if (e.key === "Escape" && !document.fullscreenElement) close();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  useEffect(() => {
    const onChange = () => setFullscreen(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", onChange);
    return () => document.removeEventListener("fullscreenchange", onChange);
  }, []);

  function toggleFullscreen() {
    if (document.fullscreenElement) void document.exitFullscreen();
    else void wrapRef.current?.parentElement?.requestFullscreen?.();
  }

  const btn = "flex h-9 w-9 items-center justify-center rounded-lg text-text-secondary transition hover:bg-surface-hover disabled:opacity-40";

  // portal to <body>: the dashboard page section is its own stacking context, under the sidebar and the floating header
  return createPortal(
    <div className="fixed inset-0 z-[70] flex flex-col bg-black/85 backdrop-blur-sm" role="dialog" aria-modal="true" aria-label={title} data-testid="pdf-reader">
      <div className="flex flex-wrap items-center gap-2 bg-surface-card px-3 py-2 shadow-md">
        <p className="min-w-0 flex-1 truncate text-sm font-semibold text-text-primary">{title}</p>
        <div className="flex items-center gap-1">
          <button className={btn} aria-label={t("medien.readerPrev")} disabled={page <= 1} onClick={() => go(page - 1)} data-testid="reader-prev"><ChevronLeft size={18} /></button>
          <input value={draft ?? String(page)} onChange={(e) => setDraft(e.target.value.replace(/\D/g, ""))} onBlur={() => { go(Number(draft) || page); setDraft(null); }} onKeyDown={(e) => { if (e.key === "Enter") { go(Number(draft) || page); setDraft(null); } }}
                 aria-label={t("medien.readerPage")} inputMode="numeric" data-testid="reader-page"
                 className="h-9 w-14 rounded-lg bg-surface-hover text-center text-sm tabular-nums text-text-primary outline-none ring-1 ring-surface-border" />
          <span className="text-sm text-text-secondary" data-testid="reader-total">/ {pages || "–"}</span>
          <button className={btn} aria-label={t("medien.readerNext")} disabled={!pages || page >= pages} onClick={() => go(page + 1)} data-testid="reader-next"><ChevronRight size={18} /></button>
        </div>
        <div className="flex items-center gap-1">
          <button className={btn} aria-label={t("medien.readerZoomOut")} onClick={() => setZoom((z) => [...ZOOMS].reverse().find((x) => x < z) ?? z)} data-testid="reader-zoom-out"><ZoomOut size={18} /></button>
          <button className="h-9 min-w-[3.5rem] rounded-lg px-2 text-xs font-semibold tabular-nums text-text-secondary hover:bg-surface-hover" onClick={() => { setFit(true); setZoom(1); }} data-testid="reader-zoom">{Math.round(zoom * 100)}%</button>
          <button className={btn} aria-label={t("medien.readerZoomIn")} onClick={() => { setFit(fit); setZoom((z) => ZOOMS.find((x) => x > z) ?? z); }} data-testid="reader-zoom-in"><ZoomIn size={18} /></button>
          <button className={btn} aria-label={t("medien.readerFullscreen")} onClick={toggleFullscreen} data-testid="reader-fullscreen">{fullscreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}</button>
          <button className={btn} aria-label={t("medien.close")} onClick={close} data-testid="reader-close"><X size={18} /></button>
        </div>
      </div>

      <div ref={wrapRef} className="relative flex-1 overflow-auto bg-stone-800 p-3 text-center">
        {state === "loading" && <div className="flex h-full items-center justify-center text-sm text-white/80"><Loader2 className="mr-2 animate-spin" size={18} /> {t("medien.loading")}</div>}
        {state === "locked" && (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-white" data-testid="reader-locked">
            <Lock size={26} /><p className="text-lg font-semibold">{t("medien.err.PURCHASE_REQUIRED")}</p>
          </div>
        )}
        {state === "error" && <div className="flex h-full items-center justify-center text-white" role="alert">{t("medien.err.GENERIC")}</div>}
        {state === "ready" && (
          <div className="inline-block bg-white shadow-2xl" style={{ opacity: rendering ? 0.7 : 1 }}>
            <canvas ref={canvasRef} data-testid="reader-canvas" />
          </div>
        )}
      </div>
    </div>,
    document.body,
  );
}
