"use client";

import { useEffect, useRef, useState, type KeyboardEvent, type PointerEvent } from "react";
import { Move, ZoomIn } from "lucide-react";

import { centred, clampOffset, MAX_ZOOM, MIN_ZOOM, toCrop, zoomAround, type Crop } from "@/features/profile/utils/photo-crop";
import { useTranslation } from "@/lib/i18n/use-translation";

const FRAME = 240;

/** Drag to reposition, slider / wheel / keys to zoom; the round mask shows how the avatar will look. */
export default function PhotoCropper({ src, onChange }: { src: string; onChange: (crop: Crop) => void }) {
  const { t } = useTranslation();
  const [natural, setNatural] = useState<{ w: number; h: number } | null>(null);
  const [view, setView] = useState({ zoom: 1, ox: 0, oy: 0 });
  const drag = useRef<{ x: number; y: number; ox: number; oy: number } | null>(null);

  useEffect(() => {
    if (natural) onChange(toCrop(natural.w, natural.h, FRAME, view.zoom, view.ox, view.oy));
  }, [natural, view, onChange]);

  const move = (dx: number, dy: number, base = view) => {
    if (!natural) return;
    setView({ zoom: base.zoom, ...clampOffset(natural.w, natural.h, FRAME, base.zoom, base.ox + dx, base.oy + dy) });
  };
  const zoomTo = (z: number) => natural && setView((v) => zoomAround(natural.w, natural.h, FRAME, v.zoom, z, v.ox, v.oy));

  const onDown = (e: PointerEvent<HTMLDivElement>) => {
    e.currentTarget.setPointerCapture(e.pointerId);
    drag.current = { x: e.clientX, y: e.clientY, ox: view.ox, oy: view.oy };
  };
  const onMove = (e: PointerEvent<HTMLDivElement>) => {
    const d = drag.current;
    if (d && natural) setView((v) => ({ zoom: v.zoom, ...clampOffset(natural.w, natural.h, FRAME, v.zoom, d.ox + e.clientX - d.x, d.oy + e.clientY - d.y) }));
  };
  const onKey = (e: KeyboardEvent<HTMLDivElement>) => {
    const step = { ArrowLeft: [10, 0], ArrowRight: [-10, 0], ArrowUp: [0, 10], ArrowDown: [0, -10] }[e.key];
    if (step) {
      e.preventDefault();
      move(step[0], step[1]);
    } else if (e.key === "+" || e.key === "=") zoomTo(view.zoom + 0.2);
    else if (e.key === "-") zoomTo(view.zoom - 0.2);
  };

  const s = natural ? (FRAME / Math.min(natural.w, natural.h)) * view.zoom : 1;

  return (
    <div className="flex flex-col items-center gap-3" data-testid="photo-cropper">
      <div
        role="application"
        tabIndex={0}
        aria-label={t("profile.cropHint")}
        onPointerDown={onDown}
        onPointerMove={onMove}
        onPointerUp={() => (drag.current = null)}
        onPointerCancel={() => (drag.current = null)}
        onWheel={(e) => zoomTo(view.zoom - Math.sign(e.deltaY) * 0.15)}
        onKeyDown={onKey}
        className="relative cursor-grab touch-none select-none overflow-hidden rounded-2xl bg-black/80 outline-none ring-1 ring-surface-border focus-visible:ring-2 focus-visible:ring-accent-blue active:cursor-grabbing"
        style={{ width: FRAME, height: FRAME }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element -- local object URL preview */}
        <img
          src={src}
          alt=""
          draggable={false}
          onLoad={(e) => {
            const w = e.currentTarget.naturalWidth;
            const h = e.currentTarget.naturalHeight;
            setNatural({ w, h });
            setView({ zoom: 1, ...centred(w, h, FRAME) });
          }}
          className="pointer-events-none absolute left-0 top-0 max-w-none origin-top-left"
          // inline max-width: the unlayered global `img { max-width: 100% }` would beat the utility class
          style={natural ? { width: natural.w * s, height: natural.h * s, maxWidth: "none", maxHeight: "none", transform: `translate(${view.ox}px, ${view.oy}px)` } : { opacity: 0 }}
        />
        <div aria-hidden="true" className="pointer-events-none absolute inset-0 bg-black/45 [mask-image:radial-gradient(circle,transparent_119px,black_120px)]" />
        <div aria-hidden="true" className="pointer-events-none absolute inset-0 m-auto h-[240px] w-[240px] rounded-full ring-2 ring-white/80" />
      </div>
      <label className="flex w-full max-w-[240px] items-center gap-2 text-xs text-text-muted">
        <ZoomIn size={14} aria-hidden="true" />
        <input type="range" min={MIN_ZOOM} max={MAX_ZOOM} step={0.01} value={view.zoom} onChange={(e) => zoomTo(Number(e.target.value))}
               className="flex-1 accent-[var(--accent-blue)]" aria-label={t("profile.cropZoom")} data-testid="photo-crop-zoom" />
      </label>
      <p className="flex items-center gap-1.5 text-xs text-text-muted"><Move size={13} aria-hidden="true" /> {t("profile.cropHint")}</p>
    </div>
  );
}
