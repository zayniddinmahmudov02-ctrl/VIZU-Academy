"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowLeft,
  Award,
  Check,
  ChevronRight,
  Clock3,
  FileText,
  GraduationCap,
  Lock,
  Play,
  ShieldCheck,
} from "lucide-react";

import Button from "@/components/ui/button";
import PageHeader from "@/components/dashboard/page-header";
import { fadeInUp } from "@/lib/motion";
import { useTranslation } from "@/lib/i18n/use-translation";
import {
  getPublicLevels,
  getPublicModelTests,
  getPublicProviders,
} from "@/features/vorbereitung/services/vorbereitung-service";
import type { PublicLevel, PublicProvider } from "@/features/vorbereitung/types/vorbereitung.types";

type Step = 1 | 2 | 3;

// CEFR levels don't sort alphabetically the way we want (B2 > B10 as
// strings would be wrong once C2 etc. exist) — this just orders the
// handful of standard codes; anything unrecognized falls to the end,
// alphabetically among itself, rather than being dropped.
const CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"];
function levelSortKey(code: string): number {
  const i = CEFR_ORDER.indexOf(code);
  return i === -1 ? CEFR_ORDER.length : i;
}

interface ProviderLevel {
  provider: PublicProvider;
  level: PublicLevel;
}

export default function VorbereitungView() {
  const { t } = useTranslation();
  const [levelCode, setLevelCode] = useState<string | null>(null);
  const [selected, setSelected] = useState<ProviderLevel | null>(null);

  const step: Step = selected ? 3 : levelCode ? 2 : 1;

  const { data: providerLevels, isLoading } = useQuery({
    queryKey: ["vorbereitung-provider-levels"],
    queryFn: async (): Promise<ProviderLevel[]> => {
      const providers = await getPublicProviders();
      const levelsPerProvider = await Promise.all(providers.map((p) => getPublicLevels(p.id)));
      return providers.flatMap((provider, i) => levelsPerProvider[i].map((level) => ({ provider, level })));
    },
  });

  const levels = Array.from(new Set((providerLevels ?? []).map((pl) => pl.level.level))).sort(
    (a, b) => levelSortKey(a) - levelSortKey(b),
  );

  function providersForLevel(code: string): ProviderLevel[] {
    return (providerLevels ?? []).filter((pl) => pl.level.level === code);
  }

  const { data: modelTests, isLoading: modelTestsLoading } = useQuery({
    queryKey: ["vorbereitung-model-tests", selected?.level.id],
    queryFn: () => getPublicModelTests(selected!.level.id),
    enabled: !!selected,
  });

  return (
    <div className="space-y-12">
      <PageHeader icon={GraduationCap} titleKey="vorbereitung.title" gradient="from-brand-700 to-accent-blue" />

      {/* Header */}
      <header className="relative overflow-hidden rounded-card bg-gradient-to-br from-brand-900 via-brand-700 to-accent-blue p-6 text-white shadow-[var(--shadow-lg)]">
        <div className="inline-flex items-center gap-2 rounded-full bg-white/15 px-3.5 py-1.5 backdrop-blur">
          <ShieldCheck size={16} className="text-white/80" />
          <span className="text-sm font-semibold">{t("vorbereitung.kicker")}</span>
        </div>
        <h1 className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl">{t("vorbereitung.title")}</h1>
        <p className="mt-1.5 max-w-2xl text-white/80">{t("vorbereitung.heroSubtitleGeneric")}</p>

        {/* Stepper */}
        <div className="mt-4 inline-flex flex-wrap items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 backdrop-blur-sm">
          <StepBadge active={step >= 1} done={step > 1} label={t("vorbereitung.stepNiveau")} n={1} />
          <span className="h-px w-5 bg-white/25" />
          <StepBadge active={step >= 2} done={step > 2} label={t("vorbereitung.stepZertifikat")} n={2} />
          <span className="h-px w-5 bg-white/25" />
          <StepBadge active={step >= 3} done={false} label={t("vorbereitung.stepMockTests")} n={3} />
        </div>
      </header>

      {isLoading && <p className="text-sm text-text-secondary">{t("common.loading")}</p>}

      {!isLoading && levels.length === 0 && (
        <p className="rounded-2xl bg-surface-card p-6 text-center text-sm text-text-secondary shadow-[var(--shadow-sm)] ring-1 ring-surface-border">
          Für die Vorbereitung sind noch keine Zertifikate verfügbar.
        </p>
      )}

      <AnimatePresence mode="wait">
        {step === 1 && levels.length > 0 && (
          <motion.section key="step-1" variants={fadeInUp} initial="hidden" animate="show" exit="hidden">
            <h2 className="text-lg font-bold text-text-primary">{t("vorbereitung.step1Heading")}</h2>
            <div className="mb-6 mt-4 h-px w-full bg-surface-border" />
            <div className="flex flex-wrap justify-center gap-5">
              {levels.map((code) => (
                <div
                  key={code}
                  className="group flex h-full w-full flex-col justify-between rounded-2xl bg-surface-card p-6 shadow-[var(--shadow-sm)] ring-1 ring-surface-border transition-all duration-300 hover:-translate-y-1.5 hover:shadow-[var(--shadow-lg)] hover:ring-accent-blue/30 sm:w-[calc((100%-1.25rem)/2)] lg:w-[calc((100%-2.5rem)/3)]"
                >
                  <div>
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-accent-blue to-accent-purple text-lg font-bold text-white shadow-md">
                      {code}
                    </div>
                    <p className="mt-4 font-semibold text-text-primary">{code}</p>
                    <p className="mt-1 text-sm text-text-secondary">
                      {t("vorbereitung.certCount", { count: providersForLevel(code).length })}
                    </p>
                  </div>

                  <Button onClick={() => setLevelCode(code)} size="sm" fullWidth className="mt-5">
                    {t("common.auswaehlen")}
                  </Button>
                </div>
              ))}
            </div>
          </motion.section>
        )}

        {step === 2 && levelCode && (
          <motion.section key="step-2" variants={fadeInUp} initial="hidden" animate="show" exit="hidden">
            <BackButton onClick={() => setLevelCode(null)} label={t("vorbereitung.changeNiveau")} />
            <h2 className="mb-4 mt-3 text-lg font-bold text-text-primary">
              {t("vorbereitung.step2Heading")} <span className="text-accent-blue">{levelCode}</span>
            </h2>
            <div className="grid gap-4 sm:grid-cols-2">
              {providersForLevel(levelCode).map((pl) => (
                <button
                  key={pl.provider.id}
                  type="button"
                  onClick={() => setSelected(pl)}
                  className="group flex items-center justify-between rounded-2xl bg-surface-card p-5 text-left shadow-[var(--shadow-sm)] ring-1 ring-surface-border transition-all duration-200 hover:-translate-y-1 hover:shadow-[var(--shadow-lg)]"
                >
                  <div className="flex items-center gap-4">
                    <div
                      className="flex h-12 w-12 items-center justify-center rounded-xl text-white shadow"
                      style={{ backgroundColor: pl.provider.color ?? "#2563eb" }}
                    >
                      <Award size={22} />
                    </div>
                    <div>
                      <p className="font-semibold text-text-primary">
                        {pl.provider.name} {levelCode}
                      </p>
                      <p className="text-sm text-text-secondary">{pl.provider.description}</p>
                    </div>
                  </div>
                  <ChevronRight
                    size={20}
                    className="text-text-muted transition-transform group-hover:translate-x-1 group-hover:text-accent-blue"
                  />
                </button>
              ))}
            </div>
          </motion.section>
        )}

        {step === 3 && selected && (
          <motion.section key="step-3" variants={fadeInUp} initial="hidden" animate="show" exit="hidden">
            <BackButton onClick={() => setSelected(null)} label={t("vorbereitung.changeZertifikat")} />
            <div className="mb-4 mt-3 flex items-center gap-3">
              <div
                className="flex h-11 w-11 items-center justify-center rounded-xl text-white shadow"
                style={{ backgroundColor: selected.provider.color ?? "#2563eb" }}
              >
                <Award size={20} />
              </div>
              <div>
                <h2 className="text-lg font-bold text-text-primary">
                  {selected.provider.name} {selected.level.level}
                </h2>
                <p className="text-sm text-text-secondary">
                  {t("vorbereitung.mockTestsCount", { count: modelTests?.length ?? 0 })}
                </p>
              </div>
            </div>

            {modelTestsLoading && <p className="text-sm text-text-secondary">{t("common.loading")}</p>}

            {!modelTestsLoading && (modelTests?.length ?? 0) === 0 && (
              <p className="rounded-2xl bg-surface-card p-6 text-center text-sm text-text-secondary shadow-[var(--shadow-sm)] ring-1 ring-surface-border">
                Für {selected.provider.name} {selected.level.level} sind noch keine Modelltests verfügbar.
              </p>
            )}

            <div className="space-y-3">
              {modelTests?.map((mt, i) => (
                <div
                  key={mt.id}
                  className={`flex flex-wrap items-center justify-between gap-4 rounded-2xl bg-surface-card p-5 shadow-[var(--shadow-sm)] ring-1 ring-surface-border ${
                    mt.is_locked ? "opacity-90" : ""
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <div
                      className={`flex h-11 w-11 items-center justify-center rounded-xl ${
                        mt.is_locked ? "bg-warning/10 text-warning" : "bg-accent-blue/10 text-accent-blue"
                      }`}
                    >
                      {mt.is_locked ? <Lock size={20} /> : <FileText size={20} />}
                    </div>
                    <div>
                      <p className="flex items-center gap-1.5 font-semibold text-text-primary">
                        {mt.is_locked && <Lock size={13} className="text-warning" />}
                        {mt.title || t("vorbereitung.mockTestLabel", { count: i + 1 })}
                      </p>
                      <p className="flex items-center gap-1.5 text-sm text-text-secondary">
                        {mt.is_locked ? (
                          t("vorbereitung.premiumRequired")
                        ) : (
                          <>
                            <Clock3 size={14} /> {t("vorbereitung.skillsRow")}
                          </>
                        )}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    {!mt.is_locked && (
                      <span className="hidden items-center gap-1 rounded-lg bg-surface-hover px-2.5 py-1 text-xs font-medium text-text-muted sm:inline-flex">
                        {t("vorbereitung.notStarted")}
                      </span>
                    )}
                    {mt.is_locked ? (
                      <Link href="/vizu-pay">
                        <Button size="sm" variant="secondary">
                          <Lock size={15} />
                          {t("vorbereitung.unlockPremium")}
                        </Button>
                      </Link>
                    ) : (
                      <Link href={`/vorbereitung/modelltest/${mt.id}`}>
                        <Button size="sm">
                          <Play size={16} />
                          {t("common.starten")}
                        </Button>
                      </Link>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </motion.section>
        )}
      </AnimatePresence>
    </div>
  );
}

function StepBadge({ active, done, label, n }: { active: boolean; done: boolean; label: string; n: number }) {
  return (
    <div className="flex items-center gap-1.5">
      <span
        className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
          active ? "bg-white text-brand-800" : "bg-white/20 text-white/70"
        }`}
      >
        {done ? <Check size={12} /> : n}
      </span>
      <span className={`text-sm ${active ? "font-semibold" : "text-white/70"}`}>{label}</span>
    </div>
  );
}

function BackButton({ onClick, label }: { onClick: () => void; label: string }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary transition-colors hover:text-accent-blue"
    >
      <ArrowLeft size={16} />
      {label}
    </button>
  );
}
