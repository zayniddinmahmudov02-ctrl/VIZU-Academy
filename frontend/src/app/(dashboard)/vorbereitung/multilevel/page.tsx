"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, FileText, Headphones, Lock, Mic, PenLine } from "lucide-react";

import ComingSoonModal from "@/features/vorbereitung/components/coming-soon-modal";
import { useTranslation } from "@/lib/i18n/use-translation";

// Purely static placeholder content — 10 Modelltests, each with the same
// 4 skills, all locked. No API call, no real ModelTest/Kompetenz rows
// exist for this yet; every card opens the same ComingSoonModal instead
// of navigating anywhere. Multilevel is its own Niveau-step card on
// /vorbereitung (see vorbereitung-view.tsx) that links here — this page
// deliberately never shows B1/B2/C1-style Zertifikat cards, only these
// 10 Modelltests directly.
const MULTILEVEL_MODELLTEST_COUNT = 10;
const MULTILEVEL_SKILLS = [
  { icon: FileText, labelKey: "lessons.sectionReading" },
  { icon: Headphones, labelKey: "lessons.sectionListening" },
  { icon: PenLine, labelKey: "lessons.sectionWriting" },
  { icon: Mic, labelKey: "lessons.sectionSpeaking" },
] as const;

export default function MultilevelPage() {
  const { t } = useTranslation();
  const [comingSoonOpen, setComingSoonOpen] = useState(false);

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <Link
        href="/vorbereitung"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary transition-colors hover:text-accent-blue"
      >
        <ArrowLeft size={16} />
        Vorbereitung
      </Link>

      <header>
        <h1 className="text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
          {t("vorbereitung.multilevelSection")}
        </h1>
        <p className="mt-2 text-text-secondary">{t("vorbereitung.multilevelSubtitle")}</p>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: MULTILEVEL_MODELLTEST_COUNT }, (_, i) => i + 1).map((number) => (
          <button
            key={number}
            type="button"
            onClick={() => setComingSoonOpen(true)}
            className="group flex flex-col gap-4 rounded-2xl bg-surface-hover/60 p-5 text-left shadow-[var(--shadow-sm)] ring-1 ring-surface-border transition-all duration-200 hover:-translate-y-1 hover:bg-surface-hover hover:shadow-[var(--shadow-lg)]"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-warning/10 text-warning">
                <Lock size={18} />
              </div>
              <p className="flex items-center gap-1.5 font-semibold text-text-primary">
                <Lock size={12} className="text-warning" />
                {t("vorbereitung.modelltestNumber", { number })}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-2">
              {MULTILEVEL_SKILLS.map((skill) => (
                <span
                  key={skill.labelKey}
                  className="flex items-center gap-1.5 rounded-lg bg-surface-card px-2.5 py-2 text-xs font-medium text-text-muted ring-1 ring-surface-border"
                >
                  <Lock size={11} className="shrink-0" />
                  <skill.icon size={13} className="shrink-0" />
                  <span className="truncate">{t(skill.labelKey)}</span>
                </span>
              ))}
            </div>
          </button>
        ))}
      </div>

      <ComingSoonModal open={comingSoonOpen} onClose={() => setComingSoonOpen(false)} />
    </div>
  );
}
