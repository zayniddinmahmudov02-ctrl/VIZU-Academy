"use client";

/* eslint-disable @next/next/no-img-element -- local preview of the chosen file (object URL) */
import { useEffect, useRef, useState } from "react";

import { useTranslation } from "@/lib/i18n/use-translation";

import { buttonPrimary, buttonSecondary } from "./ui";

export interface Crop {
  x: number;
  y: number;
  w: number;
}

/** Pick an image and the part to keep at a fixed ratio (9:16 portrait / 16:9). Returns the file and the crop as fractions of the
 * image (x, y = left / top, w = width) — the server cuts and re-encodes; nothing is cut in the browser. */
export default function RatioCropper({ ratio, onSave, busy, testId }: {
  ratio: number; onSave: (file: File, crop: Crop) => void; busy?: boolean; testId?: string;
}) {
  const { t } = useTranslation();
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState<string | null>(null);
  const [size, setSize] = useState<{ w: number; h: number } | null>(null);
  const [crop, setCrop] = useState<Crop>({ x: 0, y: 0, w: 1 });
  const drag = useRef<{ px: number; py: number; x: number; y: number } | null>(null);
  const box = useRef<HTMLDivElement>(null);

  useEffect(() => () => { if (url) URL.revokeObjectURL(url); }, [url]);

  // the largest crop box with the ratio, centred
  const maxW = size ? Math.min(1, (size.h * ratio) / size.w) : 1;
  const hFrac = size ? (crop.w * size.w) / ratio / size.h : 1;
  const clamp = (c: Crop): Crop => {
    const w = Math.min(maxW, Math.max(0.1 * maxW, c.w));
    const h = size ? (w * size.w) / ratio / size.h : 1;
    return { w, x: Math.min(1 - w, Math.max(0, c.x)), y: Math.min(1 - h, Math.max(0, c.y)) };
  };

  function choose(f: File | null) {
    setFile(f);
    setSize(null);
    setUrl(f ? URL.createObjectURL(f) : null);
  }

  function loaded(e: React.SyntheticEvent<HTMLImageElement>) {
    const img = e.currentTarget;
    const s = { w: img.naturalWidth, h: img.naturalHeight };
    setSize(s);
    const w = Math.min(1, (s.h * ratio) / s.w);
    const h = (w * s.w) / ratio / s.h;
    // float noise (h = 1.0000000000000002) must not give a negative offset
    setCrop({ w, x: Math.max(0, (1 - w) / 2), y: Math.max(0, (1 - h) / 2) });
  }

  /** What goes to the server: fractions inside 0…1, 6 decimals. */
  const toSend = (c: Crop): Crop => {
    const f = (v: number) => Math.round(Math.min(1, Math.max(0, v)) * 1e6) / 1e6;
    return { x: f(c.x), y: f(c.y), w: f(c.w) };
  };

  function onPointerDown(e: React.PointerEvent) {
    drag.current = { px: e.clientX, py: e.clientY, x: crop.x, y: crop.y };
    try { (e.target as Element).setPointerCapture(e.pointerId); } catch { /* synthetic events in tests */ }
  }

  function onPointerMove(e: React.PointerEvent) {
    if (!drag.current || !box.current) return;
    const r = box.current.getBoundingClientRect();
    setCrop((c) => clamp({ ...c, x: drag.current!.x + (e.clientX - drag.current!.px) / r.width, y: drag.current!.y + (e.clientY - drag.current!.py) / r.height }));
  }

  return (
    <div className="space-y-3" data-testid={testId}>
      <label className={buttonSecondary + " cursor-pointer"}>
        {t("market.choosePhoto")}
        <input type="file" accept="image/jpeg,image/png,image/webp" className="sr-only" onChange={(e) => choose(e.target.files?.[0] ?? null)}
               data-testid={testId ? `${testId}-input` : undefined} />
      </label>
      {url && (
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
          <div ref={box} className="relative max-w-full touch-none select-none overflow-hidden rounded-xl bg-black/5 sm:max-w-[360px]">
            <img src={url} alt="" className="block max-h-[360px] w-auto max-w-full" onLoad={loaded} draggable={false} />
            {size && (
              <div className="absolute cursor-move border-2 border-white shadow-[0_0_0_9999px_rgba(0,0,0,0.45)]"
                   style={{ left: `${crop.x * 100}%`, top: `${crop.y * 100}%`, width: `${crop.w * 100}%`, height: `${hFrac * 100}%` }}
                   onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={() => { drag.current = null; }} data-testid="crop-box" />
            )}
          </div>
          {size && (
            <div className="flex flex-col gap-3">
              <div className="overflow-hidden rounded-xl ring-1 ring-surface-border" style={{ width: ratio < 1 ? 120 : 213, aspectRatio: `${ratio}` }}
                   aria-hidden>
                <div className="h-full w-full bg-no-repeat"
                     style={{ backgroundImage: `url(${url})`, backgroundSize: `${100 / crop.w}% auto`,
                              backgroundPosition: `${crop.w >= 1 ? 0 : (crop.x / (1 - crop.w)) * 100}% ${hFrac >= 1 ? 0 : (crop.y / (1 - hFrac)) * 100}%` }} />
              </div>
              <label className="text-xs text-text-secondary">{t("market.zoom")}
                <input type="range" min={10} max={100} value={Math.round((crop.w / maxW) * 100)} className="w-40"
                       onChange={(e) => setCrop((c) => {
                         const w = (Number(e.target.value) / 100) * maxW;
                         return clamp({ w, x: c.x + (c.w - w) / 2, y: c.y + (hFrac - (size ? (w * size.w) / ratio / size.h : 1)) / 2 });
                       })} />
              </label>
              <button type="button" className={buttonPrimary} disabled={!file || busy} onClick={() => file && onSave(file, toSend(crop))}
                      data-testid={testId ? `${testId}-save` : undefined}>{t("market.save")}</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
