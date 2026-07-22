"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowLeft,
  Award,
  Check,
  ChevronRight,
  Clock3,
  FileText,
  GraduationCap,
  Play,
  ShieldCheck,
} from "lucide-react";

import Button from "@/components/ui/button";
import PageHeader from "@/components/dashboard/page-header";
import { fadeInUp } from "@/lib/motion";
import { germanLevels, type LevelCode } from "@/constants/levels";
import { MOCKS_PER_EXAM, providersForLevel, type ExamProvider } from "@/constants/exams";
import { useTranslation } from "@/lib/i18n/use-translation";

type Step = 1 | 2 | 3;

export default function VorbereitungView() {
  const { t } = useTranslation();
  const [level, setLevel] = useState<LevelCode | null>(null);
  const [provider, setProvider] = useState<ExamProvider | null>(null);

  const step: Step = provider ? 3 : level ? 2 : 1;

  return (
    <div className="space-y-12">
      <PageHeader
        icon={GraduationCap}
        titleKey="vorbereitung.title"
        gradient="from-brand-700 to-accent-blue"
      />

      {/* Header */}
      <header className="relative overflow-hidden rounded-card bg-gradient-to-br from-brand-900 via-brand-700 to-accent-blue p-6 text-white shadow-[var(--shadow-lg)]">
        <div className="inline-flex items-center gap-2 rounded-full bg-white/15 px-3.5 py-1.5 backdrop-blur">
          <ShieldCheck size={16} className="text-white/80" />
          <span className="text-sm font-semibold">{t("vorbereitung.kicker")}</span>
        </div>
        <h1 className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl">{t("vorbereitung.title")}</h1>
        <p className="mt-1.5 max-w-2xl text-white/80">
          {t("vorbereitung.heroSubtitle", { count: MOCKS_PER_EXAM })}
        </p>

        {/* Stepper */}
        <div className="mt-4 inline-flex flex-wrap items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 backdrop-blur-sm">
          <StepBadge active={step >= 1} done={step > 1} label={t("vorbereitung.stepNiveau")} n={1} />
          <span className="h-px w-5 bg-white/25" />
          <StepBadge active={step >= 2} done={step > 2} label={t("vorbereitung.stepZertifikat")} n={2} />
          <span className="h-px w-5 bg-white/25" />
          <StepBadge active={step >= 3} done={false} label={t("vorbereitung.stepMockTests")} n={3} />
        </div>
      </header>

      <AnimatePresence mode="wait">
        {step === 1 && (
          <motion.section key="step-1" variants={fadeInUp} initial="hidden" animate="show" exit="hidden">
            <h2 className="text-lg font-bold text-text-primary">{t("vorbereitung.step1Heading")}</h2>
            <div className="mb-6 mt-4 h-px w-full bg-surface-border" />
            <div className="flex flex-wrap justify-center gap-5">
              {germanLevels.map((l) => (
                <div
                  key={l.code}
                  className="group flex h-full w-full flex-col justify-between rounded-2xl bg-surface-card p-6 shadow-[var(--shadow-sm)] ring-1 ring-surface-border transition-all duration-300 hover:-translate-y-1.5 hover:shadow-[var(--shadow-lg)] hover:ring-accent-blue/30 sm:w-[calc((100%-1.25rem)/2)] lg:w-[calc((100%-2.5rem)/3)]"
                >
                  <div>
                    <div
                      className={`flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${l.gradient} text-lg font-bold text-white shadow-md`}
                    >
                      {l.code}
                    </div>
                    <p className="mt-4 font-semibold text-text-primary">{t(l.labelKey)}</p>
                    <p className="mt-1 text-sm text-text-secondary">
                      {t("vorbereitung.certCount", { count: providersForLevel(l.code).length })}
                    </p>
                  </div>

                  <Button onClick={() => setLevel(l.code)} size="sm" fullWidth className="mt-5">
                    {t("common.auswaehlen")}
                  </Button>
                </div>
              ))}
            </div>
          </motion.section>
        )}

        {step === 2 && level && (
          <motion.section key="step-2" variants={fadeInUp} initial="hidden" animate="show" exit="hidden">
            <BackButton onClick={() => setLevel(null)} label={t("vorbereitung.changeNiveau")} />
            <h2 className="mb-4 mt-3 text-lg font-bold text-text-primary">
              {t("vorbereitung.step2Heading")} <span className="text-accent-blue">{level}</span>
            </h2>
            <div className="grid gap-4 sm:grid-cols-2">
              {providersForLevel(level).map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => setProvider(p)}
                  className="group flex items-center justify-between rounded-2xl bg-surface-card p-5 text-left shadow-[var(--shadow-sm)] ring-1 ring-surface-border transition-all duration-200 hover:-translate-y-1 hover:shadow-[var(--shadow-lg)]"
                >
                  <div className="flex items-center gap-4">
                    <div
                      className={`flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${p.accent} text-white shadow`}
                    >
                      <Award size={22} />
                    </div>
                    <div>
                      <p className="font-semibold text-text-primary">
                        {p.name} {level}
                      </p>
                      <p className="text-sm text-text-secondary">{p.description}</p>
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

        {step === 3 && provider && level && (
          <motion.section key="step-3" variants={fadeInUp} initial="hidden" animate="show" exit="hidden">
            <BackButton onClick={() => setProvider(null)} label={t("vorbereitung.changeZertifikat")} />
            <div className="mb-4 mt-3 flex items-center gap-3">
              <div
                className={`flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br ${provider.accent} text-white shadow`}
              >
                <Award size={20} />
              </div>
              <div>
                <h2 className="text-lg font-bold text-text-primary">
                  {provider.name} {level}
                </h2>
                <p className="text-sm text-text-secondary">
                  {t("vorbereitung.mockTestsCount", { count: MOCKS_PER_EXAM })}
                </p>
              </div>
            </div>

            <div className="space-y-3">
              {Array.from({ length: MOCKS_PER_EXAM }).map((_, i) => (
                <div
                  key={i}
                  className="flex flex-wrap items-center justify-between gap-4 rounded-2xl bg-surface-card p-5 shadow-[var(--shadow-sm)] ring-1 ring-surface-border"
                >
                  <div className="flex items-center gap-4">
                    <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-blue/10 text-accent-blue">
                      <FileText size={20} />
                    </div>
                    <div>
                      <p className="font-semibold text-text-primary">
                        {t("vorbereitung.mockTestLabel", { count: i + 1 })}
                      </p>
                      <p className="flex items-center gap-1.5 text-sm text-text-secondary">
                        <Clock3 size={14} /> {t("vorbereitung.skillsRow")}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="hidden items-center gap-1 rounded-lg bg-surface-hover px-2.5 py-1 text-xs font-medium text-text-muted sm:inline-flex">
                      {t("vorbereitung.notStarted")}
                    </span>
                    <Button size="sm">
                      <Play size={16} />
                      {t("common.starten")}
                    </Button>
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

function StepBadge({
  active,
  done,
  label,
  n,
}: {
  active: boolean;
  done: boolean;
  label: string;
  n: number;
}) {
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
