"use client";

import { useParams, useRouter } from "next/navigation";
import { FileText } from "lucide-react";

import Button from "@/components/ui/button";
import { useTranslation } from "@/lib/i18n/use-translation";
import VizuMockStepShell from "@/features/vizu-mock/components/step-shell";
import { getSkillMeta } from "@/features/vizu-mock/constants/skills";

/** Lesen step — timer, progress and a "content coming later" placeholder
 * (per spec: no real reading passage/questions exist yet). "Weiter"
 * simply advances to the next step; nothing is submitted or graded. */
export default function VizuMockLesenPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { attemptId } = useParams<{ attemptId: string }>();
  const skill = getSkillMeta("lesen")!;

  return (
    <VizuMockStepShell
      skill={skill}
      footer={
        <Button onClick={() => router.push(`/vizu-mock/${attemptId}/hoeren`)}>{t("vizuMock.next")}</Button>
      }
    >
      <div className="flex flex-col items-center gap-3 rounded-2xl bg-surface-hover/60 px-6 py-14 text-center ring-1 ring-surface-border">
        <FileText size={32} className="text-text-muted" />
        <p className="text-sm text-text-secondary">{t("vizuMock.readingInstruction")}</p>
        <p className="text-xs text-text-muted">{t("vizuMock.placeholderNote")}</p>
      </div>
    </VizuMockStepShell>
  );
}
