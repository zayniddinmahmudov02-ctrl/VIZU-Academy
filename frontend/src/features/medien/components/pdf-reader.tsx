"use client";

import { memo, useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useRouter } from "next/navigation";
import { ArrowLeft, BookOpen, ChevronLeft, ChevronRight, Hand, Loader2, Lock, Maximize2, Minimize2, ScrollText, X, ZoomIn, ZoomOut } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

import { errorCode, mediaUrl, openBook, saveProgress, saveProgressKeepalive } from "../services/medien-service";
import BookView, { type BookViewHandle } from "./book-view";
import DownloadPdfButton from "./download-pdf-button";

type PdfDoc = import("pdfjs-dist").PDFDocumentProxy;
type RenderTask = import("pdfjs-dist").RenderTask;
/** book = one page at a time, turned like a book (swipe / click / keys, pinch zoom); scroll = all pages in one long column */
type Mode = "scroll" | "book";

const ZOOMS = [0.5, 0.75, 1, 1.25, 1.5, 2, 3];
const MODE_KEY = "vizu.reader.mode";
const HINT_KEY = "vizu.reader.gestureHint";
/** padding of the reading area and gap between two pages (px) */
const PAD = 12;
/** widest "fit width" page on a big screen (px); zoom multiplies it */
const MAX_FIT = 960;
/** the reading line: the page under 35% of the viewport height is "the current page" and the place that is saved / restored */
const ANCHOR = 0.35;
/** pixels of one rendered canvas are capped (a zoomed page on a retina screen would need hundreds of MB) */
const MAX_CANVAS_PIXELS = 12_000_000;
const DEFAULT_RATIO = 0.707; // A4 until a page is measured

interface Props {
  bookId: string;
  title: string;
  onClose: () => void;
  /** the student reads a preview and wants the whole book (opens the payment form); without it the paywall only offers "back" */
  onBuy?: () => void;
  /** where "close the book" leads (the Bibliothek) */
  exitHref?: string;
}

interface Meta { preview: boolean; total: number; previewPages: number; canDownload: boolean }

const clamp01 = (n: number) => Math.min(1, Math.max(0, n));

/** last n in 1..count for which `ok(n)` holds, where ok is true for a prefix of the pages (binary search); 0 when none */
function lastWhere(count: number, ok: (n: number) => boolean): number {
  let lo = 0;
  let hi = count;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (ok(mid)) lo = mid;
    else hi = mid - 1;
  }
  return lo;
}

/** adds the page ratios that differ from what the layout would use anyway (so a book of equal pages never re-lays-out) */
function mergeRatios(prev: Record<number, number>, found: Record<number, number>): Record<number, number> {
  let next: Record<number, number> | null = null;
  for (const [key, value] of Object.entries(found)) {
    const n = Number(key);
    const current = prev[n] ?? (n === 1 ? DEFAULT_RATIO : (prev[1] ?? DEFAULT_RATIO));
    if (Math.abs(current - value) / current > 0.005) (next ??= { ...prev })[n] = value;
  }
  return next ?? prev;
}

interface PageViewProps {
  doc: PdfDoc;
  n: number;
  width: number;
  ratio: number;
  /** near the viewport: draw it; far away: free the canvas */
  active: boolean;
  onMeasured: (n: number, ratio: number) => void;
  setEl: (n: number, el: HTMLDivElement | null) => void;
}

