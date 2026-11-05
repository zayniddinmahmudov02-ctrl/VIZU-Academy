"use client";

import { forwardRef, type ReactNode } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, Megaphone } from "lucide-react";

import { resolveMediaUrl } from "@/lib/media";

interface Props {
  title: string;
  description?: string | null;
  imageUrl?: string | null;
  ctaText: string;
  /** Where the banner leads. External (tracking) links open in a new tab. */
  href?: string;
  external?: boolean;
  /** Small label above the title (e.g. "Werbung"). */
  badge?: ReactNode;
  /** Slide-in on mount (default). The carousel turns it off for slides it
   * reveals itself and for the static shard copies of the glass effect. */
  animateIn?: boolean;
  /** Internal links: in-app navigation + click tracking. */
  onClick?: (event: React.MouseEvent<HTMLAnchorElement>) => void;
}

/** The dashboard "Werbung-Banner" — used by the real dashboard AND by the
 * admin "Vorschau", so the preview looks exactly like what students see.
 * Explicit light colours (white / warm background, VIZU dark blue, blue and
 * flame-orange accents) so it renders identically inside the admin shell.
 * The whole banner is one link; reduced motion disables the slide-in. */
const AdvertisementBannerView = forwardRef<HTMLAnchorElement, Props>(function AdvertisementBannerView(
  { title, description, imageUrl, ctaText, href, external = false, badge, animateIn = true, onClick },
  ref,
) {
  const reduce = useReducedMotion();
  const image = resolveMediaUrl(imageUrl ?? null);

  return (
    <motion.a
      ref={ref}
      href={href || undefined}
      onClick={onClick}
      target={external ? "_blank" : undefined}
      rel={external ? "noopener noreferrer sponsored" : undefined}
      initial={!animateIn ? false : reduce ? { opacity: 0 } : { opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="group relative flex flex-row overflow-hidden rounded-[22px] border border-orange-100 bg-gradient-to-br from-white via-[#fff8ee] to-white shadow-[0_10px_30px_-12px_rgba(15,23,42,0.18)] transition-shadow hover:shadow-[0_16px_40px_-14px_rgba(15,23,42,0.28)] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-blue-300"
    >
      {/* Compact (2026-11-05): ~29 % lower than before on desktop (220 → 156 px); horizontal on phones too
          (image left, text + CTA right) instead of a tall stacked card. */}
      <div className="relative w-[34%] min-h-[128px] shrink-0 overflow-hidden bg-slate-100 sm:w-[36%] sm:min-h-[156px]">
        {image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={image}
            alt=""
            className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.03] motion-reduce:transition-none motion-reduce:group-hover:scale-100"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-[#0f2a4a] to-blue-700">
            <Megaphone size={32} className="text-white/80" />
          </div>
        )}
      </div>

      <div className="flex min-w-0 flex-1 flex-col justify-center gap-1 px-3 py-3 sm:gap-2 sm:px-7 sm:py-4">
        {badge && <div>{badge}</div>}
        <h2 className="text-base font-extrabold leading-tight tracking-tight text-[#0f2a4a] sm:text-[22px]">{title}</h2>
        {description && <p className="line-clamp-2 max-w-xl text-xs leading-snug text-slate-600 sm:text-sm">{description}</p>}
        <span className="mt-1 inline-flex min-h-[40px] w-fit max-w-full items-center gap-1.5 rounded-full bg-blue-600 px-3.5 py-2 text-[13px] font-bold text-white sm:px-4 sm:text-sm shadow-md transition-all group-hover:bg-orange-500 group-active:scale-95 motion-reduce:transition-none">
          {ctaText}
          <ArrowRight size={16} className="transition-transform group-hover:translate-x-1 motion-reduce:transition-none" />
        </span>
      </div>

      <span aria-hidden="true" className="absolute inset-x-0 bottom-0 h-1 bg-gradient-to-r from-blue-600 via-orange-500 to-blue-600" />
    </motion.a>
  );
});

export default AdvertisementBannerView;
