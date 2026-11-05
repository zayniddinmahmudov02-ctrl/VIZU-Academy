"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle2, FileText, Headphones, Lock, Mic, PenLine } from "lucide-react";

import ComingSoonModal from "@/features/vorbereitung/components/coming-soon-modal";
import { getMultilevelModelTests } from "@/features/vorbereitung/services/vorbereitung-service";
import type { PublicModelTest } from "@/features/vorbereitung/types/vorbereitung.types";
import { useTranslation } from "@/lib/i18n/use-translation";

// Modelltest 1–10 of the Multilevel provider (level "Multilevel B1–C1"). Only PUBLISHED tests come back from the
// public API (backend: public_service.get_public_model_tests) and become links; every other number stays a locked
// card that opens the ComingSoonModal. Drafts are never visible here.
const MULTILEVEL_MODELLTEST_COUNT = 10;
const MULTILEVEL_SKILLS = [
  { icon: FileText, labelKey: "lessons.sectionReading" },
  { icon: Headphones, labelKey: "lessons.sectionListening" },
  { icon: PenLine, labelKey: "lessons.sectionWriting" },
  { icon: Mic, labelKey: "lessons.sectionSpeaking" },
] as const;

function testNumber(test: PublicModelTest): number | null {
  const match = /(\d+)\s*$/.exec(test.title);
  return match ? Number(match[1]) : null;
}

export default function MultilevelPage() {
  const { t } = useTranslation();
  const [comingSoonOpen, setComingSoonOpen] = useState(false);
  const { data: tests = [] } = useQuery({ queryKey: ["public-multilevel-tests"], queryFn: getMultilevelModelTests });

  const byNumber = new Map<number, PublicModelTest>();
  for (const test of tests) {
    const n = testNumber(test);
    if (n !== null && !byNumber.has(n)) byNumber.set(n, test);
  }

  const cardClass =
    "group flex flex-col gap-4 rounded-2xl bg-surface-hover/60 p-5 text-left shadow-[var(--shadow-sm)] ring-1 ring-surface-border transition-all duration-200 hover:-translate-y-1 hover:bg-surface-hover hover:shadow-[var(--shadow-lg)]";

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
        {Array.from({ length: MULTILEVEL_MODELLTEST_COUNT }, (_, i) => i + 1).map((number) => {
          const test = byNumber.get(number);
          const head = (
            <div className="flex items-center gap-3">
              <div
                className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${
                  test ? "bg-success/10 text-success" : "bg-warning/10 text-warning"
                }`}
              >
                {test ? <CheckCircle2 size={18} /> : <Lock size={18} />}
              </div>
              <p className="flex items-center gap-1.5 font-semibold text-text-primary">
                {!test && <Lock size={12} className="text-warning" />}
                {t("vorbereitung.modelltestNumber", { number })}
              </p>
            </div>
          );
          const skills = (
            <div className="grid grid-cols-2 gap-2">
              {MULTILEVEL_SKILLS.map((skill) => (
                <span
                  key={skill.labelKey}
                  className="flex items-center gap-1.5 rounded-lg bg-surface-card px-2.5 py-2 text-xs font-medium text-text-muted ring-1 ring-surface-border"
                >
                  {!test && <Lock size={11} className="shrink-0" />}
                  <skill.icon size={13} className="shrink-0" />
                  <span className="truncate">{t(skill.labelKey)}</span>
                </span>
              ))}
            </div>
          );
          return test ? (
            <Link
              key={number}
              href={`/vorbereitung/modelltest/${test.id}`}
              className={cardClass}
              data-testid={`multilevel-test-${number}`}
            >
              {head}
              {skills}
            </Link>
          ) : (
            <button
              key={number}
              type="button"
              onClick={() => setComingSoonOpen(true)}
              className={cardClass}
              data-testid={`multilevel-test-${number}-locked`}
            >
              {head}
              {skills}
            </button>
          );
        })}
      </div>

      <ComingSoonModal open={comingSoonOpen} onClose={() => setComingSoonOpen(false)} />
    </div>
  );
}