/** One page of the scroll mode: a white box of the exact size (so the scroll height is right before anything is drawn) and a canvas drawn lazily by pdf.js. */
const PageView = memo(function PageView({ doc, n, width, ratio, active, onMeasured, setEl }: PageViewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const spinRef = useRef<HTMLDivElement>(null);
  const busy = useRef<Promise<unknown>>(Promise.resolve());

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    if (!active) {
      canvas.width = 0; // frees the pixel buffer of a page that scrolled far away
      canvas.height = 0;
      return;
    }
    if (spinRef.current) spinRef.current.hidden = false;
    let cancelled = false;
    let task: RenderTask | null = null;
    (async () => {
      try {
        const page = await doc.getPage(n);
        if (cancelled) return;
        const base = page.getViewport({ scale: 1 });
        onMeasured(n, base.width / base.height);
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        let scale = (width / base.width) * dpr;
        const pixels = base.width * scale * base.height * scale;
        if (pixels > MAX_CANVAS_PIXELS) scale *= Math.sqrt(MAX_CANVAS_PIXELS / pixels);
        const viewport = page.getViewport({ scale });
        await busy.current; // a cancelled render must have let go of the canvas
        if (cancelled) return;
        canvas.width = Math.floor(viewport.width);
        canvas.height = Math.floor(viewport.height);
        task = page.render({ canvas, canvasContext: canvas.getContext("2d")!, viewport });
        busy.current = task.promise.catch(() => undefined);
        await task.promise;
        if (!cancelled && spinRef.current) spinRef.current.hidden = true;
        page.cleanup();
      } catch {
        /* a cancelled render (scrolled away, zoomed) is expected */
      }
    })();
    return () => {
      cancelled = true;
      task?.cancel();
    };
  }, [doc, n, width, active, onMeasured]);

  return (
    <div ref={(el) => setEl(n, el)} data-page={n} data-testid="reader-page-view" className="relative mx-auto bg-white shadow-xl" style={{ width, aspectRatio: String(ratio), marginBottom: PAD }}>
      <canvas ref={canvasRef} data-testid="reader-canvas" className="absolute inset-0 h-full w-full" />
      <div ref={spinRef} className="absolute inset-0 flex items-center justify-center text-stone-400" aria-hidden="true"><Loader2 className="animate-spin" size={22} /></div>
    </div>
  );
});

/** In-app PDF reader (pdf.js).
 * - Book mode (default on every device): one page at a time, fitted to the screen, turned like a book — swipe right-to-left / left-to-right on
 *   phones (the page follows the finger and turns over the spine), the buttons, ← → (also PageUp / PageDown) and a click on the left / right
 *   third of the page on computers. Two fingers zoom (pinch) and move the zoomed page; a pinch is never taken as a swipe. Double tap / the
 *   percent button: whole page again. The original page order of the PDF is kept.
 * - Scroll mode (switch in the toolbar): all pages in one column, drawn only near the viewport; zoom 50–300 % of the fitted width.
 *   The choice is remembered per device.
 * - Toolbar: a clear "close the book" button (back to the Bibliothek), page box + total, previous / next, progress, zoom, fullscreen (a full-
 *   window fallback where the browser has none); on phones a big previous / next bar at the bottom.
 * - Reading position: the page (and in scroll mode how far down it, 0..1) is saved debounced, on close and when the tab is hidden; the reader
 *   reopens on the same page.
 * - A PAID book that is not owned opens as a PREVIEW: the server hands out a separate PDF with only the free pages. Turning past the last free
 *   page shows the "unlock the full book" dialog; the locked pages do not exist in the delivered file.
 * The file comes from a short-lived signed URL issued after the access check. */
