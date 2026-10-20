import AiTools from "@/components/dashboard/home/ai-tools";
import AchievementsCard from "@/components/dashboard/home/achievements-card";
import AdvertisementBanner from "@/components/dashboard/home/advertisement-banner";
import CertificatesCard from "@/components/dashboard/home/certificates-card";
import DashboardCourses from "@/components/dashboard/home/dashboard-courses";
import DashboardMotion from "@/components/dashboard/home/dashboard-motion";
import LearningStreakCard from "@/components/dashboard/home/learning-streak-card";

// This page's content is 100% client-fetched (React Query) — forcing
// dynamic rendering just drops the default 1-year static-shell cache
// (`s-maxage=31536000`) that Next.js otherwise applies, so a deploy is
// never at risk of a stale cached shell outliving its own JS bundle.
export const dynamic = "force-dynamic";

export default function DashboardPage() {
  return (
    <div className="relative">
      {/* Subtle page-scoped background glow (dashboard only) */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -inset-x-4 -top-8 -z-10 h-[420px] bg-[radial-gradient(ellipse_at_top,_var(--accent-gold)_0%,transparent_65%)] opacity-[0.08]"
      />

      <DashboardMotion>
        <div className="space-y-8 lg:space-y-10">
          {/* 1. Werbung-Banner (admin-managed) */}
          <AdvertisementBanner />

          {/* 2. Kurse A1–C1 */}
          <DashboardCourses />

          {/* 3. Lernserie · Zertifikate · Erfolge */}
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3" data-testid="dashboard-gadgets">
            <LearningStreakCard />
            <CertificatesCard />
            <div className="md:col-span-2 xl:col-span-1">
              <AchievementsCard />
            </div>
          </div>

          {/* 4. Schnellzugriff: Zertifikatsprüfungen, VIZU-Multilevel, Wörterbuch */}
          <AiTools />

          {/* Footer */}
          <footer className="border-t border-surface-border pt-8 pb-4 text-center">
            <p className="text-sm font-semibold text-text-secondary">
              Author des Projekts
            </p>

            <p className="mt-1 text-lg font-bold text-accent-gold">
              Zayniddinkhuja Makhmudov
            </p>
          </footer>
        </div>
      </DashboardMotion>
    </div>
  );
}
