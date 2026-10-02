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
}

/** The dashboard "Werbung-Banner" — used by the real dashboard AND by the
 * admin "Vorschau", so the preview looks exactly like what students see.
 * Explicit light colours (white / warm background, VIZU dark blue, blue and
 * flame-orange accents) so it renders identically inside the admin shell.
 * The whole banner is one link; reduced motion disables the slide-in. */
const AdvertisementBannerView = forwardRef<HTMLAnchorElement, Props>(function AdvertisementBannerView(
  { title, description, imageUrl, ctaText, href, external = false, badge },
  ref,
) {
  const reduce = useReducedMotion();
  const image = resolveMediaUrl(imageUrl ?? null);

  return (
    <motion.a
      ref={ref}
      href={href || undefined}
      target={external ? "_blank" : undefined}
      rel={external ? "noopener noreferrer sponsored" : undefined}
      initial={reduce ? { opacity: 0 } : { opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="group relative flex flex-col overflow-hidden rounded-[22px] border border-orange-100 bg-gradient-to-br from-white via-[#fff8ee] to-white shadow-[0_10px_30px_-12px_rgba(15,23,42,0.18)] transition-shadow hover:shadow-[0_16px_40px_-14px_rgba(15,23,42,0.28)] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-blue-300 sm:flex-row"
    >
      <div className="relative aspect-[16/9] w-full shrink-0 overflow-hidden bg-slate-100 sm:aspect-auto sm:w-[42%] sm:min-h-[220px]">
        {image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={image}
            alt=""
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.03] motion-reduce:transition-none motion-reduce:group-hover:scale-100"
          />
        ) : (
          <div className="flex h-full min-h-[180px] w-full items-center justify-center bg-gradient-to-br from-[#0f2a4a] to-blue-700">
            <Megaphone size={48} className="text-white/80" />
          </div>
        )}
      </div>

      <div className="flex flex-1 flex-col justify-center gap-3 px-6 py-6 sm:px-9 sm:py-8">
        {badge && <div>{badge}</div>}
        <h2 className="text-2xl font-extrabold leading-tight tracking-tight text-[#0f2a4a] sm:text-[28px]">{title}</h2>
        {description && <p className="max-w-xl text-sm leading-relaxed text-slate-600 sm:text-base">{description}</p>}
        <span className="mt-2 inline-flex w-fit items-center gap-2 rounded-full bg-blue-600 px-5 py-2.5 text-sm font-bold text-white shadow-md transition-all group-hover:bg-orange-500 group-active:scale-95 motion-reduce:transition-none">
          {ctaText}
          <ArrowRight size={16} className="transition-transform group-hover:translate-x-1 motion-reduce:transition-none" />
        </span>
      </div>

      <span aria-hidden="true" className="absolute inset-x-0 bottom-0 h-1 bg-gradient-to-r from-blue-600 via-orange-500 to-blue-600" />
    </motion.a>
  );
});

export default AdvertisementBannerView;
