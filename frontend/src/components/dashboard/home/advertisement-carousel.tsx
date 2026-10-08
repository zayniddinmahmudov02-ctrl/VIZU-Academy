"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useReducedMotion } from "framer-motion";
import { Pause, Play } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import {
  advertisementClickUrl,
  trackAdvertisementImpression,
  type ActiveAdvertisement,
} from "@/features/advertisements/advertisement";

import AdvertisementBannerView from "./advertisement-banner-view";
import styles from "./advertisement-carousel.module.css";
import { shatterPattern, type ShatterPattern } from "./glass-shatter";

/** Each banner is on screen for 7 s (its reveal included), then shatters. */
export const SLIDE_INTERVAL_MS = 7000;
/** Glass-shatter transition length; the rest of the 7 s the banner is static. */
export const SHATTER_MS = 900;
/** prefers-reduced-motion: a plain cross-fade instead of the shatter. */
const FADE_MS = 300;

interface Leaving {
  ad: ActiveAdvertisement;
  pattern: ShatterPattern;
  key: number;
}

function Slide({ ad, animateIn = false }: { ad: ActiveAdvertisement; animateIn?: boolean }) {
  return (
    <AdvertisementBannerView
      title={ad.title}
      description={ad.description}
      imageUrl={ad.image_url}
      ctaText={ad.cta_text}
      href={advertisementClickUrl(ad)}
      external
      animateIn={animateIn}
    />
  );
}

/** Static, non-interactive copy of a banner for the shard layers. */
function SlideCopy({ ad }: { ad: ActiveAdvertisement }) {
  return (
    <div className="h-full [&>a]:h-full">
      <AdvertisementBannerView
        title={ad.title}
        description={ad.description}
        imageUrl={ad.image_url}
        ctaText={ad.cta_text}
        animateIn={false}
      />
    </div>
  );
}

type CssVars = React.CSSProperties & Record<`--${string}`, string>;

/** The outgoing banner breaking like glass: a short crack flash, then the
 * shards fall apart. Pure CSS keyframes (transform + opacity only), each
 * shard parameterised through CSS custom properties. */
function Shatter({ leaving }: { leaving: Leaving }) {
  const { ad, pattern } = leaving;
  return (
    <div aria-hidden="true" inert className="pointer-events-none absolute inset-0 z-10 overflow-hidden rounded-[22px]" data-testid="ad-shatter">
      {pattern.shards.map((shard, i) => {
        const style: CssVars = {
          clipPath: shard.clipPath,
          WebkitClipPath: shard.clipPath,
          "--ox": shard.origin.split(" ")[0],
          "--oy": shard.origin.split(" ")[1],
          "--dx": `${shard.dx.toFixed(1)}px`,
          "--dy": `${shard.dy.toFixed(1)}px`,
          "--rot": `${shard.rotate.toFixed(1)}deg`,
          "--delay": `${Math.round(shard.delay * 1000)}ms`,
          "--fall": `${Math.round(SHATTER_MS - shard.delay * 1000)}ms`,
        };
        return (
          <div key={i} className={styles.shard} style={style}>
            <SlideCopy ad={ad} />
            <span className={styles.sheen} />
          </div>
        );
      })}
      <svg className={styles.cracks} style={{ "--crack": `${Math.round(SHATTER_MS * 0.55)}ms` } as CssVars} viewBox="0 0 100 100" preserveAspectRatio="none">
        {pattern.cracks.map(([a, b], i) => (
          <g key={i}>
            <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="rgba(15,23,42,0.35)" strokeWidth={2.4} vectorEffect="non-scaling-stroke" />
            <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="rgba(255,255,255,0.95)" strokeWidth={1.1} vectorEffect="non-scaling-stroke" />
          </g>
        ))}
        <circle cx={pattern.impact.x} cy={pattern.impact.y} r={1.2} fill="rgba(255,255,255,0.9)" />
      </svg>
    </div>
  );
}

/** Reduced motion: the outgoing banner simply fades out. */
function FadeOut({ leaving }: { leaving: Leaving }) {
  return (
    <div
      aria-hidden="true"
      inert
      className={`pointer-events-none absolute inset-0 z-10 ${styles.fadeOut}`}
      style={{ "--fade": `${FADE_MS}ms` } as CssVars}
      data-testid="ad-fade"
    >
      <SlideCopy ad={leaving.ad} />
    </div>
  );
}

/** Dashboard Werbung carousel: rotates through every eligible advertisement
 * (7 s each, continuous, wraps to the first) with a glass-shatter transition.
 * Autoplay pauses on hover / keyboard focus, while the banner is off-screen,
 * in a background tab, or via the pause button. Impressions are sent once per
 * advertisement per page visit, only while that banner is really visible. */