export default function PdfReader({ bookId, title, onClose, onBuy, exitHref = "/medien/bibliothek" }: Props) {
  const { t } = useTranslation();
  const router = useRouter();
  const rootRef = useRef<HTMLDivElement>(null);
  const scrollerRef = useRef<HTMLDivElement>(null);
  const bookRef = useRef<BookViewHandle>(null);
  const docRef = useRef<PdfDoc | null>(null);
  const pageEls = useRef<(HTMLDivElement | null)[]>([]);
  const anchorRef = useRef({ page: 1, frac: 0 });
  const pageRef = useRef(1);
  const metaRef = useRef<Meta | null>(null);
  const saveTimer = useRef<number | null>(null);
  const raf = useRef(0);
  const dirty = useRef(false);
  const atEnd = useRef(false);

  const [status, setStatus] = useState<"loading" | "ready" | "locked" | "error">("loading");
  const [doc, setDoc] = useState<PdfDoc | null>(null);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [pages, setPages] = useState(0);
  const [page, setPage] = useState(1);
  const [mode, setMode] = useState<Mode>("book");
  const [zoom, setZoom] = useState(1);
  const [bookScale, setBookScale] = useState(1);
  const [avail, setAvail] = useState(0);
  const [ratios, setRatios] = useState<Record<number, number>>({});
  const [range, setRange] = useState({ from: 1, to: 3 });
  const [paywall, setPaywall] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [immersive, setImmersive] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [draft, setDraft] = useState<string | null>(null); // text being typed in the page box; null = show the current page
  const [hint, setHint] = useState(false);

  const pageWidth = Math.round(Math.max(160, Math.min(avail - 2 * PAD, MAX_FIT)) * zoom);
  const ratioOf = useCallback((n: number) => ratios[n] ?? ratios[1] ?? DEFAULT_RATIO, [ratios]);

  useEffect(() => {
    pageRef.current = page;
  }, [page]);

  const persist = useCallback((keepalive = false) => {
    if (saveTimer.current) window.clearTimeout(saveTimer.current);
    saveTimer.current = null;
    const info = metaRef.current;
    if (!info) return;
    dirty.current = false;
    const { page: p, frac } = anchorRef.current;
    if (keepalive) saveProgressKeepalive("BOOK", bookId, p, info.total, null, frac);
    else void saveProgress("BOOK", bookId, p, info.total, null, frac).catch(() => undefined);
  }, [bookId]);

  const scheduleSave = useCallback(() => {
    dirty.current = true;
    if (saveTimer.current) window.clearTimeout(saveTimer.current);
    saveTimer.current = window.setTimeout(() => persist(), 1200);
  }, [persist]);

  // open: signed URL -> pdf.js document -> reading position
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const info = await openBook(bookId);
        const pdfjs = await import("pdfjs-dist");
        pdfjs.GlobalWorkerOptions.workerSrc = new URL("pdfjs-dist/build/pdf.worker.min.mjs", import.meta.url).toString();
        const loaded = await pdfjs.getDocument({ url: mediaUrl(info.url), withCredentials: false }).promise;
        if (cancelled) { void loaded.destroy(); return; }
        docRef.current = loaded;
        const first = await loaded.getPage(1);
        const v = first.getViewport({ scale: 1 });
        first.cleanup();
        const start = Math.min(Math.max(1, info.progress?.position ?? 1), loaded.numPages);
        const frac = info.progress && info.progress.position === start ? clamp01(info.progress.scroll ?? 0) : 0;
        anchorRef.current = { page: start, frac };
        pageRef.current = start;
        const next: Meta = { preview: info.mode === "preview", total: info.total_pages ?? loaded.numPages, previewPages: info.preview_pages ?? loaded.numPages, canDownload: info.can_download };
        metaRef.current = next;
        let stored: string | null = null;
        try { stored = window.localStorage.getItem(MODE_KEY); } catch { /* storage may be blocked */ }
        const chosen: Mode = stored === "scroll" ? "scroll" : "book"; // "single" (the old one-page mode) is the book mode now
        setMode(chosen);
        if (chosen === "book" && window.matchMedia("(pointer: coarse)").matches) {
          let seen = false;
          try { seen = window.localStorage.getItem(HINT_KEY) === "1"; window.localStorage.setItem(HINT_KEY, "1"); } catch { /* storage may be blocked */ }
          if (!seen) setHint(true);
        }
        setMeta(next);
        setRatios({ 1: v.width / v.height });
        setPages(loaded.numPages);
        setPage(start);
        setDoc(loaded);
        setStatus("ready");
        // the real size of every page, in the background: a book with a few odd-sized pages still gets the right layout
        for (let from = 2; from <= loaded.numPages && !cancelled; from += 25) {
          const found: Record<number, number> = {};
          await Promise.all(Array.from({ length: Math.min(25, loaded.numPages - from + 1) }, async (_, i) => {
            const p = await loaded.getPage(from + i);
            const vp = p.getViewport({ scale: 1 });
            found[from + i] = vp.width / vp.height;
            p.cleanup();
          }));
          if (!cancelled) setRatios((prev) => mergeRatios(prev, found));
          await new Promise((resolve) => setTimeout(resolve, 0));
        }
      } catch (err) {
        if (!cancelled) setStatus(errorCode(err) === "PURCHASE_REQUIRED" ? "locked" : "error");
      }
    })();
    return () => {
      cancelled = true;
      void docRef.current?.destroy();
      docRef.current = null;
    };
  }, [bookId]);

  // the gesture hint disappears by itself
  useEffect(() => {
    if (!hint) return;
    const timer = window.setTimeout(() => setHint(false), 4000);
    return () => window.clearTimeout(timer);
  }, [hint]);

  // the reading area keeps the document from scrolling behind it
  useEffect(() => {
    const before = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = before; };
  }, []);

  // width of the reading area (scroll mode: pages are as wide as it is, up to MAX_FIT)
  useEffect(() => {
    const el = scrollerRef.current;
    if (!el) return;
    const observer = new ResizeObserver(() => setAvail(el.clientWidth));
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const onMeasured = useCallback((n: number, ratio: number) => setRatios((prev) => mergeRatios(prev, { [n]: ratio })), []);
  const setEl = useCallback((n: number, el: HTMLDivElement | null) => { pageEls.current[n] = el; }, []);

  /** where the reader is now: current page + position inside it (the reading line), and which pages are near enough to draw */
  const measure = useCallback(() => {
    const scroller = scrollerRef.current;
    if (!scroller || !pages) return;
    if (mode === "book") {
      anchorRef.current = { page: pageRef.current, frac: 0 };
      return;
    }
    const els = pageEls.current;
    const top = scroller.scrollTop;
    const h = scroller.clientHeight;
    const line = top + h * ANCHOR;
    const topOf = (n: number) => els[n]?.offsetTop ?? Infinity;
    const current = Math.max(1, lastWhere(pages, (n) => topOf(n) <= line));
    const el = els[current];
    anchorRef.current = { page: current, frac: el ? clamp01((line - el.offsetTop) / Math.max(1, el.offsetHeight)) : 0 };
    pageRef.current = current;
    setPage((p) => (p === current ? p : current));
    const to = Math.max(current, lastWhere(pages, (n) => topOf(n) <= top + h * 2.5));
    const from = Math.min(current, lastWhere(pages, (n) => (els[n] ? els[n].offsetTop + els[n].offsetHeight : Infinity) < top - h * 1.5) + 1);
    setRange((r) => (r.from === from && r.to === to ? r : { from, to }));
  }, [mode, pages]);

  const restoreAnchor = useCallback(() => {
    const scroller = scrollerRef.current;
    const el = scroller ? pageEls.current[anchorRef.current.page] : null;
    if (!scroller || !el) return;
    scroller.scrollTop = Math.max(0, el.offsetTop + anchorRef.current.frac * el.offsetHeight - scroller.clientHeight * ANCHOR);
  }, []);

  // the layout changed (width, zoom, mode, a page of another size): keep the reader on the same spot of the same page
  useLayoutEffect(() => {
    if (status !== "ready" || !avail) return;
    if (mode === "book") { anchorRef.current = { page: pageRef.current, frac: 0 }; return; }
    restoreAnchor();
    measure();
  }, [status, avail, pageWidth, ratios, mode, restoreAnchor, measure]);

  function onScroll() {
    if (mode !== "scroll" || raf.current) return;
    raf.current = window.requestAnimationFrame(() => {
      raf.current = 0;
      measure();
      scheduleSave();
      const scroller = scrollerRef.current;
      if (scroller && metaRef.current?.preview) { // reached the end of the free pages
        const end = scroller.scrollTop + scroller.clientHeight >= scroller.scrollHeight - 48;
        if (end && !atEnd.current) setPaywall(true);
        atEnd.current = end;
      }
    });
  }

  const scrollToPage = useCallback((n: number) => {
    const scroller = scrollerRef.current;
    const el = pageEls.current[n];
    if (!scroller || !el) return;
    scroller.scrollTop = Math.max(0, el.offsetTop - PAD);
    measure();
    scheduleSave();
  }, [measure, scheduleSave]);

  /** book mode: the page the book view turned to (after its animation), or a jump from the page box */
  const showPage = useCallback((n: number) => {
    pageRef.current = n;
    anchorRef.current = { page: n, frac: 0 };
    setPage(n);
    scheduleSave();
  }, [scheduleSave]);

  const go = useCallback((p: number) => {
    if (!Number.isFinite(p) || !pages) return;
    const target = Math.max(1, Math.round(p));
    if (metaRef.current?.preview && target > pages) { setPaywall(true); return; } // page 11+ of a preview: the server never sends it
    const next = Math.min(target, pages);
    if (mode === "scroll") { scrollToPage(next); return; }
    const now = pageRef.current;
    if (next === now) return;
    if (Math.abs(next - now) === 1 && bookRef.current?.turn(next > now ? "next" : "prev")) return; // turned with the animation
    showPage(next);
  }, [pages, mode, scrollToPage, showPage]);

  const zoomBy = useCallback((dir: 1 | -1) => {
    if (mode === "book") { bookRef.current?.zoom(dir); return; }
    setZoom((z) => (dir > 0 ? ZOOMS.find((x) => x > z + 1e-6) : [...ZOOMS].reverse().find((x) => x < z - 1e-6)) ?? z);
  }, [mode]);
  const zoomReset = () => { if (mode === "book") bookRef.current?.resetZoom(); else setZoom(1); };

  function chooseMode(next: Mode) {
    if (next === mode) return;
    try { window.localStorage.setItem(MODE_KEY, next); } catch { /* storage may be blocked */ }
    setPage(anchorRef.current.page);
    pageRef.current = anchorRef.current.page;
    setMode(next);
  }

  function toggleFullscreen() {
    if (document.fullscreenElement) { void document.exitFullscreen(); return; }
    if (immersive) { setImmersive(false); return; }
    const el = rootRef.current;
    if (el?.requestFullscreen) el.requestFullscreen().catch(() => setImmersive(true));
    else setImmersive(true); // iPhone: no element fullscreen — the toolbar shrinks instead
  }

  const close = useCallback(() => {
    if (status === "ready") persist();
    if (document.fullscreenElement) void document.exitFullscreen();
    onClose();
  }, [status, persist, onClose]);

  /** "close the book": the position is saved and the student is back on the Bibliothek shelves */
  const exit = () => {
    close();
    router.push(exitHref);
  };

  const closePaywall = () => {
    setPaywall(false);
    if (mode === "scroll") scrollToPage(pages);
  };

  const buy = () => {
    if (!onBuy) return;
    persist();
    if (document.fullscreenElement) void document.exitFullscreen();
    onBuy();
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (paywall) { if (e.key === "Escape") closePaywall(); return; } // also while the page box has the focus
      if ((e.target as HTMLElement)?.tagName === "INPUT") return;
      if (e.key === "ArrowRight" || (mode === "book" && e.key === "PageDown")) go(pageRef.current + 1);
      else if (e.key === "ArrowLeft" || (mode === "book" && e.key === "PageUp")) go(pageRef.current - 1);
      else if (e.key === "+" || e.key === "=") zoomBy(1);
      else if (e.key === "-") zoomBy(-1);
      else if (e.key === "0") zoomReset();
      else if (e.key === "f" || e.key === "F") toggleFullscreen();
      else if (e.key === "Escape" && !document.fullscreenElement) { if (immersive) setImmersive(false); else close(); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  useEffect(() => {
    const onChange = () => setFullscreen(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", onChange);
    return () => document.removeEventListener("fullscreenchange", onChange);
  }, []);

  // the tab goes to the background / the page is left: the position must not be lost
  useEffect(() => {
    const onHide = () => { if (dirty.current) persist(true); };
    const onVisibility = () => { if (document.visibilityState === "hidden") onHide(); };
    document.addEventListener("visibilitychange", onVisibility);
    window.addEventListener("pagehide", onHide);
    return () => {
      document.removeEventListener("visibilitychange", onVisibility);
      window.removeEventListener("pagehide", onHide);
      if (dirty.current) persist(true);
      if (raf.current) window.cancelAnimationFrame(raf.current);
    };
  }, [persist]);

  const canGo = useCallback((n: number) => n >= 1 && n <= pages, [pages]);
  const onBlocked = useCallback(() => { if (metaRef.current?.preview) setPaywall(true); }, []);

  const btn = "flex h-[44px] w-[44px] items-center justify-center rounded-lg text-text-secondary transition hover:bg-surface-hover disabled:opacity-40 sm:h-9 sm:w-9";
  const shown = fullscreen || immersive;
  const percent = meta?.total ? Math.min(100, Math.round((page / meta.total) * 100)) : 0;
  const shownZoom = mode === "book" ? bookScale : zoom;
  const atLast = !pages || (!meta?.preview && page >= pages);
  const list = doc && mode === "scroll" ? Array.from({ length: pages }, (_, i) => i + 1) : [];

  // portal to <body>: the dashboard page section is its own stacking context, under the sidebar and the floating header
  return createPortal(
    <div ref={rootRef} className="fixed inset-0 z-[70] flex h-dvh flex-col bg-black/85 backdrop-blur-sm" role="dialog" aria-modal="true" aria-label={title} data-testid="pdf-reader" data-mode={mode}>
      <div className="bg-surface-card shadow-md">
        <div className="flex items-center gap-2 px-2 pt-2 sm:px-3">
          <button type="button" onClick={exit} data-testid="reader-exit"
                  className="inline-flex h-[44px] shrink-0 items-center gap-1.5 rounded-xl bg-accent-blue px-3 text-sm font-semibold text-white shadow-sm transition hover:opacity-90">
            <ArrowLeft size={17} /><span className="hidden min-[400px]:inline">{t("medien.readerExit")}</span>
          </button>
          {!immersive && <p className="min-w-0 flex-1 truncate text-sm font-semibold text-text-primary">{title}</p>}
          {immersive && <span className="flex-1" />}
          {meta?.preview && <span className="shrink-0 rounded-full bg-warning/15 px-2.5 py-1 text-xs font-semibold text-warning" data-testid="reader-preview-badge">{t("medien.previewBadge", { n: meta.previewPages })}</span>}
          {meta?.canDownload && <DownloadPdfButton bookId={bookId} compact onError={setNotice} />}
          <button className={btn} aria-label={t("medien.readerFullscreen")} onClick={toggleFullscreen} data-testid="reader-fullscreen">{shown ? <Minimize2 size={18} /> : <Maximize2 size={18} />}</button>
          <button className={btn} aria-label={t("medien.close")} title={t("medien.close")} onClick={close} data-testid="reader-close"><X size={18} /></button>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 px-2 pb-2 sm:px-3">
          <div className="flex items-center gap-1">
            <button className={btn} aria-label={t("medien.readerPrev")} disabled={page <= 1} onClick={() => go(page - 1)} data-testid="reader-prev"><ChevronLeft size={18} /></button>
            <input value={draft ?? String(page)} onChange={(e) => setDraft(e.target.value.replace(/\D/g, ""))} onBlur={() => { go(Number(draft) || page); setDraft(null); }} onKeyDown={(e) => { if (e.key === "Enter") { go(Number(draft) || page); setDraft(null); } }}
                   aria-label={t("medien.readerPage")} inputMode="numeric" data-testid="reader-page"
                   className="h-9 w-14 rounded-lg bg-surface-hover text-center text-sm tabular-nums text-text-primary outline-none ring-1 ring-surface-border" />
            <span className="text-sm text-text-secondary" data-testid="reader-total">/ {meta?.total || "–"}</span>
            <button className={btn} aria-label={t("medien.readerNext")} disabled={atLast} onClick={() => go(page + 1)} data-testid="reader-next"><ChevronRight size={18} /></button>
            <span className="ml-1 hidden text-xs tabular-nums text-text-muted sm:inline" data-testid="reader-percent">{t("medien.readerProgress", { percent })}</span>
          </div>
          <div className="flex items-center gap-1">
            {mode === "book" && <span className="mr-1 hidden text-xs text-text-muted lg:inline">{t("medien.readerKeys")}</span>}
            <button className={btn} aria-label={mode === "scroll" ? t("medien.readerSingle") : t("medien.readerScroll")} title={mode === "scroll" ? t("medien.readerSingle") : t("medien.readerScroll")}
                    onClick={() => chooseMode(mode === "scroll" ? "book" : "scroll")} data-testid="reader-mode">{mode === "scroll" ? <BookOpen size={18} /> : <ScrollText size={18} />}</button>
            <button className={btn} aria-label={t("medien.readerZoomOut")} onClick={() => zoomBy(-1)} data-testid="reader-zoom-out"><ZoomOut size={18} /></button>
            <button className="h-9 min-w-[3.5rem] rounded-lg px-2 text-xs font-semibold tabular-nums text-text-secondary hover:bg-surface-hover" title={mode === "book" ? t("medien.readerZoomReset") : t("medien.readerFit")} onClick={zoomReset} data-testid="reader-zoom">{Math.round(shownZoom * 100)}%</button>
            <button className={btn} aria-label={t("medien.readerZoomIn")} onClick={() => zoomBy(1)} data-testid="reader-zoom-in"><ZoomIn size={18} /></button>
          </div>
        </div>
        <div className="h-1 bg-surface-border" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={percent} data-testid="reader-progress"><div className="h-full bg-accent-blue transition-[width]" style={{ width: `${percent}%` }} /></div>
      </div>
      {notice && <p className="bg-danger/15 px-3 py-1.5 text-center text-xs text-danger" role="alert" data-testid="reader-notice">{notice}</p>}

      <div ref={scrollerRef} onScroll={onScroll} className={mode === "book" ? "relative min-h-0 flex-1 overflow-hidden bg-stone-800" : "relative min-h-0 flex-1 overflow-auto overscroll-contain bg-stone-800"}
           style={{ touchAction: mode === "scroll" ? "pan-x pan-y pinch-zoom" : "none" }} data-testid="reader-scroll">
        {status === "loading" && <div className="flex h-full items-center justify-center text-sm text-white/80" data-testid="reader-loading"><Loader2 className="mr-2 animate-spin" size={18} /> {t("medien.loading")}</div>}
        {status === "locked" && (
          <div className="flex h-full flex-col items-center justify-center gap-3 p-6 text-center text-white" data-testid="reader-locked">
            <Lock size={26} /><p className="text-lg font-semibold">{t("medien.err.PURCHASE_REQUIRED")}</p>
            {onBuy && <button type="button" onClick={buy} className="rounded-xl bg-accent-blue px-5 py-2.5 text-sm font-semibold text-white hover:opacity-90">{t("medien.paywallBuy")}</button>}
          </div>
        )}
        {status === "error" && <div className="flex h-full items-center justify-center p-6 text-center text-white" role="alert">{t("medien.err.GENERIC")}</div>}
        {status === "ready" && doc && mode === "book" && (
          <BookView ref={bookRef} doc={doc} page={page} pages={pages} ratioOf={ratioOf} canGo={canGo} onBlocked={onBlocked} onTurned={showPage} onScale={setBookScale} />
        )}
        {status === "ready" && doc && mode === "scroll" && avail > 0 && (
          <div className="relative" style={{ width: "max-content", minWidth: "100%", padding: PAD, paddingBottom: 0 }}>
            {list.map((n) => (
              <PageView key={n} doc={doc} n={n} width={pageWidth} ratio={ratioOf(n)} active={n >= range.from && n <= range.to} onMeasured={onMeasured} setEl={setEl} />
            ))}
            {meta?.preview && (
              <div className="mx-auto mb-3 flex flex-col items-center gap-2 rounded-xl bg-surface-card p-5 text-center" style={{ width: pageWidth }} data-testid="reader-locked-page">
                <Lock size={22} className="text-warning" />
                <p className="text-sm font-semibold text-text-primary">{t("medien.lockedPage", { page: pages + 1 })}</p>
                {onBuy && <button type="button" onClick={buy} data-testid="reader-buy-inline" className="rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white hover:opacity-90">{t("medien.paywallBuy")}</button>}
              </div>
            )}
          </div>
        )}
        {hint && mode === "book" && status === "ready" && (
          <button type="button" onClick={() => setHint(false)} data-testid="reader-hint"
                  className="absolute inset-x-4 bottom-6 z-10 mx-auto flex max-w-sm items-center justify-center gap-2 rounded-2xl bg-black/75 px-4 py-3 text-sm font-medium text-white shadow-xl">
            <Hand size={18} className="shrink-0" />{t("medien.readerGestures")}
          </button>
        )}
      </div>

      {mode === "book" && status === "ready" && (
        <div className="flex items-center gap-2 bg-surface-card px-3 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-2 sm:hidden" data-testid="reader-bottom-bar">
          <button type="button" className="flex h-[52px] flex-1 items-center justify-center gap-1 rounded-xl bg-surface-hover text-sm font-semibold text-text-primary disabled:opacity-40"
                  disabled={page <= 1} onClick={() => go(page - 1)} data-testid="reader-prev-bottom" aria-label={t("medien.readerPrev")}><ChevronLeft size={20} /></button>
          <span className="min-w-[5.5rem] text-center text-sm font-semibold tabular-nums text-text-secondary" data-testid="reader-position">{page} / {meta?.total || pages}</span>
          <button type="button" className="flex h-[52px] flex-1 items-center justify-center gap-1 rounded-xl bg-accent-blue text-sm font-semibold text-white disabled:opacity-40"
                  disabled={atLast} onClick={() => go(page + 1)} data-testid="reader-next-bottom" aria-label={t("medien.readerNext")}><ChevronRight size={20} /></button>
        </div>
      )}

      {paywall && meta?.preview && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/65 p-4" data-testid="reader-paywall">
          <div className="w-full max-w-md space-y-4 rounded-3xl bg-surface-card p-6 text-center shadow-2xl ring-1 ring-surface-border" role="alertdialog" aria-labelledby="reader-paywall-title">
            <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-warning/15 text-warning"><Lock size={22} /></span>
            <h2 id="reader-paywall-title" className="text-xl font-extrabold text-text-primary">{t("medien.paywallTitle")}</h2>
            <p className="text-sm leading-relaxed text-text-secondary">{t("medien.paywallText", { n: meta.previewPages })}</p>
            <div className="flex flex-col gap-2 sm:flex-row sm:justify-center">
              {onBuy && <button type="button" onClick={buy} data-testid="paywall-buy" className="rounded-xl bg-accent-blue px-5 py-2.5 text-sm font-semibold text-white transition hover:opacity-90">{t("medien.paywallBuy")}</button>}
              <button type="button" onClick={closePaywall} data-testid="paywall-back" className="rounded-xl bg-surface-hover px-5 py-2.5 text-sm font-semibold text-text-primary ring-1 ring-surface-border transition hover:opacity-90">{t("medien.paywallBack")}</button>
            </div>
          </div>
        </div>
      )}
    </div>,
    document.body,
  );
}
