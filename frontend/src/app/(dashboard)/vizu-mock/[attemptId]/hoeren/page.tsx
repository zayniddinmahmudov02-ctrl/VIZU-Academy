"use client";

import { useParams, useRouter } from "next/navigation";
import { Headphones, Play } from "lucide-react";

import Button from "@/components/ui/button";
import { useTranslation } from "@/lib/i18n/use-translation";
import VizuMockStepShell from "@/features/vizu-mock/components/step-shell";
import { getSkillMeta } from "@/features/vizu-mock/constants/skills";

/** Hören step — timer, progress, an audio-player placeholder (no real
 * audio exists yet). "Weiter" simply advances; nothing is submitted. */
export default function VizuMockHoerenPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { attemptId } = useParams<{ attemptId: string }>();
  const skill = getSkillMeta("hoeren")!;

  return (
    <VizuMockStepShell
      skill={skill}
      footer={
        <Button onClick={() => router.push(`/vizu-mock/${attemptId}/schreiben`)}>{t("vizuMock.next")}</Button>
      }
    >
      <div className="flex flex-col items-center gap-3 rounded-2xl bg-surface-hover/60 px-6 py-14 text-center ring-1 ring-surface-border">
        <Headphones size={32} className="text-text-muted" />
        <button
          type="button"
          disabled
          aria-label="Play"
          className="flex h-14 w-14 items-center justify-center rounded-full bg-surface-border text-text-muted"
        >
          <Play size={20} />
        </button>
        <p className="text-sm text-text-secondary">{t("vizuMock.listeningInstruction")}</p>
        <p className="text-xs text-text-muted">{t("vizuMock.placeholderNote")}</p>
      </div>
    </VizuMockStepShell>
  );
}
