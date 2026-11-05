"use client";

import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";

import { API_URL } from "@/constants/api";
import { resolveThemeImage } from "@/features/battle/lib/battle-utils";
import type { Theme } from "@/features/battle/services/battle-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

const PARTICLES = Array.from({ length: 14 }, (_, i) => ({
  left: `${(i * 37) % 100}%`,
  d: `${8 + ((i * 7) % 9)}s`,
  delay: `${(i * 1.3) % 9}s`,
  x: `${((i % 5) - 2) * 24}px`,
  size: 2 + (i % 3),
}));

/**
 * Full-screen German city background of a stage: desktop / mobile picture, parallax on pointer move,
 * slow camera drift, light beams, gold particles, optional neon arena floor. Falls back to a gradient
 * when the picture fails. `lowFx` (slow device) keeps only the still picture and the overlay.
 */
export default function BattleScene({ theme, arena = false, lowFx = false, showCredit = true }: { theme: Theme | null; arena?: boolean; lowFx?: boolean; showCredit?: boolean }) {
  const { t } = useTranslation();
  const ref = useRef<HTMLDivElement>(null);
  const desktop = useMemo(() => resolveThemeImage(theme?.desktop_image, API_URL), [theme?.desktop_image]);
  const mobile = useMemo(() => resolveThemeImage(theme?.mobile_image, API_URL) ?? desktop, [theme?.mobile_image, desktop]);
  const [failed, setFailed] = useState<string | null>(null);
  const broken = failed !== null && failed === desktop;
  const overlay = Math.max(0, Math.min(90, theme?.overlay ?? 55)) / 100;

  useEffect(() => {
    const el = ref.current;
    if (!el || lowFx || !window.matchMedia("(pointer: fine)").matches) return;
    let raf = 0;
    const onMove = (e: PointerEvent) => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const x = (e.clientX / window.innerWidth - 0.5) * -24;
        const y = (e.clientY / window.innerHeight - 0.5) * -14;
        el.style.setProperty("--bt-px", `${x.toFixed(1)}px`);
        el.style.setProperty("--bt-py", `${y.toFixed(1)}px`);
      });
    };
    window.addEventListener("pointermove", onMove, { passive: true });
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("pointermove", onMove);
    };
  }, [lowFx]);

  const accent = theme?.accent ?? "#3984E8";
  const credit = theme?.attribution;

  return (
    <>
      <div ref={ref} aria-hidden="true" className="pointer-events-none fixed inset-0 -z-10 overflow-hidden" style={{ "--bt-accent": accent } as CSSProperties}>
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,#1f4e9a_0%,#101d35_55%,#0a1222_100%)]" />
        {desktop && !broken && (
          <picture>
            {mobile && <source media="(max-width: 767px)" srcSet={mobile} />}
            <img
              key={desktop}
              src={desktop}
              alt=""
              decoding="async"
              fetchPriority="high"
              onError={() => setFailed(desktop)}
              className={cn("absolute inset-0 h-full w-full object-cover", !lowFx && "bt-scene-img")}
            />
          </picture>
        )}
        <div className="absolute inset-0" style={{ background: `linear-gradient(180deg, rgba(16,29,53,${overlay * 0.55}) 0%, rgba(16,29,53,${overlay * 0.35}) 35%, rgba(16,29,53,${Math.min(0.97, overlay + 0.35)}) 100%)` }} />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_40%,rgba(5,10,20,0.65)_100%)]" />
        {!lowFx && (
          <>
            <div className="bt-beam absolute -top-1/4 left-[12%] h-[150%] w-40" />
            <div className="bt-beam absolute -top-1/4 right-[18%] h-[150%] w-28 [animation-delay:-4s]" />
            <div className="absolute inset-0">
              {PARTICLES.map((p, i) => (
                <span key={i} className="bt-particle" style={{ left: p.left, width: p.size, height: p.size, "--d": p.d, "--delay": p.delay, "--x": p.x } as CSSProperties} />
              ))}
            </div>
          </>
        )}
        {arena && <div className={cn("absolute inset-x-[-20%] bottom-0 h-[38%]", !lowFx ? "bt-grid-floor" : "hidden")} />}
        <div className="absolute inset-x-0 top-0 h-[3px] bt-flag-line opacity-90" />
      </div>
      {showCredit && credit?.author && desktop && !broken && (
        <p className="pointer-events-auto fixed bottom-1 right-2 z-0 hidden max-w-[50vw] truncate text-[10px] text-white/45 md:block" data-testid="battle-photo-credit">
          {t("battle.photo")}: {theme?.city} ·{" "}
          {credit.source_url ? (
            <a href={credit.source_url} target="_blank" rel="noopener noreferrer" className="underline decoration-white/30 hover:text-white/80">{credit.author}</a>
          ) : credit.author}
          {credit.license && <> · {credit.license_url ? <a href={credit.license_url} target="_blank" rel="noopener noreferrer license" className="underline decoration-white/30 hover:text-white/80">{credit.license}</a> : credit.license}</>}
        </p>
      )}
    </>
  );
}