export default function AdvertisementCarousel({ ads }: { ads: ActiveAdvertisement[] }) {
  const { t } = useTranslation();
  const reduce = useReducedMotion();
  const count = ads.length;

  const [index, setIndex] = useState(0);
  const [leaving, setLeaving] = useState<Leaving | null>(null);
  const [hoverPaused, setHoverPaused] = useState(false);
  const [userPaused, setUserPaused] = useState(false);
  const [inView, setInView] = useState(false);
  const [tabHidden, setTabHidden] = useState(false);
  const [transitionCount, setTransitionCount] = useState(0);

  const rootRef = useRef<HTMLDivElement>(null);
  const tracked = useRef<Set<string>>(new Set());
  const endTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const current = ads[index % Math.max(count, 1)];

  // Visibility of the banner (impressions + pausing while off-screen).
  useEffect(() => {
    const node = rootRef.current;
    if (!node || typeof IntersectionObserver === "undefined") return;
    const observer = new IntersectionObserver((entries) => setInView(entries.some((e) => e.isIntersecting)), { threshold: 0.5 });
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const onChange = () => setTabHidden(document.visibilityState === "hidden");
    document.addEventListener("visibilitychange", onChange);
    return () => document.removeEventListener("visibilitychange", onChange);
  }, []);

  // One impression per advertisement per page visit, only when really visible.
  useEffect(() => {
    if (!current || !inView || tabHidden || tracked.current.has(current.id)) return;
    tracked.current.add(current.id);
    void trackAdvertisementImpression(current.id).catch(() => {
      /* analytics must never break the dashboard */
    });
  }, [current, inView, tabHidden]);

  const goTo = useCallback(
    (next: number) => {
      if (count < 2 || leaving) return;
      const target = ((next % count) + count) % count;
      if (target === index % count) return;
      const n = transitionCount + 1;
      setTransitionCount(n);
      setLeaving({ ad: ads[index % count], pattern: shatterPattern(n), key: n });
      setIndex(target);
      if (endTimer.current) clearTimeout(endTimer.current);
      endTimer.current = setTimeout(() => setLeaving(null), reduce ? FADE_MS : SHATTER_MS);
    },
    [ads, count, index, leaving, reduce, transitionCount],
  );

  useEffect(() => () => {
    if (endTimer.current) clearTimeout(endTimer.current);
  }, []);

  // Autoplay: next banner 7 s after the current one appeared. The timer
  // depends only on the slide and the pause state — not on goTo, which
  // changes when a transition ends and would otherwise restart the 7 s.
  const goToRef = useRef(goTo);
  useEffect(() => {
    goToRef.current = goTo;
  }, [goTo]);
  const paused = hoverPaused || userPaused || !inView || tabHidden;
  useEffect(() => {
    if (count < 2 || paused) return;
    const timer = setTimeout(() => goToRef.current(index + 1), SLIDE_INTERVAL_MS);
    return () => clearTimeout(timer);
  }, [count, paused, index]);

  const dots = useMemo(() => ads.map((ad, i) => ({ id: ad.id, i })), [ads]);

  if (!current) return null;

  return (
    <div
      ref={rootRef}
      role="region"
      aria-roledescription="carousel"
      aria-label={t("dashboard.adCarouselLabel")}
      className="relative"
      onMouseEnter={() => setHoverPaused(true)}
      onMouseLeave={() => setHoverPaused(false)}
      onFocusCapture={() => setHoverPaused(true)}
      onBlurCapture={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setHoverPaused(false);
      }}
      data-testid="ad-carousel"
    >
      <div
        key={`${current.id}:${transitionCount}`}
        role="group"
        aria-roledescription="slide"
        aria-label={count > 1 ? t("dashboard.adSlide", { n: (index % count) + 1, total: count }) : undefined}
        className={transitionCount > 0 ? (reduce ? styles.fadeIn : styles.reveal) : undefined}
        style={{ "--reveal": `${SHATTER_MS}ms`, "--fade": `${FADE_MS}ms` } as CssVars}
        data-testid="ad-slide"
        data-ad-id={current.id}
      >
        {/* the very first banner keeps the existing slide-in */}
        <Slide ad={current} animateIn={transitionCount === 0} />
      </div>

      {leaving && (reduce ? <FadeOut key={leaving.key} leaving={leaving} /> : <Shatter key={leaving.key} leaving={leaving} />)}

      {count > 1 && (
        <div className="absolute right-3 top-3 z-20 flex items-center gap-1 rounded-full bg-white/85 px-1.5 py-1 shadow-sm ring-1 ring-slate-200/70 backdrop-blur">
          {dots.map(({ id, i }) => {
            const active = i === index % count;
            return (
              <button
                key={id}
                type="button"
                onClick={() => goTo(i)}
                aria-label={t("dashboard.adSlide", { n: i + 1, total: count })}
                aria-current={active ? "true" : undefined}
                className="flex h-6 items-center px-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
                data-testid="ad-dot"
              >
                <span className={`block h-2 rounded-full transition-all duration-300 motion-reduce:transition-none ${active ? "w-5 bg-blue-600" : "w-2 bg-slate-300 hover:bg-slate-400"}`} />
              </button>
            );
          })}
          <button
            type="button"
            onClick={() => setUserPaused((v) => !v)}
            aria-label={userPaused ? t("dashboard.adPlay") : t("dashboard.adPause")}
            aria-pressed={userPaused}
            className="ml-0.5 flex h-6 w-6 items-center justify-center rounded-full text-slate-600 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
            data-testid="ad-pause"
          >
            {userPaused ? <Play size={12} /> : <Pause size={12} />}
          </button>
        </div>
      )}
    </div>
  );
}
