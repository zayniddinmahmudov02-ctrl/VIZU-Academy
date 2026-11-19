"use client";

import { forwardRef, memo, useCallback, useEffect, useImperativeHandle, useRef, useState } from "react";
import { Loader2 } from "lucide-react";

import {
  clampView, dragAngle, FLIP_DEG, fitPage, nextZoomStep, pinchView, swipeDecision, TAP_MOVE, TAP_MS, tapZone, zoomAt, type Point, type View,
} from "../lib/reader-gestures";

type PdfDoc = import("pdfjs-dist").PDFDocumentProxy;
type RenderTask = import("pdfjs-dist").RenderTask;

const MAX_CANVAS_PIXELS = 12_000_000;
const TURN_MS = 420;
const IDLE: View = { scale: 1, x: 0, y: 0 };

/** One page drawn by pdf.js at `w` × `h` CSS px, sharpened for `quality` (the zoom it will be looked at) and the screen's pixel ratio. */
const PageCanvas = memo(function PageCanvas({ doc, n, w, h, quality, shown }: { doc: PdfDoc; n: number; w: number; h: number; quality: number; shown: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const spinRef = useRef<HTMLDivElement>(null);
  const busy = useRef<Promise<unknown>>(Promise.resolve());

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || w < 2) return;
    let cancelled = false;
    let task: RenderTask | null = null;
    (async () => {
      try {
        const page = await doc.getPage(n);
        if (cancelled) return;
        const base = page.getViewport({ scale: 1 });
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        let scale = (w / base.width) * dpr * quality;
        const pixels = base.width * scale * base.height * scale;
        if (pixels > MAX_CANVAS_PIXELS) scale *= Math.sqrt(MAX_CANVAS_PIXELS / pixels);
        const viewport = page.getViewport({ scale });
        await busy.current;
        if (cancelled) return;
        canvas.width = Math.floor(viewport.width);
        canvas.height = Math.floor(viewport.height);
        task = page.render({ canvas, canvasContext: canvas.getContext("2d")!, viewport });
        busy.current = task.promise.catch(() => undefined);
        await task.promise;
        if (!cancelled && spinRef.current) spinRef.current.hidden = true;
        page.cleanup();
      } catch {
        /* a cancelled render (page turned, zoom changed) is expected */
      }
    })();
    return () => { cancelled = true; task?.cancel(); };
  }, [doc, n, w, h, quality]);

  return (
    <>
      <canvas ref={canvasRef} data-testid={shown ? "reader-canvas" : undefined} className="absolute inset-0 h-full w-full" />
      <div ref={spinRef} className="absolute inset-0 flex items-center justify-center text-stone-400" aria-hidden="true"><Loader2 className="animate-spin" size={22} /></div>
    </>
  );
});

type Turn = { dir: "next" | "prev"; angle: number; animate: boolean; commit: boolean };

export interface BookViewHandle {
  /** turns one page with the page animation (false when that page cannot be reached) */
  turn: (dir: "next" | "prev") => boolean;
  zoom: (dir: 1 | -1) => void;
  resetZoom: () => void;
}

interface Props {
  doc: PdfDoc;
  page: number;
  pages: number;
  ratioOf: (n: number) => number;
  /** may the reader go to page n (a preview ends at its last free page) */
  canGo: (n: number) => boolean;
  /** a turn past the last page of a preview: the parent shows the paywall */
  onBlocked: () => void;
  onTurned: (n: number) => void;
  onScale: (scale: number) => void;
}

/** One page at a time, like a book.
 * - Phones: swipe right-to-left = next page, left-to-right = previous; the page follows the finger and turns over the spine (3D) when let go
 *   far / fast enough, else it falls back. Two fingers zoom (pinch, around the fingers) and move the zoomed page; one finger then pans —
 *   a pinch is never taken as a swipe, and a zoomed page never turns. Double tap in the middle: zoom 2× / back.
 * - Desktop: click the left / right third of the page, the buttons and ← → in the toolbar (parent), ctrl + wheel zooms, wheel pans a zoomed page.
 * Previous / current / next page stay drawn (same React keys while they change roles), so a turn never waits for pdf.js. */
