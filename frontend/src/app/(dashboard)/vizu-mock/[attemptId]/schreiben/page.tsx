"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { PenLine } from "lucide-react";

import Button from "@/components/ui/button";
import { useTranslation } from "@/lib/i18n/use-translation";
import VizuMockStepShell from "@/features/vizu-mock/components/step-shell";
import { getSkillMeta } from "@/features/vizu-mock/constants/skills";

function countWords(text: string): number {
  return text.trim().length === 0 ? 0 : text.trim().split(/\s+/).length;
}

/** Schreiben step — timer, progress, a task placeholder and a real
 * (but unsent) writing editor: input capture is purely for UX realism.
 * Nothing is persisted, since there's no real task/grading to attach it
 * to yet (per spec). "Einreichen" simply advances to Sprechen. */
export default function VizuMockSchreibenPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { attemptId } = useParams<{ attemptId: string }>();
  const skill = getSkillMeta("schreiben")!;
  const [text, setText] = useState("");

  return (
    <VizuMockStepShell
      skill={skill}
      footer={
        <Button onClick={() => router.push(`/vizu-mock/${attemptId}/sprechen`)}>{t("vizuMock.submit")}</Button>
      }
    >
      <div className="space-y-4">
        <div className="flex items-start gap-3 rounded-2xl bg-surface-hover/60 p-4 ring-1 ring-surface-border">
          <PenLine size={18} className="mt-0.5 shrink-0 text-text-muted" />
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
              {t("vizuMock.writingPrompt")}
            </p>
            <p className="mt-1 text-sm text-text-secondary">{t("vizuMock.writingPromptPlaceholder")}</p>
          </div>
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-semibold text-text-primary">
            {t("vizuMock.writingAnswerLabel")}
          </label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={8}
            placeholder={t("vizuMock.writingAnswerPlaceholder")}
            className="w-full rounded-xl bg-surface-card p-4 text-[15px] text-text-primary ring-1 ring-surface-border outline-none placeholder:text-text-muted focus:ring-accent-blue sm:text-sm"
          />
          <p className="mt-1.5 text-xs text-text-muted">{countWords(text)} Wörter</p>
        </div>
      </div>
    </VizuMockStepShell>
  );
}
