"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Award, GraduationCap, Layers, Library, Tag } from "lucide-react";

import ProgressBar from "@/components/ui/progress-bar";
import { useLmsLevels } from "@/features/lms/hooks/use-lms";
import { cardEntrance, staggerContainer } from "@/lib/motion";
import { useTranslation } from "@/lib/i18n/use-translation";

// The five main entries of the student panel. One card each — the A1–C1 levels are no longer five separate buttons here:
// "A1–C1 Kurse" opens the course overview (/kurse) where every level has its own card and status. Mein Lehrer/in and Lug'at are quick
// buttons in the welcome header (dashboard-welcome.tsx): one row of five here keeps the Battle banner above the fold.
const CARDS = [
  { id: "courses", href: "/kurse", icon: Layers, title: "hub.coursesTitle", desc: "hub.coursesDesc", gradient: "from-accent-blue to-brand-600" },
  { id: "media", href: "/medien", icon: Library, title: "hub.mediaTitle", desc: "hub.mediaDesc", gradient: "from-fuchsia-600 to-violet-800" },
  { id: "prep", href: "/vorbereitung", icon: GraduationCap, title: "hub.prepTitle", desc: "hub.prepDesc", gradient: "from-purple-600 to-accent-purple" },
  { id: "certificates", href: "/certificates", icon: Award, title: "hub.certTitle", desc: "hub.certDesc", gradient: "from-amber-500 to-orange-500" },
  { id: "purchase", href: "/angebote", icon: Tag, title: "hub.buyTitle", desc: "hub.buyDesc", gradient: "from-emerald-600 to-teal-500" },
] as const;

export default function DashboardHub() {
  const { t } = useTranslation();
  const { data } = useLmsLevels();
  const done = data?.levels.reduce((n, l) => n + l.lessons_completed, 0) ?? 0;
  const total = data?.levels.reduce((n, l) => n + l.lessons_published, 0) ?? 0;
  const percent = total ? Math.round((100 * done) / total) : 0;

  return (
    <section aria-label={t("hub.mainNav")} data-testid="dashboard-hub">
      <motion.div variants={staggerContainer} initial="hidden" animate="show" className="grid auto-rows-fr grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-3 xl:grid-cols-5">
        {CARDS.map(({ id, href, icon: Icon, title, desc, gradient }, index) => (
          <motion.div key={id} variants={cardEntrance} whileHover={{ y: -4, scale: 1.015 }} whileTap={{ scale: 0.985 }} className={`h-full ${index === CARDS.length - 1 ? "col-span-2 xl:col-span-1" : ""}`}>
            <Link href={href} prefetch={false} data-testid="hub-card" data-card={id}
                  className={`group flex h-full min-h-[190px] min-w-0 flex-col overflow-hidden rounded-card bg-gradient-to-br p-4 text-white shadow-[var(--shadow-card)] transition-shadow duration-200 hover:shadow-[var(--shadow-card-hover)] ${gradient}`}>
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/20 shadow-[var(--shadow-3d-soft)] transition-transform duration-200 group-hover:scale-110">
                <Icon size={19} aria-hidden="true" />
              </div>
              <h3 className="mt-3 break-words text-sm font-bold leading-snug text-white sm:text-base">{t(title)}</h3>
              <p className="mt-1 text-xs leading-relaxed text-white/85 sm:text-[13px]">{t(desc)}</p>
              {id === "courses" && total > 0 && (
                <div className="mt-3" data-testid="hub-courses-progress">
                  <ProgressBar value={percent} trackClassName="h-1.5 bg-white/25" indicatorClassName="bg-white" />
                  <p className="mt-1 text-[11px] text-white/85">{t("hub.coursesProgress", { done, total })}</p>
                </div>
              )}
              <span className="mt-auto inline-flex min-h-10 w-fit items-center gap-2 pt-3 text-sm font-bold text-white">
                <span>{t("hub.open")}</span>
                <ArrowRight size={15} aria-hidden="true" className="shrink-0 transition-transform duration-200 group-hover:translate-x-1" />
              </span>
            </Link>
          </motion.div>
        ))}
      </motion.div>
    </section>
  );
}