const BookView = forwardRef<BookViewHandle, Props>(function BookView({ doc, page, pages, ratioOf, canGo, onBlocked, onTurned, onScale }, ref) {
  const stageRef = useRef<HTMLDivElement>(null);
  const [stage, setStage] = useState({ w: 0, h: 0 });
  const [view, setViewState] = useState<View>(IDLE);
  const [quality, setQuality] = useState(1);
  const [turn, setTurn] = useState<Turn | null>(null);
  const viewRef = useRef(view);
  const turnRef = useRef<Turn | null>(null);
  const pointers = useRef(new Map<number, Point>());
  const gesture = useRef<{ start: Point; t: number; view: View; multi: boolean; pinch: { a: Point; b: Point; view: View } | null; moved: boolean; lastTap: { t: number; p: Point } | null }>(
    { start: { x: 0, y: 0 }, t: 0, view: IDLE, multi: false, pinch: null, moved: false, lastTap: null });
  const reduced = useRef(false);

  const box = useCallback((n: number) => fitPage(stage.w, stage.h, ratioOf(n)), [stage, ratioOf]);
  const current = box(page);

  const setView = useCallback((v: View) => {
    const next = clampView(v, current.w, current.h, stage.w, stage.h);
    viewRef.current = next;
    setViewState(next);
    onScale(next.scale);
  }, [current.w, current.h, stage.w, stage.h, onScale]);

  const setTurnBoth = (t: Turn | null) => { turnRef.current = t; setTurn(t); };

  useEffect(() => {
    reduced.current = typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const el = stageRef.current;
    if (!el) return;
    const observer = new ResizeObserver(() => setStage({ w: el.clientWidth, h: el.clientHeight }));
    observer.observe(el);
    setStage({ w: el.clientWidth, h: el.clientHeight });
    return () => observer.disconnect();
  }, []);

  // a new page (or another stage size) starts un-zoomed
  useEffect(() => { viewRef.current = IDLE; setViewState(IDLE); setQuality(1); onScale(1); }, [page, stage.w, stage.h, onScale]);

  // sharpen the page shortly after a zoom gesture settled
  useEffect(() => {
    const t = window.setTimeout(() => setQuality(Math.min(4, Math.max(1, Math.round(view.scale * 2) / 2))), 180);
    return () => window.clearTimeout(t);
  }, [view.scale]);

  // turns asked for while one is still running (quick clicks / key repeat) run one after the other
  const queue = useRef<("next" | "prev")[]>([]);
  const ownPage = useRef<number | null>(null);
  const timer = useRef<number | undefined>(undefined);

  /** runs the rest of a turn (or its way back) as a CSS transition, then tells the parent */
  const finishTurn = useCallback((dir: "next" | "prev", commit: boolean) => {
    const target = commit ? (dir === "next" ? -FLIP_DEG : 0) : (dir === "next" ? 0 : -FLIP_DEG);
    const done = () => {
      setTurnBoth(null);
      if (commit) {
        ownPage.current = dir === "next" ? page + 1 : page - 1;
        onTurned(ownPage.current);
      } else queue.current = [];
    };
    if (reduced.current) { done(); return; }
    setTurnBoth({ dir, angle: target, animate: true, commit });
    timer.current = window.setTimeout(done, TURN_MS + 30);
  }, [onTurned, page]);

  const startTurn = useCallback((dir: "next" | "prev"): boolean => {
    const to = dir === "next" ? page + 1 : page - 1;
    if (turnRef.current) {
      if (queue.current.length < 4) queue.current.push(dir);
      return true;
    }
    if (!canGo(to)) {
      queue.current = [];
      if (dir === "next" && to > pages) onBlocked();
      return false;
    }
    if (reduced.current) { onTurned(to); return true; }
    setTurnBoth({ dir, angle: dir === "next" ? 0 : -FLIP_DEG, animate: false, commit: true });
    // two frames: the start angle is painted, then the transition runs to the end
    requestAnimationFrame(() => requestAnimationFrame(() => finishTurn(dir, true)));
    return true;
  }, [page, pages, canGo, onBlocked, onTurned, finishTurn]);

  // the page changed: after our own turn the next queued turn starts; a jump from outside (page box) ends a running turn and the queue
  useEffect(() => {
    if (ownPage.current === page) {
      ownPage.current = null;
      if (!turnRef.current && queue.current.length) startTurn(queue.current.shift()!);
      return;
    }
    queue.current = [];
    window.clearTimeout(timer.current);
    if (turnRef.current) setTurnBoth(null);
  }, [page]); // eslint-disable-line react-hooks/exhaustive-deps -- only a page change counts here
  useEffect(() => () => window.clearTimeout(timer.current), []);

  useImperativeHandle(ref, () => ({
    turn: startTurn,
    zoom: (dir) => setView(zoomAt(viewRef.current, nextZoomStep(viewRef.current.scale, dir))),
    resetZoom: () => setView(IDLE),
  }), [startTurn, setView]);

  // ctrl + wheel (also a touchpad pinch on desktop) zooms around the pointer; the wheel moves a zoomed page
  useEffect(() => {
    const el = stageRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      const v = viewRef.current;
      const r = el.getBoundingClientRect();
      const at = { x: e.clientX - r.left - r.width / 2, y: e.clientY - r.top - r.height / 2 };
      if (e.ctrlKey) { e.preventDefault(); setView(zoomAt(v, v.scale * Math.exp(-e.deltaY / 300), at)); }
      else if (v.scale > 1.01) { e.preventDefault(); setView({ ...v, x: v.x - e.deltaX, y: v.y - e.deltaY }); }
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, [setView]);

  const local = (e: React.PointerEvent): Point => {
    const r = stageRef.current!.getBoundingClientRect();
    return { x: e.clientX - r.left - r.width / 2, y: e.clientY - r.top - r.height / 2 };
  };

  function onPointerDown(e: React.PointerEvent) {
    if (e.pointerType === "mouse" && e.button !== 0) return;
    try { stageRef.current?.setPointerCapture(e.pointerId); } catch { /* a pointer the browser does not track (e.g. synthetic): still handled */ }
    const p = local(e);
    pointers.current.set(e.pointerId, p);
    const g = gesture.current;
    if (pointers.current.size === 1) {
      g.start = p; g.t = performance.now(); g.view = viewRef.current; g.moved = false; g.multi = false; g.pinch = null;
    } else if (pointers.current.size === 2) {
      const [a, b] = [...pointers.current.values()];
      g.multi = true;
      g.pinch = { a, b, view: viewRef.current };
      if (turnRef.current && !turnRef.current.animate) finishTurn(turnRef.current.dir, false); // a second finger cancels a page drag
    }
  }

  function onPointerMove(e: React.PointerEvent) {
    if (!pointers.current.has(e.pointerId)) return;
    const p = local(e);
    pointers.current.set(e.pointerId, p);
    const g = gesture.current;
    if (pointers.current.size >= 2 && g.pinch) {
      const [a, b] = [...pointers.current.values()];
      setView(pinchView(g.pinch.view, g.pinch.a, g.pinch.b, a, b));
      return;
    }
    if (g.multi || pointers.current.size !== 1) return;
    const dx = p.x - g.start.x;
    const dy = p.y - g.start.y;
    if (Math.hypot(dx, dy) > TAP_MOVE) g.moved = true;
    if (g.view.scale > 1.01) { setView({ ...g.view, x: g.view.x + dx, y: g.view.y + dy }); return; }
    if (turnRef.current?.animate) return;
    if (!g.moved || Math.abs(dx) < Math.abs(dy)) return;
    const dir = dx < 0 ? "next" : "prev";
    if (!canGo(dir === "next" ? page + 1 : page - 1)) return; // nothing to turn to: the page stays (a preview shows its paywall on release)
    setTurnBoth({ dir, angle: dragAngle(dx, current.w, dir), animate: false, commit: true });
  }

  function onPointerUp(e: React.PointerEvent) {
    if (!pointers.current.has(e.pointerId)) return;
    const p = local(e);
    pointers.current.delete(e.pointerId);
    const g = gesture.current;
    if (pointers.current.size > 0) { if (pointers.current.size === 1) g.pinch = null; return; }
    if (g.multi) { g.multi = false; return; } // the end of a pinch is never a swipe or a tap
    const dx = p.x - g.start.x;
    const dy = p.y - g.start.y;
    const ms = performance.now() - g.t;
    const t = turnRef.current;
    if (t && !t.animate) {
      const decision = swipeDecision(dx, dy, ms, current.w);
      finishTurn(t.dir, decision === t.dir);
      return;
    }
    if (g.moved) {
      if (g.view.scale > 1.01) return; // the end of moving a zoomed page
      const decision = swipeDecision(dx, dy, ms, current.w);
      if (decision !== "cancel") startTurn(decision); // a flick towards a page that cannot be reached: startTurn shows the paywall
      return;
    }
    if (ms > TAP_MS) return;
    // a tap: double tap = zoom 2× there / back to the whole page; a single tap on the left / right third turns the page (un-zoomed only)
    const now = performance.now();
    const last = g.lastTap;
    const zoomed = viewRef.current.scale > 1.01;
    if (last && now - last.t < 320 && Math.hypot(last.p.x - p.x, last.p.y - p.y) < 40) {
      g.lastTap = null;
      setView(zoomed ? IDLE : zoomAt(viewRef.current, 2, p));
      return;
    }
    g.lastTap = { t: now, p };
    if (zoomed) return;
    const rect = stageRef.current!.getBoundingClientRect();
    const zone = tapZone(p.x + rect.width / 2, rect.width);
    if (zone !== "middle") { g.lastTap = null; startTurn(zone); }
  }

  function onPointerCancel(e: React.PointerEvent) {
    pointers.current.delete(e.pointerId);
    if (pointers.current.size === 0) {
      gesture.current.multi = false;
      if (turnRef.current && !turnRef.current.animate) finishTurn(turnRef.current.dir, false);
    }
  }

  const neighbours = [page - 1, page, page + 1].filter((n) => n >= 1 && n <= pages);
  const shade = turn ? Math.min(0.45, (Math.abs(turn.angle) / FLIP_DEG) * 0.45) : 0;

  return (
    <div ref={stageRef} className="relative h-full w-full touch-none select-none overflow-hidden" style={{ perspective: "2200px" }}
         onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={onPointerUp} onPointerCancel={onPointerCancel}
         data-testid="reader-book" data-page={page} data-scale={view.scale.toFixed(2)} data-turning={turn ? turn.dir : ""}>
      {stage.w > 0 && neighbours.map((n) => {
        const size = box(n);
        let role: "current" | "below" | "top" | "hidden" = n === page ? "current" : "hidden";
        if (turn?.dir === "next") role = n === page ? "top" : n === page + 1 ? "below" : "hidden";
        if (turn?.dir === "prev") role = n === page - 1 ? "top" : n === page ? "below" : "hidden";
        const transform = role === "current"
          ? `translate(${view.x}px, ${view.y}px) scale(${view.scale})`
          : role === "top" ? `rotateY(${turn!.angle}deg)` : undefined;
        return (
          <div key={n} data-page={n} data-role={role} data-testid={role === "current" || role === "below" || role === "top" ? "reader-page-view" : undefined}
               className="absolute left-1/2 top-1/2 bg-white shadow-[0_12px_32px_rgba(0,0,0,0.45)]"
               style={{
                 width: size.w, height: size.h, marginLeft: -size.w / 2, marginTop: -size.h / 2,
                 visibility: role === "hidden" ? "hidden" : "visible", zIndex: role === "top" ? 3 : role === "below" ? 1 : role === "current" ? 2 : 0,
                 transform, transformOrigin: role === "top" ? "left center" : "center center", backfaceVisibility: "hidden",
                 transition: role === "top" && turn?.animate ? `transform ${TURN_MS}ms cubic-bezier(0.3, 0.1, 0.25, 1)` : undefined,
                 willChange: role === "top" || role === "current" ? "transform" : undefined,
               }}>
            <PageCanvas doc={doc} n={n} w={size.w} h={size.h} quality={n === page && !turn ? quality : 1} shown={role !== "hidden"} />
            {role === "top" && <div className="pointer-events-none absolute inset-0 bg-gradient-to-l from-black to-transparent" style={{ opacity: shade }} />}
            {role === "below" && <div className="pointer-events-none absolute inset-y-0 left-0 w-1/3 bg-gradient-to-r from-black/30 to-transparent" style={{ opacity: 1 - shade / 0.45 }} />}
          </div>
        );
      })}
    </div>
  );
});

export default BookView;
