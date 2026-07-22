import Link from "next/link";
import { BookOpen } from "lucide-react";

export default function NextLessonCard() {
  // Placeholder until per-user lesson progress is tracked — mirrors the
  // "Modul 1" placeholder used by the featured continue-learning card.
  const next = { level: "A1", module: "Modul 2", title: "Vorstellung" };

  return (
    <section className="flex h-full flex-col justify-between gap-5 rounded-card bg-surface-card p-5 shadow-[var(--shadow-card)] ring-1 ring-surface-border sm:p-6">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-b from-accent-blue to-brand-600 text-white shadow-[var(--shadow-3d-soft)]">
          <BookOpen size={20} />
        </div>
        <h2 className="text-base font-bold text-text-primary">Nächste Lektion</h2>
      </div>

      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
          {next.level} · {next.module}
        </p>
        <p className="mt-1 text-lg font-bold text-text-primary">{next.title}</p>
      </div>

      <Link
        href="/lessons"
        className="inline-flex w-fit items-center gap-1.5 rounded-button bg-accent-blue/10 px-4 py-2.5 text-sm font-semibold text-accent-blue shadow-[var(--shadow-3d-soft)] transition-all duration-200 hover:-translate-y-px hover:bg-accent-blue/15"
      >
        Öffnen
      </Link>
    </section>
  );
}
