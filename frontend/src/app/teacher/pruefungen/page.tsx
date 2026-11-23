"use client";

import Link from "next/link";
import { Mic, PenLine } from "lucide-react";

import { TeacherPageTitle } from "@/components/teacher/teacher-ui";
import { useTranslation } from "@/lib/i18n/use-translation";

/** Hub for the existing exam review pages (Schreiben / Sprechen of Vorbereitung and VIZU-Multilevel). */
export default function TeacherExamsPage() {
  const { t } = useTranslation();
  const cards = [
    { href: "/teacher/schreiben", label: t("tpanel.examWriting"), icon: PenLine, testId: "exam-writing" },
    { href: "/teacher/sprechen", label: t("tpanel.examSpeaking"), icon: Mic, testId: "exam-speaking" },
  ];
  return (
    <div data-testid="teacher-pruefungen">
      <TeacherPageTitle title={t("tpanel.examsTitle")} subtitle={t("tpanel.examsSubtitle")} />
      <div className="grid gap-4 sm:grid-cols-2">
        {cards.map(({ href, label, icon: Icon, testId }) => (
          <Link key={href} href={href} data-testid={testId}
                className="flex items-center gap-4 rounded-2xl bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border transition hover:-translate-y-0.5 hover:bg-surface-hover">
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-blue/10 text-accent-blue"><Icon size={22} /></span>
            <span className="text-lg font-semibold text-text-primary">{label}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
