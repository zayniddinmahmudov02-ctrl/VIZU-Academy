"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { LucideIcon } from "lucide-react";
import { ChevronRight } from "lucide-react";
import { motion } from "framer-motion";

import Tooltip from "@/components/ui/tooltip";
import { useTranslation } from "@/lib/i18n/use-translation";

interface Props {
  titleKey: string;
  href: string;
  icon: LucideIcon;
  collapsed?: boolean;
}

export default function NavItem({
  titleKey,
  href,
  icon: Icon,
  collapsed,
}: Props) {
  const pathname = usePathname();
  const { t } = useTranslation();
  const title = t(titleKey);

  const active =
    pathname === href || pathname.startsWith(`${href}/`);

  return (
    <Tooltip label={title} disabled={!collapsed}>
      <Link
        href={href}
        // This link is part of the persistent sidebar/mobile nav, mounted
        // once and visible on every dashboard page. Next.js prefetches a
        // visible Link's full route+data, and re-prefetches it again each
        // time the router context it was cached against changes (i.e. on
        // every client-side navigation) — with ~9 always-visible nav links,
        // that adds up to hundreds of background requests during normal
        // browsing (measured: ~1370 req/min while navigating between
        // lesson sections). None of these links benefit meaningfully from
        // being prefetched milliseconds early, so it's not worth the cost.
        prefetch={false}
        className={`group relative flex items-center gap-3 overflow-hidden rounded-2xl px-3.5 py-3 text-sm font-semibold transition-all duration-300 ${
          collapsed ? "justify-center" : ""
        } ${
          active
            ? "text-accent-gold dark:text-white"
            : "text-accent-gold dark:text-white hover:bg-white/5 hover:text-[#FFD700] dark:hover:text-white"
        }`}
      >
        {active && (
          <motion.span
            layoutId="active-nav-pill"
            transition={{
              type: "spring",
              stiffness: 420,
              damping: 35,
            }}
            className="absolute inset-0 rounded-2xl border border-accent-gold/40 bg-gradient-to-r from-[#18243F] via-[#22395A] to-[#18243F] shadow-[var(--shadow-3d-gold)]"
          />
        )}

        <Icon
          size={18}
          strokeWidth={2}
          className={`relative z-10 shrink-0 transition-all duration-300 group-hover:scale-110 ${
            active
              ? "text-accent-gold dark:text-white"
              : "text-accent-gold dark:text-white group-hover:text-[#FFD700] dark:group-hover:text-white"
          }`}
        />

        {!collapsed && (
          <span
            className={`relative z-10 flex-1 truncate transition-colors duration-300 ${
              active
                ? "text-accent-gold dark:text-white"
                : "text-accent-gold dark:text-white group-hover:text-[#FFD700] dark:group-hover:text-white"
            }`}
          >
            {title}
          </span>
        )}

        {!collapsed && active && (
          <ChevronRight
            size={14}
            className="relative z-10 shrink-0 text-accent-gold dark:text-white"
          />
        )}
      </Link>
    </Tooltip>
  );
}