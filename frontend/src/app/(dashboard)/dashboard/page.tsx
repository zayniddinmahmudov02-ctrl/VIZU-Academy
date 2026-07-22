import AiTools from "@/components/dashboard/home/ai-tools";
import ContinueLearning from "@/components/dashboard/home/continue-learning";
import DashboardHero from "@/components/dashboard/home/dashboard-hero";
import StatsRow from "@/components/dashboard/home/stats-row";

export default function DashboardPage() {
  return (
    <div className="relative">
      {/* Subtle page-scoped background glow (dashboard only) */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -inset-x-4 -top-8 -z-10 h-[420px] bg-[radial-gradient(ellipse_at_top,_var(--accent-gold)_0%,transparent_65%)] opacity-[0.08]"
      />

      <div className="space-y-8 lg:space-y-10">
        {/* Welcome */}
        <DashboardHero />

        {/* Statistics */}
        <StatsRow />

        {/* Continue Learning */}
        <ContinueLearning />

        {/* Quick Actions */}
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
    </div>
  );
}
